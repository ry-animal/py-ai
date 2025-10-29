from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import get_settings


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = max(limit, 0)
        self.window = max(window_seconds, 1)
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> tuple[bool, float]:
        if self.limit == 0:
            return True, 0.0
        now = time.monotonic()
        async with self._lock:
            bucket = self._hits[key]
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry_after = self.window - (now - bucket[0])
                return False, max(retry_after, 0.0)
            bucket.append(now)
        return True, 0.0


def _build_rate_limiter() -> RateLimiter:
    settings = get_settings()
    return RateLimiter(settings.rate_limit_requests_per_window, settings.rate_limit_window_seconds)


async def request_size_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    settings = get_settings()
    max_bytes = settings.max_request_body_bytes
    if max_bytes and max_bytes > 0:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."},
            )
    return await call_next(request)


_rate_limiter = _build_rate_limiter()


def refresh_rate_limiter() -> None:
    global _rate_limiter  # noqa: PLW0603
    _rate_limiter = _build_rate_limiter()


async def rate_limit_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    if _rate_limiter.limit == 0:
        return await call_next(request)

    client_host = request.client.host if request.client else "anonymous"
    allowed, retry_after = await _rate_limiter.check(client_host)
    if not allowed:
        headers = {"Retry-After": str(int(retry_after) + 1)} if retry_after else {}
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests", "retry_after": round(retry_after, 2)},
            headers=headers,
        )
    return await call_next(request)
