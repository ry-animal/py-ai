from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import router
from .routers_ai import ai_router
from .routers_rag import rag_router
from .config import get_settings
from .logging_middleware import request_id_middleware

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Python AI Learning API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    return app


app = create_app()


