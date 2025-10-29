from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agent_service import AgentService
from app.dependencies import get_agent_memory
from app.web_search import TavilySearch

agent_router = APIRouter()
agent = AgentService(memory=get_agent_memory())


@agent_router.get("/agent/chat")
async def agent_chat(q: str, stream: bool | None = None, session: str | None = None):
    effective_stream = stream is True
    if effective_stream:
        chunks = await agent.answer(q, stream=True, session=session)  # type: ignore[assignment]
        return StreamingResponse(chunks, media_type="text/plain")
    ans = await agent.answer(q, stream=False, session=session)  # type: ignore[assignment]
    return {"answer": ans}


@agent_router.get("/agent/debug/web")
async def agent_debug_web(q: str):
    """Return raw web search contexts and Tavily's direct answer for debugging."""
    try:
        search = TavilySearch()
        snippets, direct = await search.search_with_answer(q)
        return {"snippets": snippets, "tavily_answer": direct}
    except Exception as exc:  # noqa: BLE001
        return {"snippets": [], "tavily_answer": None, "error": str(exc)}
