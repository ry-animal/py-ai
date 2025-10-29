from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from typing import Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph

from app.agent_memory import AgentMemory, InMemoryAgentMemory
from app.ai_service import AIService
from app.dependencies import get_ai_service
from app.rag_service import RAGService
from app.web_search import TavilySearch


class AgentState(TypedDict, total=False):
    question: str
    messages: list[BaseMessage]
    log: list[str]
    route: Literal["rag", "web"]
    route_reason: str
    contexts: list[str]
    direct_answer: str | None


class AgentService:
    def __init__(
        self,
        rag: RAGService | None = None,
        ai: AIService | None = None,
        web: TavilySearch | None = None,
        memory: AgentMemory | None = None,
        memory_turns: int = 3,
    ) -> None:
        self.rag = rag or RAGService()
        self.ai = ai or get_ai_service()
        if web is not None:
            self.web = web
        else:
            try:
                self.web = TavilySearch()
            except Exception:  # noqa: BLE001 - optional dependency
                self.web = None
        self.max_turns = memory_turns
        self.memory = memory or InMemoryAgentMemory(max_turns=self.max_turns)
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        async def route_node(state: AgentState) -> AgentState:
            question = state["question"]
            history = state.get("messages", [])[:-1]
            decision, reason = self._route_question(question, history)
            log = state.get("log", [])
            entry = f"[route] {decision.upper()} — {reason}"
            return {
                "route": decision,
                "route_reason": reason,
                "log": log + [entry],
            }

        async def rag_node(state: AgentState) -> AgentState:
            question = state["question"]
            contexts = [c for c in self.rag.retrieve(question) if c]
            log = state.get("log", [])
            entry = f"[rag] Retrieved {len(contexts)} context chunk(s)."
            return {
                "contexts": contexts,
                "log": log + [entry],
            }

        async def web_node(state: AgentState) -> AgentState:
            question = state["question"]
            log = state.get("log", [])
            if self.web is None:
                fallback = [c for c in self.rag.retrieve(question) if c]
                entry = "[web] Web search disabled; falling back to RAG contexts."
                return {"contexts": fallback, "log": log + [entry]}
            snippets, direct = await self.web.search_with_answer(question)
            snippets = [s for s in snippets if s]
            entry = f"[web] Retrieved {len(snippets)} snippet(s) from Tavily."
            return {
                "contexts": snippets,
                "direct_answer": direct,
                "log": log + [entry],
            }

        workflow.add_node("route", route_node)
        workflow.add_node("rag", rag_node)
        workflow.add_node("web", web_node)
        workflow.set_entry_point("route")

        def choose_next(state: AgentState) -> str:
            return state.get("route", "rag")

        workflow.add_conditional_edges("route", choose_next, {"rag": "rag", "web": "web"})
        workflow.add_edge("rag", END)
        workflow.add_edge("web", END)

        return workflow.compile()

    def _route_question(
        self, question: str, history: list[BaseMessage]
    ) -> tuple[Literal["rag", "web"], str]:
        lowered = question.lower()
        web_keywords = ["web", "latest", "news", "today", "current", "recent", "update"]
        prefer_web = any(keyword in lowered for keyword in web_keywords) or "http" in lowered
        if self.web is None:
            return "rag", "Web search unavailable; using local knowledge base"
        if prefer_web:
            return "web", "Detected recency/web intent"
        if any(isinstance(msg, AIMessage) and "web" in msg.content.lower() for msg in history[-4:]):
            return "web", "Maintaining prior turn web context"
        return "rag", "Defaulting to RAG for doc-grounded questions"

    def _session_key(self, session_id: str | None) -> str:
        return session_id or "default"

    async def _commit_turn(self, session_key: str, question: str, answer: str) -> None:
        await self.memory.append(
            session_key,
            [HumanMessage(content=question), AIMessage(content=answer)],
        )

    async def answer(
        self, question: str, stream: bool = False, session: str | None = None
    ) -> str | AsyncIterator[str]:
        session_key = self._session_key(session)
        history = await self.memory.read(session_key)
        state: AgentState = {
            "question": question,
            "messages": history + [HumanMessage(content=question)],
            "log": [],
        }
        config = {"configurable": {"thread_id": session_key}}
        if stream:

            async def gen() -> AsyncGenerator[str, None]:
                combined: AgentState = {"log": []}
                last_log_len = 0
                async for event in self.graph.astream(state, config=config):
                    for node_state in event.values():
                        if not isinstance(node_state, dict):
                            continue
                        if "log" in node_state:
                            log = node_state["log"]
                            new_entries = log[last_log_len:]
                            for entry in new_entries:
                                yield f"{entry}\n"
                            last_log_len = len(log)
                            combined["log"] = log
                        for key, value in node_state.items():
                            if key == "log":
                                continue
                            combined[key] = value

                contexts = combined.get("contexts", []) or []
                direct = combined.get("direct_answer")
                answer_text = ""
                if not contexts and direct:
                    yield "[answer] Using Tavily direct answer.\n"
                    yield direct
                    answer_text = direct
                else:
                    if not contexts:
                        contexts = [
                            (
                                "[agent] No supporting documents were retrieved;"
                                " replying conservatively."
                            )
                        ]
                    stream_iter = await self.ai.generate_answer(question, contexts, stream=True)
                    chunks: list[str] = []
                    async for chunk in stream_iter:
                        chunks.append(chunk)
                        yield chunk
                    answer_text = "".join(chunks).strip()
                    if (not answer_text or "I don't know" in answer_text) and direct:
                        fallback = f"\nTavily suggests: {direct}"
                        answer_text = f"{answer_text}{fallback}" if answer_text else direct
                        yield fallback
                await self._commit_turn(session_key, question, answer_text)

            return gen()

        result = await self.graph.ainvoke(state, config=config)
        contexts = result.get("contexts", []) or []
        direct = result.get("direct_answer")
        if not contexts and direct:
            answer = direct
        else:
            if not contexts:
                contexts = [
                    ("[agent] No supporting documents were retrieved;" " replying conservatively.")
                ]
            answer = await self.ai.generate_answer(question, contexts, stream=False)
            if (not answer or "I don't know" in answer) and direct:
                answer = answer + f"\nTavily suggests: {direct}" if answer else direct
        await self._commit_turn(session_key, question, answer)
        return answer
