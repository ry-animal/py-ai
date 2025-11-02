from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from starlette.responses import Response as StarletteResponse

from app.dependencies import get_agent_memory
from app.pydantic_agent_service import PydanticAgentService

# Try to import AG-UI components, gracefully handle if not available
try:
    from pydantic_ai.ag_ui import handle_ag_ui_request

    AG_UI_AVAILABLE = True
except ImportError:
    AG_UI_AVAILABLE = False

pydantic_agent_router = APIRouter(prefix="/pydantic-agent", tags=["pydantic-agent"])

# Lazy initialization to avoid API key requirements during import
agent_service = None


def get_pydantic_agent_service():
    """Get or create pydantic agent service."""
    global agent_service
    if agent_service is None:
        agent_service = PydanticAgentService(memory=get_agent_memory())
    return agent_service


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    question: str
    session_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    answer: str
    sources: list[dict] = []
    route_decision: dict = {}
    session_id: str | None = None


@pydantic_agent_router.post("/chat", response_model=None)
async def pydantic_agent_chat(request: ChatRequest):
    """Chat with the pydantic-ai agent."""
    if request.stream:
        response_stream = await get_pydantic_agent_service().ask(
            request.question, session_id=request.session_id, stream=True
        )
        return StreamingResponse(response_stream, media_type="text/plain")

    response = await get_pydantic_agent_service().ask(
        request.question, session_id=request.session_id, stream=False
    )

    return ChatResponse(
        answer=response.answer,
        sources=[source.model_dump() for source in response.sources],
        route_decision=response.route_decision.model_dump(),
        session_id=response.session_id,
    )


@pydantic_agent_router.get("/chat", response_model=None)
async def pydantic_agent_chat_get(q: str, stream: bool | None = None, session: str | None = None):
    """GET endpoint for chat (compatible with existing agent interface)."""
    effective_stream = stream is True

    if effective_stream:
        response_stream = await get_pydantic_agent_service().ask(q, session_id=session, stream=True)
        return StreamingResponse(response_stream, media_type="text/plain")

    response = await get_pydantic_agent_service().ask(q, session_id=session, stream=False)

    return {
        "answer": response.answer,
        "sources": [source.model_dump() for source in response.sources],
        "route_decision": response.route_decision.model_dump(),
        "session_id": response.session_id,
    }


# AG-UI Integration endpoints
if AG_UI_AVAILABLE:

    @pydantic_agent_router.post("/ag-ui")
    async def ag_ui_endpoint(request: Request) -> Response:
        """AG-UI compatible endpoint for frontend integration."""
        return await handle_ag_ui_request(get_pydantic_agent_service().agent, request)

    @pydantic_agent_router.get("/ag-ui/app")
    async def ag_ui_app() -> StarletteResponse:
        """Serve the AG-UI application."""
        app = get_pydantic_agent_service().agent.to_ag_ui()
        return app
else:

    @pydantic_agent_router.get("/ag-ui/status")
    async def ag_ui_status() -> dict:
        """Status endpoint when AG-UI is not available."""
        return {
            "ag_ui_available": False,
            "message": "AG-UI not installed. Install with: pip install 'pydantic-ai[ag-ui]'",
        }


@pydantic_agent_router.get("/status")
async def pydantic_agent_status() -> dict:
    """Status endpoint for the pydantic-ai agent."""
    return {
        "status": "ready",
        "model": get_pydantic_agent_service().model,
        "web_search_available": get_pydantic_agent_service().web is not None,
        "ag_ui_available": AG_UI_AVAILABLE,
        "memory_type": type(get_pydantic_agent_service().memory).__name__,
    }


@pydantic_agent_router.get("/debug/capabilities")
async def debug_capabilities() -> dict:
    """Debug endpoint to show agent capabilities."""
    return {
        "tools": [
            {"name": "route_query", "description": "Determine whether to use RAG or web search"},
            {"name": "search_documents", "description": "Search internal documents using RAG"},
            {"name": "search_web", "description": "Search the web using Tavily"},
        ],
        "output_schema": get_pydantic_agent_service().agent.output_type.model_json_schema(),
        "dependencies": {
            "rag_service": "RAGService",
            "ai_service": "AIService",
            "web_search": "TavilySearch" if get_pydantic_agent_service().web else None,
            "memory": type(get_pydantic_agent_service().memory).__name__,
        },
    }
