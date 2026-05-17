from __future__ import annotations

from app.embeddings.service import EmbeddingService
from app.retrieval.chroma_store import ChromaStore
from app.models.debug_entry import DebugEntry, SimilarEntry
from app.models.query import QueryResult
from app.utils.text_processing import build_embedding_document
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self):
        self.store = ChromaStore()
        self.embedding_service = EmbeddingService()

    def index_entry(self, entry: DebugEntry) -> None:
        """Generate embedding and store entry in ChromaDB."""
        embedding = self.embedding_service.generate(
            title=entry.title,
            root_cause=entry.root_cause,
            fix=entry.fix,
            symptoms=entry.symptoms,
            tags=entry.tags,
        )

        document = build_embedding_document(
            entry.title, entry.root_cause, entry.fix, entry.symptoms, entry.tags,
        )

        metadata = {
            "title": entry.title,
            "root_cause": entry.root_cause,
            "fix": entry.fix,
            "symptoms": entry.symptoms,
            "tags": entry.tags,
            "tech_stack": entry.tech_stack,
            "category": entry.category,
            "confidence": entry.confidence,
        }

        self.store.upsert(
            entry_id=entry.id,
            embedding=embedding,
            metadata=metadata,
            document=document,
        )

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        where: dict | None = None,
    ) -> list[QueryResult]:
        query_embedding = self.embedding_service.generate_query_embedding(query)
        raw = self.store.query(query_embedding, top_k=top_k, where=where)

        if not raw["ids"] or not raw["ids"][0]:
            return []

        results = []
        for i, entry_id in enumerate(raw["ids"][0]):
            meta = raw["metadatas"][0][i] if raw["metadatas"] else {}
            distance = raw["distances"][0][i] if raw["distances"] else 1.0
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            similarity = max(0.0, 1.0 - distance)

            results.append(QueryResult(
                id=entry_id,
                title=meta.get("title", ""),
                symptoms=self._parse_list(meta.get("symptoms", "")),
                root_cause=meta.get("root_cause", ""),
                fix=meta.get("fix", ""),
                tags=self._parse_list(meta.get("tags", "")),
                tech_stack=self._parse_list(meta.get("tech_stack", "")),
                confidence=meta.get("confidence", 0.0),
                similarity_score=round(similarity, 4),
                related_ids=[],
            ))

        return results

    def find_similar(self, entry_id: str, top_k: int = 5) -> list[SimilarEntry]:
        """Find entries similar to a given entry by its ID."""
        stored = self.store.get_by_id(entry_id)
        if stored is None or stored.get("embedding") is None or len(stored["embedding"]) == 0:
            return []

        raw = self.store.query(stored["embedding"], top_k=top_k + 1)

        if not raw["ids"] or not raw["ids"][0]:
            return []

        results = []
        for i, rid in enumerate(raw["ids"][0]):
            if rid == entry_id:
                continue
            meta = raw["metadatas"][0][i] if raw["metadatas"] else {}
            distance = raw["distances"][0][i] if raw["distances"] else 1.0
            similarity = max(0.0, 1.0 - distance)

            results.append(SimilarEntry(
                id=rid,
                title=meta.get("title", ""),
                root_cause=meta.get("root_cause", ""),
                fix=meta.get("fix", ""),
                similarity_score=round(similarity, 4),
                tags=self._parse_list(meta.get("tags", "")),
            ))

        return results[:top_k]

    def _parse_list(self, value: str | list) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]
