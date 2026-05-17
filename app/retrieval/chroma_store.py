from __future__ import annotations

from typing import Any

import chromadb

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(path=str(settings.chroma_persist_path))
        logger.info(f"ChromaDB client initialized at {settings.chroma_persist_path}")
    return _client


class ChromaStore:
    def __init__(self):
        settings = get_settings()
        client = _get_client()
        self.collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        entry_id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        document: str,
    ) -> None:
        # ChromaDB metadata only supports str, int, float, bool
        clean_meta = self._flatten_metadata(metadata)
        self.collection.upsert(
            ids=[entry_id],
            embeddings=[embedding],
            metadatas=[clean_meta],
            documents=[document],
        )
        logger.info(f"Upserted to ChromaDB", extra={"entry_id": entry_id})

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where: dict | None = None,
    ) -> dict:
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["metadatas", "documents", "distances"],
        }
        if where:
            kwargs["where"] = where

        return self.collection.query(**kwargs)

    def get_by_id(self, entry_id: str) -> dict | None:
        result = self.collection.get(
            ids=[entry_id],
            include=["metadatas", "documents", "embeddings"],
        )
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "metadata": result["metadatas"][0] if result["metadatas"] else {},
            "document": result["documents"][0] if result["documents"] else "",
            "embedding": result["embeddings"][0] if result["embeddings"] else [],
        }

    def get_all_ids(self) -> list[str]:
        result = self.collection.get(include=[])
        return result["ids"]

    def get_all_with_embeddings(self) -> dict:
        return self.collection.get(include=["metadatas", "documents", "embeddings"])

    def count(self) -> int:
        return self.collection.count()

    def delete(self, entry_id: str) -> None:
        self.collection.delete(ids=[entry_id])

    def _flatten_metadata(self, metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        """ChromaDB only supports scalar metadata values. Flatten lists to comma-separated strings."""
        flat = {}
        for key, value in metadata.items():
            if isinstance(value, list):
                flat[key] = ",".join(str(v) for v in value)
            elif isinstance(value, (str, int, float, bool)):
                flat[key] = value
            else:
                flat[key] = str(value)
        return flat
