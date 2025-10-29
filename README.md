# py-ai

FastAPI-based AI backend with RAG, structured extraction, and a minimal agent with web search.

## Features
- FastAPI app with health/ready endpoints, structured request logging, and guardrails (size limits + per-client rate limiting)
- Structured extraction via OpenAI + Instructor (Claude fallback)
- RAG with Chroma + sentence-transformers (`all-MiniLM-L6-v2`), chunking + cache
- Agent endpoint that routes between RAG and Tavily web search (JSON fallback)
- Streaming support for AI answers
- Celery-backed background jobs (`/rag/reload` queues ingestion by default)
- Evaluation harnesses (simple, web, agent blended, and RAGAS)

## Quickstart
1) Prereqs: Python 3.11+, `uv` installed
2) Install
```bash
make setup   # uv sync + pre-commit hooks
```
3) Environment (.env)
```ini
ANTHROPIC_API_KEY=...
# Optional
OPENAI_API_KEY=...
TAVILY_API_KEY=...
STREAMING_ENABLED=true
MODEL_NAME=gpt-4o-mini
CLAUDE_MODEL=claude-3-5-sonnet-latest
embedding_model=all-MiniLM-L6-v2
MAX_WEB_RESULTS=10
TAVILY_SEARCH_DEPTH=advanced
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_TASK_DEFAULT_QUEUE=default
MAX_REQUEST_BODY_BYTES=2000000
RATE_LIMIT_REQUESTS_PER_WINDOW=120
RATE_LIMIT_WINDOW_SECONDS=60
```
4) Run
```bash
make run        # http://127.0.0.1:8000/docs (binds 0.0.0.0)
make worker     # start Celery worker (requires Redis)
```

## Endpoints
- Health
  - GET `/health`, GET `/ready`
- Structured extraction
  - POST `/extract-user` body: `{ "text": "Jane <jane@example.com>" }`
- RAG
  - POST `/rag/reload` body: `[["id","text"], ...]` (chunking on by default, queues Celery unless `background=false`)
  - GET `/ask?q=...&stream=true|false`
- Agent
  - GET `/agent/chat?q=...&stream=true|false`
  - GET `/agent/debug/web?q=...` (raw Tavily contexts + direct answer)
- Tasks
  - POST `/tasks/echo` body: `{ "text": "hello" }`
  - GET `/tasks/{task_id}` → status/progress/result

## Examples (cURL)
```bash
# RAG load + ask
curl -s -X POST 'http://127.0.0.1:8000/rag/reload' \
  -H 'Content-Type: application/json' \
  -d '[["1","FastAPI is a modern, fast web framework for building APIs."]]'

curl -s -N 'http://127.0.0.1:8000/ask?q=What%20is%20FastAPI%3F&stream=true'

# Agent web (JSON)
curl -s 'http://127.0.0.1:8000/agent/chat?q=web%3A%20FastAPI%20latest%20release%20notes'

# Background reload + status
curl -s -X POST 'http://127.0.0.1:8000/rag/reload' \
  -H 'Content-Type: application/json' \
  -d '[["batch1","Document text..."]]' \
  | jq

curl -s 'http://127.0.0.1:8000/tasks/<task_id>' | jq
```

## Dev commands
```bash
make run       # start API
make test      # run tests
make lint      # ruff check
make format    # ruff format
make eval      # RAG simple eval → portfolio/eval_report.csv
make weval     # Web agent eval → portfolio/web_eval_report.csv
make ragas     # RAGAS metrics → portfolio/ragas_report.csv
make agent-eval # Blended agent eval → portfolio/agent_eval_report.csv
make worker    # Celery worker (background jobs)
```

Set `API_BASE_URL` when running against Docker compose (e.g. `make eval API_BASE_URL=http://127.0.0.1:8010`).

## Docker / Compose
```bash
# Build runtime image
docker build -t py-ai:latest .

# Or run API + worker + redis together (API on http://127.0.0.1:8010)
docker compose up --build
```

## Notes
- Local vector DB is stored in `.rag_store/` (ignored).
- Streaming returns text/plain; non-stream returns JSON with `answer` and/or `contexts`.
- Request guardrails: requests larger than `MAX_REQUEST_BODY_BYTES` receive HTTP 413; exceeding the per-client rate limit yields HTTP 429 with a `Retry-After` header.
