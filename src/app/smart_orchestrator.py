from __future__ import annotations

from collections.abc import AsyncIterator
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.agent_service import AgentService
from app.hybrid_agent_service import HybridAgentService
from app.pydantic_agent_service import PydanticAgentService


class AgentType(str, Enum):
    """Available agent types."""

    LANGGRAPH = "langgraph"
    PYDANTIC_AI = "pydantic_ai"
    HYBRID = "hybrid"


class TaskComplexity(str, Enum):
    """Task complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class TaskCategory(str, Enum):
    """Task categories."""

    QA = "question_answering"
    SEARCH = "search"
    ANALYSIS = "analysis"
    WORKFLOW = "workflow"
    STRUCTURED_OUTPUT = "structured_output"


class OrchestrationDecision(BaseModel):
    """Decision made by the orchestrator."""

    chosen_agent: AgentType
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    task_complexity: TaskComplexity
    task_category: TaskCategory
    fallback_agents: list[AgentType] = Field(default_factory=list)


class SmartOrchestrator:
    """
    Smart orchestrator that chooses the best agent (LangGraph, Pydantic-AI, or Hybrid)
    based on the task characteristics, user requirements, and system capabilities.
    """

    def __init__(self):
        self.langgraph_agent = AgentService()
        self.pydantic_agent = PydanticAgentService()
        self.hybrid_agent = HybridAgentService()

    async def analyze_task(
        self, question: str, context: dict[str, Any] | None = None
    ) -> OrchestrationDecision:
        """Analyze the task and decide which agent to use."""
        context = context or {}

        # Analyze question characteristics - ensure question is a string
        if not isinstance(question, str):
            question = str(question)
        question_lower = question.lower()

        # Determine task category
        task_category = self._categorize_task(question_lower)

        # Determine complexity
        task_complexity = self._assess_complexity(question_lower, context)

        # Make agent selection based on analysis
        agent_choice, reasoning, confidence, fallbacks = self._select_agent(
            task_category, task_complexity, question_lower, context
        )

        return OrchestrationDecision(
            chosen_agent=agent_choice,
            reasoning=reasoning,
            confidence=confidence,
            task_complexity=task_complexity,
            task_category=task_category,
            fallback_agents=fallbacks,
        )

    def _categorize_task(self, question: str) -> TaskCategory:
        """Categorize the task based on question content."""

        # Workflow indicators
        workflow_keywords = [
            "step by step",
            "process",
            "workflow",
            "sequence",
            "pipeline",
            "multiple",
        ]
        if any(keyword in question for keyword in workflow_keywords):
            return TaskCategory.WORKFLOW

        # Structured output indicators
        structured_keywords = [
            "json",
            "format",
            "structure",
            "schema",
            "fields",
            "extract",
            "parse",
        ]
        if any(keyword in question for keyword in structured_keywords):
            return TaskCategory.STRUCTURED_OUTPUT

        # Analysis indicators
        analysis_keywords = ["analyze", "compare", "evaluate", "assess", "review", "summary"]
        if any(keyword in question for keyword in analysis_keywords):
            return TaskCategory.ANALYSIS

        # Search indicators
        search_keywords = ["find", "search", "lookup", "latest", "current", "recent", "news"]
        if any(keyword in question for keyword in search_keywords):
            return TaskCategory.SEARCH

        # Default to Q&A
        return TaskCategory.QA

    def _assess_complexity(self, question: str, context: dict[str, Any]) -> TaskComplexity:
        """Assess task complexity based on various factors."""

        complexity_score = 0

        # Length-based complexity
        word_count = len(question.split())
        if word_count > 20:
            complexity_score += 2
        elif word_count > 10:
            complexity_score += 1

        # Multi-part questions
        if any(
            indicator in question for indicator in ["and", "then", "after", "also", "additionally"]
        ):
            complexity_score += 2

        # Complex keywords
        complex_keywords = ["multi-step", "complex", "detailed", "comprehensive", "thorough"]
        if any(keyword in question for keyword in complex_keywords):
            complexity_score += 3

        # Context-based complexity
        if context.get("requires_memory", False):
            complexity_score += 1
        if context.get("multi_turn", False):
            complexity_score += 1
        if context.get("requires_validation", False):
            complexity_score += 1

        # Determine complexity level
        if complexity_score >= 5:
            return TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE

    def _select_agent(
        self,
        category: TaskCategory,
        complexity: TaskComplexity,
        question: str,
        context: dict[str, Any],
    ) -> tuple[AgentType, str, float, list[AgentType]]:
        """Select the best agent based on task analysis."""

        # Priority matrix for agent selection
        selection_rules = {
            # Simple structured output → Pydantic-AI
            (TaskCategory.STRUCTURED_OUTPUT, TaskComplexity.SIMPLE): (
                AgentType.PYDANTIC_AI,
                "Simple structured output best handled by pydantic-ai type safety",
                0.9,
                [AgentType.HYBRID],
            ),
            # Complex structured output → Hybrid
            (TaskCategory.STRUCTURED_OUTPUT, TaskComplexity.COMPLEX): (
                AgentType.HYBRID,
                "Complex structured output requires both workflow control and type safety",
                0.85,
                [AgentType.PYDANTIC_AI, AgentType.LANGGRAPH],
            ),
            # Simple Q&A → Pydantic-AI
            (TaskCategory.QA, TaskComplexity.SIMPLE): (
                AgentType.PYDANTIC_AI,
                "Simple Q&A benefits from structured output and modern patterns",
                0.8,
                [AgentType.LANGGRAPH],
            ),
            # Complex workflows → LangGraph
            (TaskCategory.WORKFLOW, TaskComplexity.COMPLEX): (
                AgentType.LANGGRAPH,
                "Complex workflows require LangGraph's advanced state management",
                0.9,
                [AgentType.HYBRID],
            ),
            # Moderate workflows → Hybrid
            (TaskCategory.WORKFLOW, TaskComplexity.MODERATE): (
                AgentType.HYBRID,
                "Moderate workflows benefit from both structure and workflow control",
                0.85,
                [AgentType.LANGGRAPH, AgentType.PYDANTIC_AI],
            ),
            # Search tasks → Pydantic-AI (for better source attribution)
            (TaskCategory.SEARCH, TaskComplexity.SIMPLE): (
                AgentType.PYDANTIC_AI,
                "Search tasks benefit from structured source attribution",
                0.8,
                [AgentType.HYBRID],
            ),
            # Complex search → Hybrid
            (TaskCategory.SEARCH, TaskComplexity.COMPLEX): (
                AgentType.HYBRID,
                "Complex search requires workflow control with structured sources",
                0.85,
                [AgentType.PYDANTIC_AI, AgentType.LANGGRAPH],
            ),
            # Analysis → Hybrid (needs both structure and reasoning)
            (TaskCategory.ANALYSIS, TaskComplexity.MODERATE): (
                AgentType.HYBRID,
                "Analysis benefits from structured reasoning and workflow control",
                0.85,
                [AgentType.PYDANTIC_AI, AgentType.LANGGRAPH],
            ),
        }

        # Try exact match first
        key = (category, complexity)
        if key in selection_rules:
            return selection_rules[key]

        # Fallback logic based on context preferences
        if context.get("prefer_structured", False):
            return (
                AgentType.PYDANTIC_AI,
                "User preference for structured output",
                0.7,
                [AgentType.HYBRID],
            )

        if context.get("complex_workflow", False):
            return (AgentType.LANGGRAPH, "Complex workflow requirements", 0.7, [AgentType.HYBRID])

        # Default to hybrid for unknown cases
        return (
            AgentType.HYBRID,
            "Balanced approach for unclear requirements",
            0.6,
            [AgentType.PYDANTIC_AI, AgentType.LANGGRAPH],
        )

    async def ask(
        self,
        question: str,
        session_id: str | None = None,
        stream: bool = False,
        context: dict[str, Any] | None = None,
        force_agent: AgentType | None = None,
    ) -> dict[str, Any] | AsyncIterator[str]:
        """
        Ask a question using the best agent for the task.

        Args:
            question: The question to ask
            session_id: Session ID for conversation continuity
            stream: Whether to stream the response
            context: Additional context for agent selection
            force_agent: Force a specific agent (for testing/comparison)
        """

        # Analyze task and select agent
        if force_agent:
            decision = OrchestrationDecision(
                chosen_agent=force_agent,
                reasoning=f"Forced selection: {force_agent}",
                confidence=1.0,
                task_complexity=TaskComplexity.SIMPLE,
                task_category=TaskCategory.QA,
            )
        else:
            decision = await self.analyze_task(question, context)

        # Route to appropriate agent
        try:
            if decision.chosen_agent == AgentType.LANGGRAPH:
                response = await self.langgraph_agent.answer(
                    question, stream=stream, session=session_id
                )

                if stream:
                    return response
                else:
                    return {
                        "answer": response,
                        "orchestration": decision.model_dump(),
                        "agent_used": "langgraph",
                        "session_id": session_id,
                    }

            elif decision.chosen_agent == AgentType.PYDANTIC_AI:
                response = await self.pydantic_agent.ask(
                    question, session_id=session_id, stream=stream
                )

                if stream:
                    return response
                else:
                    result = response.model_dump()
                    result["orchestration"] = decision.model_dump()
                    result["agent_used"] = "pydantic_ai"
                    return result

            elif decision.chosen_agent == AgentType.HYBRID:
                response = await self.hybrid_agent.ask(
                    question, session_id=session_id, stream=stream
                )

                if stream:
                    return response
                else:
                    result = response.model_dump()
                    result["orchestration"] = decision.model_dump()
                    result["agent_used"] = "hybrid"
                    return result

        except Exception as e:
            # Try fallback agents
            for fallback_agent in decision.fallback_agents:
                try:
                    if fallback_agent == AgentType.PYDANTIC_AI:
                        response = await self.pydantic_agent.ask(
                            question, session_id=session_id, stream=stream
                        )
                        if not stream:
                            result = response.model_dump()
                            result["orchestration"] = decision.model_dump()
                            result["agent_used"] = "pydantic_ai_fallback"
                            result["original_error"] = str(e)
                            return result
                        return response
                except Exception:
                    continue

            # If all agents fail, return error
            error_msg = str(e) if "e" in locals() else "Unknown error occurred"
            if stream:

                async def error_stream():
                    yield f"Error: All agents failed. Original error: {error_msg}"

                return error_stream()
            else:
                return {
                    "answer": (
                        f"I apologize, but I encountered an error processing "
                        f"your request: {error_msg}"
                    ),
                    "orchestration": decision.model_dump(),
                    "agent_used": "error",
                    "error": error_msg,
                }
