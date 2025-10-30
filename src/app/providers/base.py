from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas import ExtractedUser


class AIProvider(ABC):
    @abstractmethod
    async def extract_user(
        self, text: str, model: str
    ) -> ExtractedUser:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    async def stream_extract_user(
        self, text: str, model: str
    ) -> AsyncIterator[str]:  # SSE text chunks
        raise NotImplementedError
