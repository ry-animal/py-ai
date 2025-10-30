from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable

from app.config import get_settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.openai_provider import OpenAIProvider
from app.schemas import ExtractedUser


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self.provider_name = settings.model_provider
        self.openai_model = settings.model_name
        self.claude_model = settings.claude_model
        self.default_streaming = settings.streaming_enabled
        self.has_openai = bool(settings.openai_api_key)
        self.has_anthropic = bool(settings.anthropic_api_key)
        self.openai = OpenAIProvider(settings.openai_api_key) if self.has_openai else None
        self.anthropic = (
            AnthropicProvider(settings.anthropic_api_key) if self.has_anthropic else None
        )

    async def _retry(self, func: Callable[[], Awaitable], attempts: int = 2, delay_s: float = 0.5):
        last_exc: Exception | None = None
        for i in range(attempts):
            try:
                return await func()
            except Exception as exc:  # noqa: BLE001 - surface upstream
                last_exc = exc
                await asyncio.sleep(delay_s * (2**i))
        if last_exc is None:
            msg = "No exception captured during retry"
            raise RuntimeError(msg)
        raise last_exc

    async def extract_user(
        self, text: str, stream: bool = False
    ) -> ExtractedUser | AsyncIterator[str]:
        # Choose primary based on available keys: prefer OpenAI when configured, else Claude
        if self.has_openai and self.openai is not None:

            async def do_openai():
                return await self.openai.extract_user(text, self.openai_model)

            async def do_openai_stream():
                async for chunk in self.openai.stream_extract_user(text, self.openai_model):
                    yield chunk

            try:
                if stream:
                    return do_openai_stream()
                return await self._retry(do_openai)
            except Exception:
                if self.has_anthropic and self.anthropic is not None:
                    if stream:
                        return self.anthropic.stream_extract_user(text, self.claude_model)
                    return await self._retry(
                        lambda: self.anthropic.extract_user(text, self.claude_model)
                    )
                raise

        if self.has_anthropic and self.anthropic is not None:
            if stream:
                return self.anthropic.stream_extract_user(text, self.claude_model)
            return await self._retry(lambda: self.anthropic.extract_user(text, self.claude_model))

        raise RuntimeError("No AI provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

    async def generate_answer(
        self, question: str, contexts: list[str], stream: bool = False
    ) -> str | AsyncIterator[str]:
        if self.has_openai and self.openai is not None:
            try:
                if stream:
                    return self.openai.stream_answer(question, contexts, self.openai_model)
                return await self.openai.generate_answer(question, contexts, self.openai_model)
            except Exception:
                if self.has_anthropic and self.anthropic is not None:
                    if stream:
                        return self.anthropic.stream_answer(question, contexts, self.claude_model)
                    return await self.anthropic.generate_answer(
                        question, contexts, self.claude_model
                    )
                raise
        if self.has_anthropic and self.anthropic is not None:
            if stream:
                return self.anthropic.stream_answer(question, contexts, self.claude_model)
            return await self.anthropic.generate_answer(question, contexts, self.claude_model)
        raise RuntimeError("No AI provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
