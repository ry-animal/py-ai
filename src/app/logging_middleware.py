from __future__ import annotations

import logging
import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request

logger = logging.getLogger("app")


async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status": getattr(locals().get("response"), "status_code", None),
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
            },
        )
    response.headers["x-request-id"] = request_id
    return response


