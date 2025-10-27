from __future__ import annotations

from typing import List, Tuple

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.rag_service import RAGService
from app.text_splitter import split_into_chunks
from app.dependencies import get_ai_service
from app.config import get_settings


rag_router = APIRouter()
rag = RAGService()


@rag_router.post("/rag/reload")
async def rag_reload(docs: List[Tuple[str, str]], chunk: bool = True) -> dict:
    to_ingest: List[Tuple[str, str]] = []
    if chunk:
        for doc_id, text in docs:
            chunks = split_into_chunks(text)
            for i, ch in enumerate(chunks):
                to_ingest.append((f"{doc_id}::part{i}", ch))
    else:
        to_ingest = docs
    count = rag.ingest(to_ingest)
    return {"ingested": count}


@rag_router.get("/ask")
async def rag_ask(q: str, stream: bool | None = None, ai=Depends(get_ai_service)):
    settings = get_settings()
    effective_stream = stream if stream is not None else settings.streaming_enabled
    contexts = rag.retrieve(q)
    if effective_stream:
        chunks = await ai.generate_answer(q, contexts, stream=True)  # type: ignore[assignment]
        return StreamingResponse(chunks, media_type="text/plain")
    answer: str = await ai.generate_answer(q, contexts, stream=False)  # type: ignore[assignment]
    return {"answer": answer, "contexts": contexts}


