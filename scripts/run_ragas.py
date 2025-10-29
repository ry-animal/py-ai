from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, context_recall


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGAS metrics against the API.")
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
    golden = load_golden(Path("tests/golden/golden.json"))
    # Use expected tokens joined as the reference for a toy baseline; answers come from /ask
    records: list[dict[str, Any]] = []
    for case in golden:
        question = case["question"]
        docs = [(d[0], d[1]) for d in case["docs"]]
        reference = ", ".join(case["expected_contains"])  # simplistic reference text

        # reload corpus per case
        resp = requests.post(f"{base_url}/rag/reload", json=docs, timeout=30)
        resp.raise_for_status()

        # ask and collect answer + contexts
        resp = requests.get(f"{base_url}/ask", params={"q": question}, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        answer = payload.get("answer", "")
        contexts = payload.get("contexts", [])

        records.append(
            {
                "question": question,
                "contexts": contexts,
                "answer": answer,
                "ground_truth": reference,
            }
        )

    ds = Dataset.from_list(records)
    result = evaluate(ds, metrics=[answer_relevancy, context_precision, context_recall])
    df = result.to_pandas()
    out = Path("portfolio")
    out.mkdir(exist_ok=True)
    out_path = out / "ragas_report.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
