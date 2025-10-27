from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.dependencies import get_ai_service
from app.schemas import ExtractUserRequest, ExtractedUser


ai_router = APIRouter()


@ai_router.post("/extract-user", response_model=ExtractedUser)
async def extract_user(
    payload: ExtractUserRequest,
    stream: bool | None = None,
    ai=Depends(get_ai_service),
):
    settings = get_settings()
    effective_stream = stream if stream is not None else settings.streaming_enabled
    if effective_stream:
        chunks: AsyncIterator[str] = await ai.extract_user(payload.text, stream=True)  # type: ignore[assignment]
        return StreamingResponse(chunks, media_type="text/plain")
    else:
        result: ExtractedUser = await ai.extract_user(payload.text, stream=False)  # type: ignore[assignment]
        return result


