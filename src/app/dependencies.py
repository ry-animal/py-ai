from __future__ import annotations

import functools

from app.agent_memory import AgentMemory, InMemoryAgentMemory, RedisAgentMemory
from app.agent_service import AgentService
from app.ai_service import AIService
from app.config import get_settings
from app.document_service import DocumentService
from app.rag_service import RAGService


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


@functools.lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()


@functools.lru_cache(maxsize=1)
def get_document_service() -> DocumentService:
    rag_service = get_rag_service()
    return DocumentService(rag_service=rag_service)


@functools.lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    rag_service = get_rag_service()
    ai_service = get_ai_service()
    memory = get_agent_memory()
    return AgentService(rag=rag_service, ai=ai_service, memory=memory)
