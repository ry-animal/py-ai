from __future__ import annotations

from typing import AsyncIterator, List

from anthropic import AsyncAnthropic

from app.schemas import ExtractedUser


class AnthropicProvider:
    def __init__(self, api_key: str | None) -> None:
        self.client = AsyncAnthropic(api_key=api_key)

    async def extract_user(self, text: str, model: str) -> ExtractedUser:
        prompt = (
            "Extract a user's name and email from the following text and return valid JSON with "
            "keys: name, email. If missing, infer best effort. Text: " + text
        )
        resp = await self.client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0,
        )
        content = "".join(
            part.text for part in resp.content if hasattr(part, "text") and part.text is not None
        )
        # Very naive parse to keep demo simple
        name = "unknown"
        email = "unknown@example.com"
        return ExtractedUser(name=name, email=email)

    async def stream_extract_user(self, text: str, model: str) -> AsyncIterator[str]:
        stream = await self.client.messages.stream(
            model=model,
            messages=[{"role": "user", "content": text}],
            max_tokens=256,
            temperature=0,
        )
        async with stream as s:
            async for event in s:
                if hasattr(event, "delta") and getattr(event.delta, "text", None):
                    yield event.delta.text

    async def generate_answer(self, question: str, contexts: List[str], model: str) -> str:
        system = (
            "You are a helpful assistant. Answer the question using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know."
        )
        context_block = "\n\n".join(f"[Context {i+1}]\n{c}" for i, c in enumerate(contexts))
        user = f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:"
        resp = await self.client.messages.create(
            model=model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=512,
            temperature=0,
        )
        text = "".join(
            part.text for part in resp.content if hasattr(part, "text") and part.text is not None
        )
        return text

    async def stream_answer(self, question: str, contexts: List[str], model: str) -> AsyncIterator[str]:
        system = (
            "You are a helpful assistant. Answer the question using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know."
        )
        context_block = "\n\n".join(f"[Context {i+1}]\n{c}" for i, c in enumerate(contexts))
        user = f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:"
        stream = await self.client.messages.stream(
            model=model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=512,
            temperature=0,
        )
        async with stream as s:
            async for event in s:
                if hasattr(event, "delta") and getattr(event.delta, "text", None):
                    yield event.delta.text


