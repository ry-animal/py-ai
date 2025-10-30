# ruff: noqa: S101 - pytest-style asserts expected

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage

from app.agent_memory import InMemoryAgentMemory
from app.agent_service import AgentService


class FakeRAG:
    def __init__(self, contexts: list[str]) -> None:
        self.contexts = contexts
        self.queries: list[str] = []

    def retrieve(self, query: str, k: int = 4) -> list[str]:  # noqa: ARG002 - signature parity
        self.queries.append(query)
        return self.contexts

    def retrieve_with_sources(self, query: str, k: int = 4) -> list[dict]:  # noqa: ARG002 - signature parity
        self.queries.append(query)
        return [
            {
                "content": context,
                "metadata": {"source": f"test_doc_{i}", "document_id": f"doc_{i}"},
                "relevance_score": 0.8,
            }
            for i, context in enumerate(self.contexts)
        ]


class FakeAI:
    def __init__(self, answer: str = "ok", stream_chunks: list[str] | None = None) -> None:
        self.answer = answer
        self.stream_chunks = stream_chunks or [answer]
        self.calls: list[tuple[str, list[str], bool]] = []

    async def generate_answer(
        self, question: str, contexts: list[str], stream: bool = False
    ) -> str | AsyncIterator[str]:
        self.calls.append((question, contexts, stream))
        if stream:

            async def gen() -> AsyncIterator[str]:
                for chunk in self.stream_chunks:
                    yield chunk

            return gen()
        return self.answer


class FakeWeb:
    def __init__(self, snippets: list[str], direct: str | None = None) -> None:
        self.snippets = snippets
        self.direct = direct
        self.queries: list[str] = []

    async def search_with_answer(self, query: str) -> tuple[list[str], str | None]:
        self.queries.append(query)
        return self.snippets, self.direct


def test_agent_service_rag_flow() -> None:
    rag = FakeRAG(["doc piece"])
    ai = FakeAI(answer="rag answer")

    async def run() -> None:
        memory = InMemoryAgentMemory(max_turns=3)
        service = AgentService(rag=rag, ai=ai, web=None, memory=memory)
        result = await service.answer("Explain the docs", stream=False, session="s1")
        assert result == "rag answer"
        assert ai.calls[0][2] is False
        stored = await memory.read("s1")
        assert isinstance(stored[0], HumanMessage)
        assert isinstance(stored[1], AIMessage)

    asyncio.run(run())


def test_agent_service_web_route() -> None:
    rag = FakeRAG(["fallback"])
    ai = FakeAI(answer="web answer")
    web = FakeWeb(["web snippet"], direct="direct hit")

    async def run() -> None:
        memory = InMemoryAgentMemory(max_turns=3)
        service = AgentService(rag=rag, ai=ai, web=web, memory=memory)
        result = await service.answer("Latest FastAPI news", stream=False, session="s2")
        assert result == "web answer"
        assert web.queries == ["Latest FastAPI news"]
        assert ai.calls[0][1] == ["web snippet"]

    asyncio.run(run())


def test_agent_service_streams_reasoning_and_updates_memory() -> None:
    rag = FakeRAG(["knowledge chunk"])
    ai = FakeAI(answer="final", stream_chunks=["chunk1", "chunk2"])

    async def run() -> None:
        memory = InMemoryAgentMemory(max_turns=3)
        service = AgentService(rag=rag, ai=ai, web=None, memory=memory)
        stream = await service.answer("Tell me more", stream=True, session="s3")
        chunks: list[str] = []
        async for piece in stream:
            chunks.append(piece)
        combined = "".join(chunks)
        assert "chunk1" in combined and "chunk2" in combined
        assert "[route]" in combined
        stored = await memory.read("s3")
        assert isinstance(stored[-1], AIMessage)

    asyncio.run(run())
