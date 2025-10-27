from __future__ import annotations

import functools

from app.ai_service import AIService


@functools.lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    return AIService()


