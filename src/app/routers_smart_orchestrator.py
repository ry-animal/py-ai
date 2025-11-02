from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.smart_orchestrator import AgentType, SmartOrchestrator

orchestrator_router = APIRouter(prefix="/smart", tags=["smart-orchestrator"])

# Lazy initialization to avoid API key requirements during import
orchestrator = None


def get_orchestrator():
    """Get or create smart get_orchestrator()."""
    global orchestrator
    if orchestrator is None:
        orchestrator = SmartOrchestrator()
    return orchestrator


class SmartChatRequest(BaseModel):
    """Request model for smart orchestrator chat."""

    question: str
    session_id: str | None = None
    stream: bool = False
    context: dict[str, Any] | None = None
    force_agent: AgentType | None = None


@orchestrator_router.post("/chat", response_model=None)
async def smart_chat(request: SmartChatRequest):
    """
    Chat using the smart orchestrator that automatically chooses the best agent
    (LangGraph, Pydantic-AI, or Hybrid) based on task characteristics.

    The orchestrator analyzes:
    - Task complexity (simple/moderate/complex)
    - Task category (Q&A, search, analysis, workflow, structured output)
    - User context and preferences
    - System capabilities

    Then routes to the most appropriate agent for optimal results.
    """
    response = await get_orchestrator().ask(
        question=request.question,
        session_id=request.session_id,
        stream=request.stream,
        context=request.context,
        force_agent=request.force_agent,
    )

    if request.stream:
        return StreamingResponse(response, media_type="text/plain")

    return response


@orchestrator_router.get("/chat", response_model=None)
async def smart_chat_get(
    q: str,
    stream: bool | None = None,
    session: str | None = None,
    force_agent: AgentType | None = None,
):
    """GET endpoint for smart orchestrator chat."""
    effective_stream = stream is True

    response = await get_orchestrator().ask(
        question=q, session_id=session, stream=effective_stream, force_agent=force_agent
    )

    if effective_stream:
        return StreamingResponse(response, media_type="text/plain")

    return response


@orchestrator_router.post("/analyze")
async def analyze_task(request: dict[str, Any]):
    """
    Analyze a task and get orchestration decision without executing.

    Useful for understanding which agent would be chosen and why.
    """
    question = request.get("question", "")
    context = request.get("context", {})

    decision = await get_orchestrator().analyze_task(question, context)

    return {
        "decision": decision.model_dump(),
        "explanation": {
            "why_this_agent": decision.reasoning,
            "confidence_level": f"{decision.confidence:.1%}",
            "fallback_options": decision.fallback_agents,
            "task_assessment": {
                "complexity": decision.task_complexity,
                "category": decision.task_category,
            },
        },
    }


@orchestrator_router.get("/agents/comparison")
async def agent_comparison():
    """Compare all available agents and their strengths."""
    return {
        "available_agents": {
            "langgraph": {
                "endpoint": "/agent/chat",
                "strengths": [
                    "Complex multi-step workflows",
                    "Advanced state management",
                    "Conditional logic and routing",
                    "Mature LangChain ecosystem",
                ],
                "best_for": [
                    "Complex workflows",
                    "Multi-agent coordination",
                    "State-dependent processing",
                    "Legacy LangChain integrations",
                ],
                "limitations": [
                    "Less type safety",
                    "Manual output structuring",
                    "Steeper learning curve",
                ],
            },
            "pydantic_ai": {
                "endpoint": "/pydantic-agent/chat",
                "strengths": [
                    "Type-safe operations",
                    "Structured output validation",
                    "Modern FastAPI-like patterns",
                    "AG-UI compatibility",
                    "Better IDE support",
                ],
                "best_for": [
                    "Structured responses",
                    "Type-safe AI applications",
                    "Frontend integrations",
                    "Developer experience",
                ],
                "limitations": [
                    "Limited workflow complexity",
                    "Newer ecosystem",
                    "Less complex routing",
                ],
            },
            "hybrid": {
                "endpoint": "/hybrid-agent/chat",
                "strengths": [
                    "Best of both worlds",
                    "Complex workflows + type safety",
                    "Structured validation within workflows",
                    "Migration-friendly",
                ],
                "best_for": [
                    "Production systems",
                    "Complex requirements",
                    "Gradual migrations",
                    "Enterprise applications",
                ],
                "limitations": [
                    "Added complexity",
                    "Learning curve",
                    "Potential performance overhead",
                ],
            },
            "smart_orchestrator": {
                "endpoint": "/smart/chat",
                "strengths": [
                    "Automatic agent selection",
                    "Task-aware routing",
                    "Fallback mechanisms",
                    "Simplified interface",
                ],
                "best_for": [
                    "General-purpose AI applications",
                    "Varied workloads",
                    "Prototyping",
                    "User-facing applications",
                ],
                "limitations": [
                    "Orchestration overhead",
                    "Potential over-engineering for simple tasks",
                ],
            },
        },
        "selection_criteria": {
            "simple_qa": "pydantic_ai",
            "complex_workflows": "langgraph",
            "structured_output": "pydantic_ai",
            "mixed_requirements": "hybrid",
            "unknown_requirements": "smart_orchestrator",
        },
    }


@orchestrator_router.get("/status")
async def orchestrator_status():
    """Status of the smart orchestrator and all underlying agents."""
    return {
        "status": "ready",
        "architecture": "Smart Multi-Agent Orchestrator",
        "available_agents": [agent.value for agent in AgentType],
        "selection_logic": {
            "task_categories": [
                "question_answering",
                "search",
                "analysis",
                "workflow",
                "structured_output",
            ],
            "complexity_levels": ["simple", "moderate", "complex"],
            "selection_factors": [
                "Task complexity assessment",
                "Category classification",
                "User context preferences",
                "Agent capabilities matching",
            ],
        },
        "features": [
            "Automatic agent selection",
            "Task complexity analysis",
            "Fallback mechanisms",
            "Comprehensive logging",
            "Performance optimization",
        ],
    }


@orchestrator_router.get("/debug/decision-matrix")
async def debug_decision_matrix():
    """Debug endpoint showing the decision matrix for agent selection."""
    return {
        "decision_rules": {
            "structured_output_simple": {
                "agent": "pydantic_ai",
                "reasoning": "Simple structured output best handled by pydantic-ai type safety",
                "confidence": 0.9,
            },
            "structured_output_complex": {
                "agent": "hybrid",
                "reasoning": (
                    "Complex structured output requires both workflow control " "and type safety"
                ),
                "confidence": 0.85,
            },
            "qa_simple": {
                "agent": "pydantic_ai",
                "reasoning": "Simple Q&A benefits from structured output and modern patterns",
                "confidence": 0.8,
            },
            "workflow_complex": {
                "agent": "langgraph",
                "reasoning": "Complex workflows require LangGraph's advanced state management",
                "confidence": 0.9,
            },
            "workflow_moderate": {
                "agent": "hybrid",
                "reasoning": "Moderate workflows benefit from both structure and workflow control",
                "confidence": 0.85,
            },
            "search_simple": {
                "agent": "pydantic_ai",
                "reasoning": "Search tasks benefit from structured source attribution",
                "confidence": 0.8,
            },
            "search_complex": {
                "agent": "hybrid",
                "reasoning": "Complex search requires workflow control with structured sources",
                "confidence": 0.85,
            },
            "analysis_moderate": {
                "agent": "hybrid",
                "reasoning": "Analysis benefits from structured reasoning and workflow control",
                "confidence": 0.85,
            },
        },
        "complexity_factors": [
            "Word count (>20 words = +2, >10 words = +1)",
            "Multi-part questions (+2)",
            "Complex keywords (+3)",
            "Context requirements (+1 each)",
        ],
        "category_keywords": {
            "workflow": ["step by step", "process", "workflow", "sequence", "pipeline", "multiple"],
            "structured_output": [
                "json",
                "format",
                "structure",
                "schema",
                "fields",
                "extract",
                "parse",
            ],
            "analysis": ["analyze", "compare", "evaluate", "assess", "review", "summary"],
            "search": ["find", "search", "lookup", "latest", "current", "recent", "news"],
        },
    }
