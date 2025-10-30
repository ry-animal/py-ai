from __future__ import annotations

from app.celery_app import get_celery_app
from app.document_service import DocumentService
from app.rag_service import RAGService
from app.text_splitter import split_into_chunks

celery_app = get_celery_app()


@celery_app.task(name="app.tasks.echo")
def echo_task(text: str) -> str:
    """Simple demo task that uppercases incoming text."""
    return text.upper()


@celery_app.task(bind=True, name="app.tasks.reload_rag")
def reload_rag_task(self, docs: list[list[str]], chunk: bool = True) -> dict[str, int]:
    """Background ingestion of documents into the RAG vector store."""

    rag = RAGService()
    total_docs = len(docs)
    ingested = 0
    to_ingest: list[tuple[str, str, dict[str, object]]] = []

    for index, pair in enumerate(docs):
        if len(pair) != 2:
            continue
        doc_id, text = pair
        if chunk:
            chunks = split_into_chunks(text)
            for part_index, chunk_text in enumerate(chunks):
                to_ingest.append(
                    (
                        f"{doc_id}::part{part_index}",
                        chunk_text,
                        {"source_id": doc_id, "chunk_index": part_index},
                    )
                )
        else:
            to_ingest.append((doc_id, text, {"source_id": doc_id, "chunk_index": 0}))

        ingested_so_far = len(to_ingest)
        if index % 10 == 0:
            self.update_state(
                state="PROGRESS",
                meta={
                    "processed_docs": index + 1,
                    "total_docs": total_docs,
                    "chunks_pending": ingested_so_far,
                },
            )

    if to_ingest:
        ingested = rag.ingest(to_ingest)

    result = {
        "processed_docs": total_docs,
        "ingested_chunks": ingested,
    }
    self.update_state(state="SUCCESS", meta=result)
    return result


@celery_app.task(bind=True, name="app.tasks.process_document")
def process_document_task(self, doc_id: str) -> dict[str, str]:
    """Background task to process an uploaded document."""
    try:
        # Initialize services
        rag_service = RAGService()
        document_service = DocumentService(rag_service=rag_service)

        # Update progress
        self.update_state(
            state="PROGRESS", meta={"message": "Starting document processing", "progress": 10}
        )

        # Process the document (note: calling sync version since Celery tasks are sync)
        import asyncio

        document = asyncio.run(document_service.process_document(doc_id))

        # Update progress
        self.update_state(
            state="PROGRESS", meta={"message": "Document processing completed", "progress": 100}
        )

        result = {
            "document_id": doc_id,
            "status": document.status.value,
            "message": "Document processed successfully",
        }

        self.update_state(state="SUCCESS", meta=result)
        return result

    except Exception as e:
        error_msg = f"Failed to process document {doc_id}: {str(e)}"
        self.update_state(state="FAILURE", meta={"error": error_msg, "document_id": doc_id})
        raise Exception(error_msg)
