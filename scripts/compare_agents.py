#!/usr/bin/env python3
"""
Comparison script for pydantic-ai vs LangGraph agent implementations.

This script tests both agent implementations with a set of test questions
and compares their performance, response quality, and consistency.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agent_service import AgentService
from app.pydantic_agent_service import PydanticAgentService


@dataclass
class TestCase:
    """Test case for agent comparison."""

    question: str
    category: str
    expected_route: str  # "rag" or "web"
    description: str


@dataclass
class AgentResult:
    """Result from an agent execution."""

    answer: str
    response_time: float
    route_used: str | None = None
    sources_count: int = 0
    error: str | None = None
    structured_output: dict[str, Any] | None = None


# Test cases covering different scenarios
TEST_CASES = [
    TestCase(
        question="What is machine learning?",
        category="general_knowledge",
        expected_route="rag",
        description="General ML question - should prefer internal docs if available",
    ),
    TestCase(
        question="What are the latest AI news from this week?",
        category="recency",
        expected_route="web",
        description="Recency question - should trigger web search",
    ),
    TestCase(
        question="How do I implement a REST API in Python?",
        category="technical",
        expected_route="rag",
        description="Technical question that might be in internal docs",
    ),
    TestCase(
        question="What is the current weather in San Francisco?",
        category="real_time",
        expected_route="web",
        description="Real-time query - requires web search",
    ),
    TestCase(
        question="Explain transformer neural networks",
        category="technical_deep",
        expected_route="rag",
        description="Deep technical question - prefer internal docs",
    ),
]


async def test_langgraph_agent(test_case: TestCase) -> AgentResult:
    """Test the LangGraph-based agent."""
    agent = AgentService()

    start_time = time.perf_counter()
    try:
        response = await agent.answer(test_case.question, stream=False)
        end_time = time.perf_counter()

        return AgentResult(
            answer=response,
            response_time=end_time - start_time,
            route_used=None,  # LangGraph doesn't expose route decision easily
            sources_count=0,  # Would need to inspect logs
        )
    except Exception as e:
        end_time = time.perf_counter()
        return AgentResult(answer="", response_time=end_time - start_time, error=str(e))


async def test_pydantic_agent(test_case: TestCase) -> AgentResult:
    """Test the pydantic-ai based agent."""
    agent = PydanticAgentService()

    start_time = time.perf_counter()
    try:
        response = await agent.ask(test_case.question, stream=False)
        end_time = time.perf_counter()

        return AgentResult(
            answer=response.answer,
            response_time=end_time - start_time,
            route_used=response.route_decision.route,
            sources_count=len(response.sources),
            structured_output={
                "route_decision": response.route_decision.model_dump(),
                "sources": [source.model_dump() for source in response.sources],
                "session_id": response.session_id,
                "direct_answer": response.direct_answer,
            },
        )
    except Exception as e:
        end_time = time.perf_counter()
        return AgentResult(answer="", response_time=end_time - start_time, error=str(e))


def analyze_results(
    test_case: TestCase,
    langgraph_result: AgentResult,
    pydantic_result: AgentResult,
) -> dict:
    """Analyze and compare results from both agents."""
    analysis = {
        "test_case": {
            "question": test_case.question,
            "category": test_case.category,
            "expected_route": test_case.expected_route,
            "description": test_case.description,
        },
        "langgraph": {
            "response_time": langgraph_result.response_time,
            "answer_length": len(langgraph_result.answer),
            "has_error": langgraph_result.error is not None,
            "error": langgraph_result.error,
        },
        "pydantic_ai": {
            "response_time": pydantic_result.response_time,
            "answer_length": len(pydantic_result.answer),
            "route_used": pydantic_result.route_used,
            "sources_count": pydantic_result.sources_count,
            "has_error": pydantic_result.error is not None,
            "error": pydantic_result.error,
            "route_matches_expected": pydantic_result.route_used == test_case.expected_route,
        },
        "comparison": {
            "speed_difference": langgraph_result.response_time - pydantic_result.response_time,
            "pydantic_faster": pydantic_result.response_time < langgraph_result.response_time,
            "both_succeeded": langgraph_result.error is None and pydantic_result.error is None,
        },
    }

    return analysis


async def run_comparison():
    """Run the full comparison between both agent implementations."""
    print("🚀 Starting Agent Comparison: Pydantic-AI vs LangGraph")
    print("=" * 60)

    results = []

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n📝 Test {i}/{len(TEST_CASES)}: {test_case.category}")
        print(f"   Question: {test_case.question}")
        print(f"   Expected route: {test_case.expected_route}")

        # Test LangGraph agent
        print("   🔍 Testing LangGraph agent...")
        langgraph_result = await test_langgraph_agent(test_case)

        # Test Pydantic-AI agent
        print("   🔍 Testing Pydantic-AI agent...")
        pydantic_result = await test_pydantic_agent(test_case)

        # Analyze results
        analysis = analyze_results(test_case, langgraph_result, pydantic_result)
        results.append(analysis)

        # Print immediate results
        print(f"   ⏱️  LangGraph: {langgraph_result.response_time:.2f}s")
        print(f"   ⏱️  Pydantic-AI: {pydantic_result.response_time:.2f}s")
        if pydantic_result.route_used:
            route_icon = "✅" if analysis["pydantic_ai"]["route_matches_expected"] else "❌"
            print(f"   🧭 Route: {pydantic_result.route_used} {route_icon}")
        if pydantic_result.sources_count > 0:
            print(f"   📚 Sources: {pydantic_result.sources_count}")

        if langgraph_result.error:
            print(f"   ❌ LangGraph Error: {langgraph_result.error}")
        if pydantic_result.error:
            print(f"   ❌ Pydantic-AI Error: {pydantic_result.error}")

    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)

    successful_tests = [r for r in results if r["comparison"]["both_succeeded"]]
    pydantic_faster_count = sum(1 for r in successful_tests if r["comparison"]["pydantic_faster"])
    correct_routes = sum(1 for r in results if r["pydantic_ai"]["route_matches_expected"])

    avg_langgraph_time = (
        sum(r["langgraph"]["response_time"] for r in successful_tests) / len(successful_tests)
        if successful_tests
        else 0
    )
    avg_pydantic_time = (
        sum(r["pydantic_ai"]["response_time"] for r in successful_tests) / len(successful_tests)
        if successful_tests
        else 0
    )

    print(f"🧪 Total tests: {len(TEST_CASES)}")
    print(f"✅ Both succeeded: {len(successful_tests)}")
    print(f"⚡ Pydantic-AI faster: {pydantic_faster_count}/{len(successful_tests)}")
    print(f"🎯 Correct routing: {correct_routes}/{len(TEST_CASES)}")
    print(f"⏱️  Avg LangGraph time: {avg_langgraph_time:.2f}s")
    print(f"⏱️  Avg Pydantic-AI time: {avg_pydantic_time:.2f}s")

    if avg_langgraph_time > 0 and avg_pydantic_time > 0:
        speed_improvement = ((avg_langgraph_time - avg_pydantic_time) / avg_langgraph_time) * 100
        print(f"📈 Speed improvement: {speed_improvement:.1f}%")

    # Save detailed results
    output_path = Path("portfolio/agent_comparison_results.json")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "summary": {
                    "total_tests": len(TEST_CASES),
                    "successful_tests": len(successful_tests),
                    "pydantic_faster_count": pydantic_faster_count,
                    "correct_routes": correct_routes,
                    "avg_langgraph_time": avg_langgraph_time,
                    "avg_pydantic_time": avg_pydantic_time,
                },
                "detailed_results": results,
            },
            f,
            indent=2,
        )

    print(f"💾 Detailed results saved to: {output_path}")

    # Recommendations
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 60)

    if correct_routes / len(TEST_CASES) > 0.8:
        print("✅ Pydantic-AI routing logic works well")
    else:
        print("⚠️  Consider tuning Pydantic-AI routing logic")

    if pydantic_faster_count / len(successful_tests) > 0.5:
        print("✅ Pydantic-AI shows good performance")
    else:
        print("⚠️  LangGraph may be faster in some cases")

    print("🚀 Pydantic-AI provides:")
    print("   • Better structured output")
    print("   • Type safety and validation")
    print("   • AG-UI compatibility")
    print("   • Cleaner architecture")


if __name__ == "__main__":
    asyncio.run(run_comparison())
