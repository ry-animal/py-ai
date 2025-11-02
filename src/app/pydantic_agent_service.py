from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from app.agent_memory import AgentMemory, InMemoryAgentMemory
from app.ai_service import AIService
from app.config import get_settings
from app.rag_service import RAGService
from app.web_search import TavilySearch


@dataclass
class AgentDependencies:
    """Dependencies for the pydantic-ai agent with type-safe context injection."""

    rag_service: RAGService
    ai_service: AIService
    web_search: TavilySearch | None
    memory: AgentMemory
    session_id: str | None = None


class RouteDecision(BaseModel):
    """Decision made by the routing logic."""

    route: Literal["rag", "web"]
    reason: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in routing decision")


class SourceInfo(BaseModel):
    """Information about a source document or web result."""

    content: str
    source_type: Literal["document", "web"]
    title: str | None = None
    url: str | None = None
    relevance_score: float | None = None
    document_id: str | None = None


class AgentResponse(BaseModel):
    """Structured response from the pydantic-ai agent."""

    answer: str = Field(description="The agent's response to the user's question")
    sources: list[SourceInfo] = Field(
        default_factory=list, description="Sources used to generate the answer"
    )
    route_decision: RouteDecision = Field(
        default=RouteDecision(route="rag", reason="Default routing", confidence=0.5),
        description="How the agent decided to route the query",
    )
    session_id: str | None = Field(
        default=None, description="Session ID for conversation continuity"
    )
    direct_answer: str | None = Field(
        default=None, description="Direct answer from web search if available"
    )


class PydanticAgentService:
    """Pydantic-AI based agent service that integrates RAG and web search capabilities."""

    def __init__(
        self,
        rag: RAGService | None = None,
        ai: AIService | None = None,
        web: TavilySearch | None = None,
        memory: AgentMemory | None = None,
        memory_turns: int = 3,
    ) -> None:
        settings = get_settings()

        self.rag = rag or RAGService()
        self.ai = ai or AIService()

        if web is not None:
            self.web = web
        else:
            try:
                self.web = TavilySearch()
            except Exception:  # noqa: BLE001 - optional dependency
                self.web = None

        self.max_turns = memory_turns
        self.memory = memory or InMemoryAgentMemory(max_turns=self.max_turns)

        # Determine the model to use based on available keys
        if settings.openai_api_key:
            self.model = "openai:gpt-4o"
        elif settings.anthropic_api_key:
            self.model = "anthropic:claude-3-5-sonnet-latest"
        else:
            raise RuntimeError(
                "No AI provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
            )

        # Create the pydantic-ai agent
        self.agent = Agent(
            self.model,
            deps_type=AgentDependencies,
            output_type=AgentResponse,
            instructions="""You are an intelligent assistant that can access both internal 
documents and web search.

When a user asks a question, you MUST follow this exact process:
1. First call route_query to determine whether to use internal documents (RAG) or web search
2. Based on the routing decision, call either search_documents or search_web
3. Generate a comprehensive answer citing your sources
4. Return an AgentResponse with the answer, sources, and the route_decision from step 1

IMPORTANT: You must ALWAYS call route_query first and include its result in your final response.

Use internal documents when:
- Keywords suggest recency: "latest", "current", "recent", "news", "today"
- Internal documents don't have good matches
- The question explicitly asks for web/online information
- Previous conversation context suggests web search

Always cite your sources clearly and provide helpful, accurate responses.""",
        )

        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register tools for the pydantic-ai agent."""

        @self.agent.tool
        async def route_query(ctx: RunContext[AgentDependencies], question: str) -> RouteDecision:
            """Determine whether to use RAG or web search for this query."""
            lowered = question.lower()
            web_keywords = ["web", "latest", "news", "today", "current", "recent", "update"]
            prefer_web = any(keyword in lowered for keyword in web_keywords) or "http" in lowered

            # Check for good internal matches
            try:
                internal_results = ctx.deps.rag_service.retrieve_with_sources(question, k=2)
                has_good_internal_match = any(
                    result["relevance_score"] > 0.7 for result in internal_results
                )
                confidence = max(
                    max((result["relevance_score"] for result in internal_results), default=0.0),
                    0.0,
                )
            except Exception:
                has_good_internal_match = False
                confidence = 0.0

            if ctx.deps.web_search is None:
                return RouteDecision(
                    route="rag",
                    reason="Web search unavailable; using local knowledge base",
                    confidence=min(confidence + 0.3, 1.0),
                )

            if has_good_internal_match and not prefer_web:
                return RouteDecision(
                    route="rag",
                    reason="Found relevant internal documents",
                    confidence=max(0.0, min(1.0, confidence)),
                )

            if prefer_web:
                return RouteDecision(
                    route="web", reason="Detected recency/web intent", confidence=0.8
                )

            return RouteDecision(
                route="rag",
                reason="Using internal knowledge base as primary source",
                confidence=max(0.0, min(1.0, confidence)),
            )

        @self.agent.tool
        async def search_documents(
            ctx: RunContext[AgentDependencies], question: str, max_results: int = 4
        ) -> list[SourceInfo]:
            """Search internal documents using RAG."""
            try:
                results = ctx.deps.rag_service.retrieve_with_sources(question, k=max_results)
                return [
                    SourceInfo(
                        content=result["content"],
                        source_type="document",
                        title=result.get("title"),
                        relevance_score=result.get("relevance_score"),
                        document_id=result.get("document_id"),
                    )
                    for result in results
                ]
            except Exception:
                return []

        @self.agent.tool
        async def search_web(
            ctx: RunContext[AgentDependencies], question: str
        ) -> tuple[list[SourceInfo], str | None]:
            """Search the web using Tavily."""
            if ctx.deps.web_search is None:
                return [], None

            try:
                snippets, direct = await ctx.deps.web_search.search_with_answer(question)
                sources = [
                    SourceInfo(content=snippet, source_type="web", title="Web Result")
                    for snippet in snippets
                    if snippet
                ]
                return sources, direct
            except Exception:
                return [], None

    def _session_key(self, session_id: str | None) -> str:
        """Generate session key for memory storage."""
        return session_id or "default"

    async def _commit_turn(self, session_key: str, question: str, answer: str) -> None:
        """Save the conversation turn to memory."""
        from langchain_core.messages import AIMessage, HumanMessage

        await self.memory.append(
            session_key,
            [HumanMessage(content=question), AIMessage(content=answer)],
        )

    async def ask(
        self, question: str, session_id: str | None = None, stream: bool = False
    ) -> AgentResponse | AsyncIterator[str]:
        """Ask the agent a question and get a structured response."""
        session_key = self._session_key(session_id)

        # Load conversation history
        try:
            history = await self.memory.read(session_key)
        except Exception:
            history = []

        # Create dependencies for this request
        deps = AgentDependencies(
            rag_service=self.rag,
            ai_service=self.ai,
            web_search=self.web,
            memory=self.memory,
            session_id=session_id,
        )

        # Add conversation history to the context
        context_with_history = question
        if history:
            # Format recent conversation history
            recent_history = history[-4:]  # Last 2 turns (4 messages)
            history_text = "\n".join(
                [
                    f"{'Human' if i % 2 == 0 else 'Assistant'}: {msg.content}"
                    for i, msg in enumerate(recent_history)
                ]
            )
            context_with_history = (
                f"Recent conversation:\n{history_text}\n\nCurrent question: {question}"
            )

        if stream:
            # For streaming, we'll need to handle differently
            # This is a simplified version - full streaming would require more work
            response = await self.agent.run(context_with_history, deps=deps)

            async def stream_response():
                # Stream the answer in chunks
                answer = response.output.answer
                chunk_size = 50
                for i in range(0, len(answer), chunk_size):
                    yield answer[i : i + chunk_size]

                # Save conversation after streaming
                await self._commit_turn(session_key, question, answer)

            return stream_response()
        else:
            # Run the agent and get structured response
            response = await self.agent.run(context_with_history, deps=deps)

            # Save conversation turn to memory
            await self._commit_turn(session_key, question, response.output.answer)

            # Update session_id in response
            response.output.session_id = session_id
            return response.output
