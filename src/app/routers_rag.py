from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.ai_service import AIService
from app.dependencies import get_ai_service
from app.rag_service import RAGService
from app.tasks import reload_rag_task
from app.text_splitter import split_into_chunks

rag_router = APIRouter()
rag = RAGService()


@rag_router.post("/rag/reload")
async def rag_reload(
    docs: list[tuple[str, str]],
    chunk: bool = True,
    background: bool = True,
) -> dict:
    if background:
        docs_payload = [[doc_id, text] for doc_id, text in docs]
        result = reload_rag_task.delay(docs_payload, chunk)
        return {"task_id": result.id}

    to_ingest: list[tuple[str, str]] = []
    if chunk:
        for doc_id, text in docs:
            chunks = split_into_chunks(text)
            for i, ch in enumerate(chunks):
                to_ingest.append(
                    (
                        f"{doc_id}::part{i}",
                        ch,
                        {"source_id": doc_id, "chunk_index": i},
                    )
                )
    else:
        to_ingest = [
            (doc_id, text, {"source_id": doc_id, "chunk_index": 0}) for doc_id, text in docs
        ]
    count = rag.ingest(to_ingest)
    return {"ingested": count}


@rag_router.get("/ask")
async def rag_ask(
    q: str,
    ai: Annotated[AIService, Depends(get_ai_service)],
    stream: bool | None = None,
):
    effective_stream = stream is True
    contexts = rag.retrieve(q)
    if effective_stream:
        chunks = await ai.generate_answer(q, contexts, stream=True)  # type: ignore[assignment]
        return StreamingResponse(chunks, media_type="text/plain")
    answer: str = await ai.generate_answer(q, contexts, stream=False)  # type: ignore[assignment]
    return {"answer": answer, "contexts": contexts}
