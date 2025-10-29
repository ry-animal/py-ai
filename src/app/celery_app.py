from __future__ import annotations

import functools

from celery import Celery

from app.config import get_settings


def _resolve_url(primary: str | None, fallback: str | None, default: str) -> str:
    if primary:
        return primary
    if fallback:
        return fallback
    return default


@functools.lru_cache(maxsize=1)
def get_celery_app() -> Celery:
    settings = get_settings()
    broker_url = _resolve_url(settings.celery_broker_url, settings.redis_url, "memory://")
    backend_url = _resolve_url(
        settings.celery_result_backend, settings.redis_url, "cache+memory://"
    )

    app = Celery(
        "py_ai",
        broker=broker_url,
        backend=backend_url,
        include=["app.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_default_queue=settings.celery_task_default_queue,
        task_track_started=True,
        timezone="UTC",
        enable_utc=True,
    )
    return app
