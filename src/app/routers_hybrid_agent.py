from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import get_agent_memory
from app.hybrid_agent_service import HybridAgentService

hybrid_agent_router = APIRouter(prefix="/hybrid-agent", tags=["hybrid-agent"])

# Lazy initialization to avoid API key requirements during import
hybrid_service = None


def get_hybrid_service():
    """Get or create hybrid agent service."""
    global hybrid_service
    if hybrid_service is None:
        hybrid_service = HybridAgentService(memory=get_agent_memory())
    return hybrid_service


class HybridChatRequest(BaseModel):
    """Request model for hybrid agent chat."""

    question: str
    session_id: str | None = None
    stream: bool = False


@hybrid_agent_router.post("/chat", response_model=None)
async def hybrid_agent_chat(request: HybridChatRequest):
    """
    Chat with the hybrid agent that combines LangGraph workflow orchestration
    with pydantic-ai structured tools and output validation.

    This approach gives you:
    - Complex workflow control from LangGraph
    - Type-safe tools and validation from pydantic-ai
    - Structured responses with comprehensive metadata
    """
    if request.stream:
        response_stream = await get_hybrid_service().ask(
            request.question, session_id=request.session_id, stream=True
        )
        return StreamingResponse(response_stream, media_type="text/plain")

    response = await get_hybrid_service().ask(
        request.question, session_id=request.session_id, stream=False
    )

    return response.model_dump()


@hybrid_agent_router.get("/chat", response_model=None)
async def hybrid_agent_chat_get(q: str, stream: bool | None = None, session: str | None = None):
    """GET endpoint for hybrid agent chat (compatible with existing interfaces)."""
    effective_stream = stream is True

    if effective_stream:
        response_stream = await get_hybrid_service().ask(q, session_id=session, stream=True)
        return StreamingResponse(response_stream, media_type="text/plain")

    response = await get_hybrid_service().ask(q, session_id=session, stream=False)

    return response.model_dump()


@hybrid_agent_router.get("/status")
async def hybrid_agent_status() -> dict:
    """Status endpoint for the hybrid agent."""
    return {
        "status": "ready",
        "architecture": "LangGraph + Pydantic-AI Hybrid",
        "workflow_engine": "LangGraph StateGraph",
        "tools_engine": "Pydantic-AI Structured Tools",
        "features": [
            "Complex workflow orchestration",
            "Type-safe tool execution",
            "Structured output validation",
            "Intelligent routing decisions",
            "Comprehensive logging and observability",
        ],
        "web_search_available": get_hybrid_service().web is not None,
        "memory_type": type(get_hybrid_service().memory).__name__,
    }


@hybrid_agent_router.get("/architecture")
async def hybrid_architecture() -> dict:
    """Detailed architecture information for the hybrid approach."""
    return {
        "design_pattern": "Hybrid Architecture",
        "components": {
            "workflow_orchestration": {
                "engine": "LangGraph",
                "purpose": "State management, conditional routing, complex workflows",
                "nodes": ["planning", "rag_execution", "web_execution"],
                "benefits": ["Complex control flow", "State persistence", "Conditional logic"],
            },
            "tool_execution": {
                "engine": "Pydantic-AI",
                "purpose": "Type-safe tools, structured output, validation",
                "tools": ["route_query", "search_documents", "search_web"],
                "benefits": [
                    "Type safety",
                    "Structured output",
                    "Validation",
                    "AG-UI compatibility",
                ],
            },
            "integration_layer": {
                "purpose": "Bridge between LangGraph nodes and pydantic-ai tools",
                "method": "Pydantic-AI tools called within LangGraph nodes",
                "data_flow": (
                    "LangGraph state → Pydantic-AI tools → " "Structured output → LangGraph state"
                ),
            },
        },
        "advantages": [
            "Best of both worlds: LangGraph workflow control + Pydantic-AI type safety",
            "Complex multi-step workflows with structured validation",
            "Gradual migration path from pure LangGraph to hybrid approach",
            "Maintains backward compatibility while adding modern features",
        ],
        "use_cases": [
            "Complex multi-agent workflows",
            "Type-safe tool execution within workflows",
            "Structured output requirements with complex routing",
            "Production systems requiring both flexibility and safety",
        ],
    }


@hybrid_agent_router.get("/comparison")
async def architecture_comparison() -> dict:
    """Compare the three agent architectures available."""
    return {
        "architectures": {
            "langgraph_only": {
                "endpoint": "/agent/chat",
                "strengths": ["Complex workflows", "State management", "Mature ecosystem"],
                "weaknesses": ["Less type safety", "Manual output structuring"],
                "best_for": ["Complex multi-step processes", "Workflow orchestration"],
            },
            "pydantic_ai_only": {
                "endpoint": "/pydantic-agent/chat",
                "strengths": ["Type safety", "Structured output", "Modern patterns", "AG-UI ready"],
                "weaknesses": ["Limited workflow complexity", "Newer ecosystem"],
                "best_for": [
                    "Type-safe AI applications",
                    "Structured responses",
                    "Frontend integration",
                ],
            },
            "hybrid": {
                "endpoint": "/hybrid-agent/chat",
                "strengths": ["Best of both", "Complex workflows + type safety", "Future-proof"],
                "weaknesses": ["More complexity", "Learning curve"],
                "best_for": ["Production systems", "Complex requirements", "Migration scenarios"],
            },
        },
        "migration_path": [
            "1. Start with LangGraph for complex workflows",
            "2. Migrate individual nodes to use pydantic-ai tools",
            "3. Add structured output validation",
            "4. Eventually move to pure pydantic-ai if workflow complexity allows",
        ],
    }
