from __future__ import annotations

import json
from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

MessageFactories = {
    "human": HumanMessage,
    "ai": AIMessage,
    "assistant": AIMessage,
    "system": SystemMessage,
}


class AgentMemory(Protocol):
    async def read(self, session_id: str) -> list[BaseMessage]:
        """Return the stored messages for a session (oldest → newest)."""

    async def append(self, session_id: str, messages: Iterable[BaseMessage]) -> None:
        """Persist new messages, trimming to the configured window."""

    async def clear(self, session_id: str) -> None:
        """Clear stored messages for a session."""


def _message_to_dict(message: BaseMessage) -> dict[str, str]:
    return {
        "type": getattr(message, "type", "human"),
        "content": message.content if isinstance(message.content, str) else str(message.content),
    }


def _message_from_dict(payload: dict[str, str]) -> BaseMessage:
    msg_type = payload.get("type", "human").lower()
    content = payload.get("content", "")
    factory = MessageFactories.get(msg_type, AIMessage)
    return factory(content=content)


class InMemoryAgentMemory:
    """Simple deque-backed memory for local development and tests."""

    def __init__(self, max_turns: int = 3) -> None:
        self._store: defaultdict[str, deque[BaseMessage]] = defaultdict(
            lambda: deque(maxlen=max(1, max_turns * 2))
        )

    async def read(self, session_id: str) -> list[BaseMessage]:
        return list(self._store[session_id])

    async def append(self, session_id: str, messages: Iterable[BaseMessage]) -> None:
        record = self._store[session_id]
        for message in messages:
            record.append(message)

    async def clear(self, session_id: str) -> None:
        if session_id in self._store:
            del self._store[session_id]


class RedisAgentMemory:
    """Redis-backed agent memory with TTL-based eviction."""

    def __init__(
        self,
        url: str,
        *,
        max_turns: int = 3,
        ttl_seconds: int | None = 86_400,
        prefix: str = "agent:session",
    ) -> None:
        try:
            from redis import asyncio as redis_async
        except ImportError as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "RedisAgentMemory requires the 'redis' package. Install with "
                "'pip install redis>=5'."
            ) from exc

        self._client = redis_async.from_url(url, encoding="utf-8", decode_responses=True)
        self._max_messages = max(1, max_turns * 2)
        self._ttl_seconds = ttl_seconds
        self._prefix = prefix.rstrip(":")

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}:{session_id}"

    async def read(self, session_id: str) -> list[BaseMessage]:
        raw = await self._client.get(self._key(session_id))
        if not raw:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await self.clear(session_id)
            return []
        return [_message_from_dict(item) for item in data if isinstance(item, dict)]

    async def append(self, session_id: str, messages: Iterable[BaseMessage]) -> None:
        stored = await self.read(session_id)
        stored.extend(messages)
        trimmed = stored[-self._max_messages :]
        payload = json.dumps([_message_to_dict(msg) for msg in trimmed])
        if self._ttl_seconds is None:
            await self._client.set(self._key(session_id), payload)
        else:
            await self._client.set(self._key(session_id), payload, ex=self._ttl_seconds)

    async def clear(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    async def aclose(self) -> None:
        await self._client.aclose()
