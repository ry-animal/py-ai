from __future__ import annotations

from typing import AsyncIterator, List

import instructor
from openai import AsyncOpenAI

from app.schemas import ExtractedUser


class OpenAIProvider:
    def __init__(self, api_key: str | None) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.client = instructor.patch(self.client)  # enable Pydantic-native responses

    async def extract_user(self, text: str, model: str) -> ExtractedUser:
        resp = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}],
            response_model=ExtractedUser,
            temperature=0,
        )
        return resp

    async def stream_extract_user(self, text: str, model: str) -> AsyncIterator[str]:
        # Fall back to non-structured streaming for simplicity in demo
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": text}],
            stream=True,
            temperature=0,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    async def generate_answer(self, question: str, contexts: List[str], model: str) -> str:
        system = (
            "You are a helpful assistant. Answer the question using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know."
        )
        context_block = "\n\n".join(f"[Context {i+1}]\n{c}" for i, c in enumerate(contexts))
        user = f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:"
        resp = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
        )
        return resp.choices[0].message.content or ""

    async def stream_answer(self, question: str, contexts: List[str], model: str) -> AsyncIterator[str]:
        system = (
            "You are a helpful assistant. Answer the question using ONLY the provided context. "
            "If the answer isn't in the context, say you don't know."
        )
        context_block = "\n\n".join(f"[Context {i+1}]\n{c}" for i, c in enumerate(contexts))
        user = f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:"
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta


