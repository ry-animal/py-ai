from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request

logger = logging.getLogger("app")


async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": 500,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
                "client_ip": request.client.host if request.client else None,
            },
        )
        raise
    finally:
        status_code = response.status_code if response is not None else 500
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
                "client_ip": request.client.host if request.client else None,
                "content_length": request.headers.get("content-length"),
            },
        )
    if response is not None:
        response.headers["x-request-id"] = request_id
    return response
