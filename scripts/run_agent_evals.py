from __future__ import annotations

import asyncio
import csv
import json
import time
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from pathlib import Path

from app.agent_memory import InMemoryAgentMemory
from app.agent_service import AgentService
from app.rag_service import RAGService
from app.text_splitter import split_into_chunks

DATA_PATH = Path("tests/golden/agent_golden.json")
REPORT_PATH = Path("portfolio/agent_eval_report.csv")
PORTFOLIO_DIR = REPORT_PATH.parent


@dataclass
class AgentCase:
    name: str
    question: str
    preferred_route: str
    docs: list[str]
    web_snippets: list[str]
    web_direct_answer: str | None
    expected_contains: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> AgentCase:
        return cls(
            name=str(raw["name"]),
            question=str(raw["question"]),
            preferred_route=str(raw["preferred_route"]).lower(),
            docs=[str(item) for item in raw.get("docs", [])],
            web_snippets=[str(item) for item in raw.get("web_snippets", [])],
            web_direct_answer=(
                str(raw["web_direct_answer"]) if raw.get("web_direct_answer") is not None else None
            ),
            expected_contains=[str(item) for item in raw.get("expected_contains", [])],
        )


class FakeWeb:
    def __init__(self, snippets: Iterable[str], direct: str | None) -> None:
        cleaned = [text for text in snippets if text]
        self._snippets = cleaned or ["[web harness] no snippets provided"]
        self._direct = direct

    async def search_with_answer(self, query: str) -> tuple[list[str], str | None]:  # noqa: ARG002
        return list(self._snippets), self._direct


class FakeAIService:
    async def generate_answer(
        self, question: str, contexts: list[str], stream: bool = False
    ) -> str | AsyncIterator[str]:
        answer_text = " ".join(contexts).strip()
        if not contexts:
            answer_text = "I don't know"

        if not stream:
            return answer_text

        async def gen() -> AsyncIterator[str]:
            yield answer_text

        return gen()


def _ingest_docs_into_rag(rag: RAGService, case: AgentCase) -> None:
    if not case.docs:
        return
    payload = []
    for idx, text in enumerate(case.docs):
        base_id = f"{case.name}::doc{idx}"
        chunks = split_into_chunks(text)
        for chunk_index, chunk_text in enumerate(chunks):
            payload.append(
                (
                    f"{base_id}::part{chunk_index}",
                    chunk_text,
                    {"source_id": case.name, "chunk_index": chunk_index, "doc_index": idx},
                )
            )
    rag.ingest(payload)


async def run_case(case: AgentCase) -> dict[str, object]:
    rag = RAGService(persist_path=None)
    _ingest_docs_into_rag(rag, case)
    web = (
        FakeWeb(case.web_snippets, case.web_direct_answer)
        if case.preferred_route == "web"
        else None
    )
    ai = FakeAIService()
    memory = InMemoryAgentMemory(max_turns=3)
    agent = AgentService(rag=rag, ai=ai, web=web, memory=memory)

    start = time.perf_counter()
    stream = await agent.answer(case.question, stream=True, session=case.name)

    breadcrumbs: list[str] = []
    answer_parts: list[str] = []
    async for chunk in stream:  # type: ignore[assignment]
        for line in chunk.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("["):
                breadcrumbs.append(stripped)
            else:
                answer_parts.append(stripped)
    duration_ms = (time.perf_counter() - start) * 1000

    route_line = next((line for line in breadcrumbs if line.startswith("[route]")), "")
    observed_route = "unknown"
    if route_line:
        tokens = route_line.split()
        if len(tokens) > 1:
            observed_route = tokens[1].lower()

    answer_text = " ".join(answer_parts).strip()
    score = contains_score(answer_text, case.expected_contains)

    contexts_meta = []
    if observed_route == "rag":
        retrieved = rag.retrieve(case.question, include_metadata=True)
        contexts_meta = [meta for _, meta in retrieved]

    return {
        "name": case.name,
        "question": case.question,
        "preferred_route": case.preferred_route,
        "observed_route": observed_route,
        "route_match": "yes" if observed_route == case.preferred_route else "no",
        "latency_ms": f"{duration_ms:.2f}",
        "contains_score": f"{score:.2f}",
        "answer_excerpt": answer_text[:160],
        "contexts_used": " | ".join(
            f"{meta.get('source_id', '?')}::part{meta.get('chunk_index', 0)}"
            for meta in contexts_meta
        ),
    }


def contains_score(answer: str, expected_tokens: list[str]) -> float:
    if not expected_tokens:
        return 1.0
    normalized_answer = answer.lower()
    hits = sum(1 for token in expected_tokens if token.lower() in normalized_answer)
    return hits / len(expected_tokens)


async def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Golden file not found: {DATA_PATH}")

    data = json.loads(DATA_PATH.read_text())
    cases = [AgentCase.from_dict(item) for item in data]

    results: list[dict[str, object]] = []
    for case in cases:
        result = await run_case(case)
        results.append(result)

    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", newline="") as csvfile:
        fieldnames = [
            "name",
            "question",
            "preferred_route",
            "observed_route",
            "route_match",
            "latency_ms",
            "contains_score",
            "answer_excerpt",
            "contexts_used",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    route_accuracy = sum(1 for item in results if item["route_match"] == "yes") / len(results)
    avg_score = sum(float(item["contains_score"]) for item in results) / len(results)

    print("Agent eval complete")
    print(f"  Cases: {len(results)}")
    print(f"  Route accuracy: {route_accuracy:.2%}")
    print(f"  Mean contains score: {avg_score:.2f}")
    print(f"  Report → {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
