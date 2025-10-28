from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.ai_service import AIService
from app.dependencies import get_ai_service
from app.schemas import ExtractedUser, ExtractUserRequest

ai_router = APIRouter()


@ai_router.post("/extract-user", response_model=ExtractedUser)
async def extract_user(
    payload: ExtractUserRequest,
    ai: Annotated[AIService, Depends(get_ai_service)],
    stream: bool | None = None,
):
    effective_stream = stream is True
    if effective_stream:
        chunks: AsyncIterator[str] = await ai.extract_user(payload.text, stream=True)  # type: ignore[assignment]
        return StreamingResponse(chunks, media_type="text/plain")
    result: ExtractedUser = await ai.extract_user(payload.text, stream=False)  # type: ignore[assignment]
    return result
