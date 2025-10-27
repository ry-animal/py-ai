.PHONY: run test lint format eval setup

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

eval:
	uv run python scripts/run_evals.py

ragas:
	uv run python scripts/run_ragas.py

setup:
	uv sync
	uv run pre-commit install || true


