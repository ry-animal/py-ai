from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.agent_memory import AgentMemory, InMemoryAgentMemory
from app.pydantic_agent_service import PydanticAgentService, RouteDecision, SourceInfo
from app.rag_service import RAGService
from app.web_search import TavilySearch


class HybridAgentState(TypedDict, total=False):
    """State for hybrid agent combining LangGraph workflow with pydantic-ai tools."""

    question: str
    messages: list[BaseMessage]
    log: list[str]
    pydantic_decision: RouteDecision | None
    sources: list[SourceInfo] | None
    structured_output: dict[str, Any] | None
    final_answer: str | None


class HybridResponse(BaseModel):
    """Response combining LangGraph workflow control with pydantic-ai structured output."""

    answer: str
    workflow_log: list[str]
    pydantic_sources: list[SourceInfo]
    route_decision: RouteDecision
    session_id: str | None = None


class HybridAgentService:
    """
    Hybrid agent that combines LangGraph workflow orchestration
    with pydantic-ai structured tools and output validation.

    Benefits:
    - LangGraph: Complex workflow control, state management, conditional routing
    - Pydantic-AI: Type-safe tools, structured output, validation
    """

    def __init__(
        self,
        rag: RAGService | None = None,
        web: TavilySearch | None = None,
        memory: AgentMemory | None = None,
        memory_turns: int = 3,
    ) -> None:
        self.rag = rag or RAGService()
        if web is not None:
            self.web = web
        else:
            try:
                self.web = TavilySearch()
            except Exception:  # noqa: BLE001
                self.web = None

        self.memory = memory or InMemoryAgentMemory(max_turns=memory_turns)

        # Create pydantic-ai service for structured tools
        self.pydantic_service = PydanticAgentService(rag=self.rag, web=self.web, memory=self.memory)

        # Build LangGraph workflow
        self.graph = self._build_hybrid_graph()

    def _build_hybrid_graph(self):
        """Build hybrid workflow using LangGraph orchestration with pydantic-ai tools."""
        workflow = StateGraph(HybridAgentState)

        async def planning_node(state: HybridAgentState) -> HybridAgentState:
            """LangGraph node that uses pydantic-ai for intelligent routing."""
            question = state["question"]
            log = state.get("log", [])

            # Use pydantic-ai agent for routing decision (but not full execution)
            try:
                # Get just the routing decision using pydantic-ai tools
                route_tool = None
                for tool_def in self.pydantic_service.agent.tool_definitions:
                    if tool_def["name"] == "route_query":
                        route_tool = tool_def["function"]
                        break

                if route_tool:
                    # Create minimal context for routing
                    from app.pydantic_agent_service import AgentDependencies

                    deps = AgentDependencies(
                        rag_service=self.rag,
                        ai_service=self.pydantic_service.ai,
                        web_search=self.web,
                        memory=self.memory,
                    )

                    # Simulate RunContext for the tool
                    class MockContext:
                        def __init__(self, deps):
                            self.deps = deps

                    mock_ctx = MockContext(deps)
                    decision = await route_tool(mock_ctx, question)
                else:
                    # Fallback routing logic
                    decision = RouteDecision(
                        route="rag",
                        reason="Fallback routing - no pydantic tool available",
                        confidence=0.5,
                    )
            except Exception:
                decision = RouteDecision(
                    route="rag",
                    reason="Error in pydantic routing, defaulting to RAG",
                    confidence=0.3,
                )

            log.append(
                f"[hybrid-planning] Route decision: {decision.route} "
                f"({decision.confidence:.2f}) - {decision.reason}"
            )

            return {
                "pydantic_decision": decision,
                "log": log,
            }

        async def rag_execution_node(state: HybridAgentState) -> HybridAgentState:
            """LangGraph node that executes RAG using pydantic-ai structured tools."""
            question = state["question"]
            log = state.get("log", [])

            try:
                # Use pydantic-ai for structured RAG execution
                response = await self.pydantic_service.ask(question, stream=False)

                return {
                    "sources": response.sources,
                    "final_answer": response.answer,
                    "structured_output": {
                        "route_decision": response.route_decision.model_dump(),
                        "sources": [s.model_dump() for s in response.sources],
                    },
                    "log": log
                    + [f"[hybrid-rag] Generated answer with {len(response.sources)} sources"],
                }
            except Exception as e:
                return {
                    "final_answer": f"Error in RAG execution: {str(e)}",
                    "log": log + [f"[hybrid-rag] Error: {str(e)}"],
                }

        async def web_execution_node(state: HybridAgentState) -> HybridAgentState:
            """LangGraph node that executes web search using pydantic-ai structured tools."""
            question = state["question"]
            log = state.get("log", [])

            try:
                # Use pydantic-ai for structured web search execution
                response = await self.pydantic_service.ask(question, stream=False)

                return {
                    "sources": response.sources,
                    "final_answer": response.answer,
                    "structured_output": {
                        "route_decision": response.route_decision.model_dump(),
                        "sources": [s.model_dump() for s in response.sources],
                    },
                    "log": log
                    + [f"[hybrid-web] Generated answer with {len(response.sources)} sources"],
                }
            except Exception as e:
                return {
                    "final_answer": f"Error in web execution: {str(e)}",
                    "log": log + [f"[hybrid-web] Error: {str(e)}"],
                }

        # Add nodes to workflow
        workflow.add_node("planning", planning_node)
        workflow.add_node("rag_execution", rag_execution_node)
        workflow.add_node("web_execution", web_execution_node)

        # Set entry point
        workflow.set_entry_point("planning")

        # Add conditional routing based on pydantic-ai decision
        def route_execution(state: HybridAgentState) -> str:
            decision = state.get("pydantic_decision")
            if decision and decision.route == "web":
                return "web_execution"
            return "rag_execution"

        workflow.add_conditional_edges(
            "planning",
            route_execution,
            {"rag_execution": "rag_execution", "web_execution": "web_execution"},
        )

        # End after execution
        workflow.add_edge("rag_execution", END)
        workflow.add_edge("web_execution", END)

        return workflow.compile()

    def _session_key(self, session_id: str | None) -> str:
        """Generate session key for memory storage."""
        return session_id or "default"

    async def ask(
        self, question: str, session_id: str | None = None, stream: bool = False
    ) -> HybridResponse | AsyncIterator[str]:
        """
        Ask the hybrid agent a question.

        This combines:
        - LangGraph workflow orchestration and state management
        - Pydantic-AI structured tools and output validation
        - Type-safe responses with comprehensive metadata
        """
        session_key = self._session_key(session_id)

        # Load conversation history
        try:
            history = await self.memory.read(session_key)
        except Exception:
            history = []

        # Prepare initial state
        initial_state: HybridAgentState = {
            "question": question,
            "messages": history + [HumanMessage(content=question)],
            "log": ["[hybrid-start] Starting hybrid LangGraph + Pydantic-AI execution"],
        }

        if stream:

            async def stream_response():
                async for event in self.graph.astream(initial_state):
                    for _node_name, node_output in event.items():
                        if "log" in node_output:
                            for log_entry in node_output["log"]:
                                yield f"{log_entry}\n"

                        if "final_answer" in node_output and node_output["final_answer"]:
                            answer = node_output["final_answer"]
                            # Stream the answer in chunks
                            chunk_size = 50
                            for i in range(0, len(answer), chunk_size):
                                yield answer[i : i + chunk_size]

            return stream_response()
        else:
            # Execute workflow
            result = await self.graph.ainvoke(initial_state)

            # Create structured response
            return HybridResponse(
                answer=result.get("final_answer", "No answer generated"),
                workflow_log=result.get("log", []),
                pydantic_sources=result.get("sources", []),
                route_decision=result.get("pydantic_decision")
                or RouteDecision(route="unknown", reason="No decision made", confidence=0.0),
                session_id=session_id,
            )
