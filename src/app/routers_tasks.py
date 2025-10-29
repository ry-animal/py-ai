from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.celery_app import get_celery_app
from app.tasks import echo_task

tasks_router = APIRouter()


class EchoTaskRequest(BaseModel):
    text: str


@tasks_router.post("/tasks/echo", status_code=202)
async def enqueue_echo_task(payload: EchoTaskRequest) -> dict[str, str]:
    try:
        result = echo_task.delay(payload.text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Failed to enqueue task: {exc}") from exc
    return {"task_id": result.id}


@tasks_router.get("/tasks/{task_id}")
async def fetch_task(task_id: str) -> dict[str, object | None]:
    app = get_celery_app()
    async_result = AsyncResult(task_id, app=app)
    info = async_result.info if async_result.info else None
    meta: dict[str, str | int] | None = None
    if isinstance(info, dict):
        meta = info
    elif info is not None:
        meta = {"message": str(info)}

    response: dict[str, object | None] = {
        "task_id": task_id,
        "status": async_result.status,
        "result": None,
        "meta": meta,
    }
    if async_result.successful():
        response["result"] = async_result.result
    elif async_result.failed():
        response["result"] = str(async_result.result)
    return response
