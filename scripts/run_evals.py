from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run golden-set RAG evaluations against the API.")
    parser.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        help="Base URL for the API (can also be set via API_BASE_URL).",
    )
    return parser.parse_args()


def load_golden(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    golden_path = Path("tests/golden/golden.json")
    data = load_golden(golden_path)
    report_rows: list[dict[str, Any]] = []
    for case in data:
        name = case["name"]
        docs: list[tuple[str, str]] = [(d[0], d[1]) for d in case["docs"]]
        q: str = case["question"]
        expected: list[str] = case["expected_contains"]

        # reload corpus
        resp = requests.post(f"{base_url}/rag/reload", json=docs, timeout=30)
        resp.raise_for_status()

        # ask question
        t0 = time.perf_counter()
        resp = requests.get(f"{base_url}/ask", params={"q": q}, timeout=60)
        dt_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        payload = resp.json()
        answer: str = payload.get("answer", "")

        # simple contains scoring
        hits = sum(1 for token in expected if token.lower() in answer.lower())
        score = hits / max(1, len(expected))

        report_rows.append(
            {
                "name": name,
                "latency_ms": round(dt_ms, 2),
                "hits": hits,
                "out_of": len(expected),
                "score": round(score, 3),
            }
        )

    out = Path("portfolio")
    out.mkdir(exist_ok=True)
    csv_path = out / "eval_report.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "latency_ms", "hits", "out_of", "score"])
        writer.writeheader()
        writer.writerows(report_rows)
    print(f"Wrote {csv_path} with {len(report_rows)} rows.")


if __name__ == "__main__":
    main()
