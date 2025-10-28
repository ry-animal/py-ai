# py-ai

FastAPI-based AI backend with RAG, structured extraction, and a minimal agent with web search.

## Features
- FastAPI app with health/ready endpoints and request ID logging
- Structured extraction via OpenAI + Instructor (Claude fallback)
- RAG with Chroma + sentence-transformers (`all-MiniLM-L6-v2`), chunking + cache
- Agent endpoint that routes between RAG and Tavily web search (JSON fallback)
- Streaming support for AI answers
- Evaluation harnesses (simple and RAGAS)

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
```
4) Run
```bash
make run        # http://127.0.0.1:8000/docs
```

## Endpoints
- Health
  - GET `/health`, GET `/ready`
- Structured extraction
  - POST `/extract-user` body: `{ "text": "Jane <jane@example.com>" }`
- RAG
  - POST `/rag/reload` body: `[["id","text"], ...]` (chunking on by default)
  - GET `/ask?q=...&stream=true|false`
- Agent
  - GET `/agent/chat?q=...&stream=true|false`
  - GET `/agent/debug/web?q=...` (raw Tavily contexts + direct answer)

## Examples (cURL)
```bash
# RAG load + ask
curl -s -X POST 'http://127.0.0.1:8000/rag/reload' \
  -H 'Content-Type: application/json' \
  -d '[["1","FastAPI is a modern, fast web framework for building APIs."]]'

curl -s -N 'http://127.0.0.1:8000/ask?q=What%20is%20FastAPI%3F&stream=true'

# Agent web (JSON)
curl -s 'http://127.0.0.1:8000/agent/chat?q=web%3A%20FastAPI%20latest%20release%20notes'
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
```

## Notes
- Local vector DB is stored in `.rag_store/` (ignored).
- Streaming returns text/plain; non-stream returns JSON with `answer` and/or `contexts`.
