from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .logging_middleware import request_id_middleware
from .middleware_guardrails import (
    rate_limit_middleware,
    refresh_rate_limiter,
    request_size_middleware,
)
from .routers import router
from .routers_agent import agent_router
from .routers_ai import ai_router
from .routers_chat import router as chat_router
from .routers_docs import router as docs_router
from .routers_rag import rag_router
from .routers_tasks import tasks_router
from .telemetry import instrument_app, setup_telemetry


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Python AI Learning API", version="0.1.0")
    refresh_rate_limiter()

    # Setup OpenTelemetry
    setup_telemetry("py-ai")
    instrument_app(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(request_size_middleware)
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(request_id_middleware)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    app.include_router(router)
    app.include_router(ai_router)
    app.include_router(rag_router)
    app.include_router(agent_router)
    app.include_router(tasks_router)
    app.include_router(docs_router)
    app.include_router(chat_router)

    return app


app = create_app()
