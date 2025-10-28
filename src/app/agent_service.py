from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

from app.dependencies import get_ai_service
from app.rag_service import RAGService
from app.web_search import TavilySearch


class AgentService:
    def __init__(self) -> None:
        self.rag = RAGService()
        self.ai = get_ai_service()
        try:
            self.web = TavilySearch()
        except Exception:
            self.web = None

    async def route(self, question: str) -> Literal["rag", "web"]:
        # naive heuristic: prefer RAG unless explicit "web" keyword
        return "web" if "web" in question.lower() else "rag"

    async def answer(self, question: str, stream: bool = False):
        choice = await self.route(question)
        if choice == "rag":
            contexts = self.rag.retrieve(question)
            return await self.ai.generate_answer(question, contexts, stream=stream)
        # web path
        if self.web is not None:
            snippets, direct = await self.web.search_with_answer(question)
            # Prefer grounded synthesis; if weak, fall back to Tavily's direct answer
            if stream:
                return await self.ai.generate_answer(question, snippets, stream=True)
            answer = await self.ai.generate_answer(question, snippets, stream=False)
            if (not answer or "I don't know" in answer) and direct:
                return direct
            return answer
        if stream:

            async def gen() -> AsyncIterator[str]:
                yield "[web search not implemented yet]"

            return gen()
        return "[web search not implemented yet]"
