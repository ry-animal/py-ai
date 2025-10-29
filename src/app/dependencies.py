from __future__ import annotations

import functools

from app.agent_memory import AgentMemory, InMemoryAgentMemory, RedisAgentMemory
from app.ai_service import AIService
from app.config import get_settings


@functools.lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    return AIService()


@functools.lru_cache(maxsize=1)
def get_agent_memory() -> AgentMemory:
    settings = get_settings()
    if settings.redis_url:
        return RedisAgentMemory(
            settings.redis_url,
            max_turns=settings.agent_memory_max_turns,
            ttl_seconds=settings.agent_memory_ttl_seconds,
        )
    return InMemoryAgentMemory(max_turns=settings.agent_memory_max_turns)
