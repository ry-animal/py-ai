from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

from app.config import get_settings
from app.text_splitter import split_into_chunks


class RAGService:
    def __init__(self, persist_path: str | None = ".rag_store") -> None:
        settings = get_settings()
        if persist_path is None:
            self.client = chromadb.EphemeralClient()
        else:
            persist_dir = Path(persist_path).absolute()
            persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(persist_dir))
        model_name = settings.embedding_model
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        self.collection = self.client.get_or_create_collection(name="documents")
        self._embedding_cache: dict[str, list[float]] = {}

    def ingest(self, docs: Iterable[tuple[str, str] | tuple[str, str, dict[str, Any]]]) -> int:
        ids: list[str] = []
        texts: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, Any]] = []
        for item in docs:
            if len(item) == 3:
                doc_id, text, metadata = item  # type: ignore[misc]
            else:
                doc_id, text = item  # type: ignore[misc]
                metadata = {"source_id": doc_id, "chunk_index": 0}
            ids.append(doc_id)
            texts.append(text)
            metadatas.append(metadata)
            if text in self._embedding_cache:
                embeddings.append(self._embedding_cache[text])
            else:
                emb = self.embedder([text])[0]
                self._embedding_cache[text] = emb
                embeddings.append(emb)
        if not ids:
            return 0
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(ids)

    def retrieve(self, query: str, k: int = 4, include_metadata: bool = False):
        results = self.collection.query(query_texts=[query], n_results=k)
        documents = results.get("documents", [[""]])[0]
        if not include_metadata:
            return documents
        metadatas = results.get("metadatas", [[{}]])[0]
        combined: list[tuple[str, dict[str, Any]]] = []
        for doc, meta in zip(documents, metadatas, strict=False):
            combined.append((doc, meta or {}))
        return combined

    async def ingest_document(self, doc_id: str, text: str, metadata: dict[str, Any]) -> int:
        """Ingest a document with chunking and metadata."""
        # Split document into chunks
        chunks = split_into_chunks(text)

        docs_to_ingest = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}::part{i}"
            chunk_metadata = {
                **metadata,
                "document_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            docs_to_ingest.append((chunk_id, chunk, chunk_metadata))

        return self.ingest(docs_to_ingest)

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks for a document."""
        # Get all documents to find matching chunks
        all_docs = self.collection.get()
        doc_ids_to_delete = [
            doc_id for doc_id in all_docs.get("ids", []) if doc_id.startswith(f"{doc_id}::")
        ]

        if doc_ids_to_delete:
            self.collection.delete(ids=doc_ids_to_delete)

    def retrieve_with_sources(self, query: str, k: int = 4):
        """Retrieve documents with source metadata for citations."""
        results = self.collection.query(
            query_texts=[query], n_results=k, include=["documents", "metadatas", "distances"]
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        enriched_results = []
        for doc, meta, distance in zip(documents, metadatas, distances, strict=False):
            enriched_results.append(
                {
                    "content": doc,
                    "metadata": meta or {},
                    "relevance_score": 1 - distance,  # Convert distance to relevance
                    "source": meta.get("filename", "Unknown") if meta else "Unknown",
                    "document_id": meta.get("document_id") if meta else None,
                }
            )

        return enriched_results
