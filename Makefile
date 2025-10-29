.PHONY: run test lint format eval setup

API_BASE_URL ?= http://127.0.0.1:8000

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

eval:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_evals.py

ragas:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_ragas.py

weval:
	API_BASE_URL=$(API_BASE_URL) uv run python scripts/run_web_evals.py

agent-eval:
	uv run python scripts/run_agent_evals.py

worker:
	uv run celery -A app.tasks worker --loglevel=info

setup:
	uv sync
	uv run pre-commit install || uvx pre-commit install || true
