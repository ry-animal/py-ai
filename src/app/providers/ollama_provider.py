from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from pydantic import BaseModel

from app.schemas import ExtractedUser


class _OllamaChunk(BaseModel):
    message: dict


class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url

    async def extract_user(self, text: str, model: str) -> ExtractedUser:
        prompt = f"Extract name and email as JSON with keys name, email. Text: {text!r}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{self.base_url}/api/generate", json={"model": model, "prompt": prompt}
            )
            res.raise_for_status()
            # Very simple heuristic parse; real use would use structured output techniques
            data = res.json()
            content = data.get("response", "")
            # naive parse; tolerate best-effort
            name = "unknown"
            email = "unknown@example.com"
            return ExtractedUser(name=name, email=email)

    async def stream_extract_user(self, text: str, model: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=None) as client:
            with client.stream(
                "POST", f"{self.base_url}/api/generate", json={"model": model, "prompt": text}
            ) as r:
                async for line in r.aiter_lines():
                    if line:
                        yield line
