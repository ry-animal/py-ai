from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import chromadb
from chromadb.utils import embedding_functions

from app.config import get_settings


class RAGService:
    def __init__(self) -> None:
        settings = get_settings()
        persist_dir = Path(".rag_store").absolute()
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        model_name = settings.embedding_model
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        self.collection = self.client.get_or_create_collection(name="documents")
        self._embedding_cache: Dict[str, List[float]] = {}

    def ingest(self, docs: Iterable[Tuple[str, str]]) -> int:
        # docs: iterable of (doc_id, text)
        ids: List[str] = []
        texts: List[str] = []
        embeddings: List[List[float]] = []
        for doc_id, text in docs:
            ids.append(doc_id)
            texts.append(text)
            if text in self._embedding_cache:
                embeddings.append(self._embedding_cache[text])
            else:
                # batch later; here we keep per-doc for cache simplicity
                emb = self.embedder([text])[0]
                self._embedding_cache[text] = emb
                embeddings.append(emb)
        if not ids:
            return 0
        self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings)
        return len(ids)

    def retrieve(self, query: str, k: int = 4) -> List[str]:
        results = self.collection.query(query_texts=[query], n_results=k)
        return results.get("documents", [[""]])[0]


