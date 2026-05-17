from __future__ import annotations

from datetime import datetime

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
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "update_count": entry.update_count,
            "similarity_reliability": entry.similarity_reliability,
            "related_ids": entry.related_ids,
            "markdown_path": entry.markdown_path or "",
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

    def get_entry(self, entry_id: str) -> DebugEntry | None:
        stored = self.store.get_by_id(entry_id)
        if stored is None:
            return None
        return self._entry_from_metadata(entry_id, stored.get("metadata", {}))

    def list_entries(self, category: str | None = None) -> list[DebugEntry]:
        raw = self.store.get_all_with_embeddings()
        ids = raw.get("ids", [])
        metadatas = raw.get("metadatas", [])

        entries: list[DebugEntry] = []
        for index, entry_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            entry = self._entry_from_metadata(entry_id, metadata)
            if category is None or entry.category == category:
                entries.append(entry)

        entries.sort(key=lambda item: item.created_at, reverse=True)
        return entries

    def get_entries_with_embeddings(
        self,
        category: str | None = None,
    ) -> list[tuple[DebugEntry, list[float]]]:
        raw = self.store.get_all_with_embeddings()
        ids = raw.get("ids", [])
        metadatas = raw.get("metadatas", [])
        embeddings = raw.get("embeddings", [])

        results: list[tuple[DebugEntry, list[float]]] = []
        for index, entry_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            embedding = embeddings[index] if index < len(embeddings) else []
            entry = self._entry_from_metadata(entry_id, metadata)
            if category is None or entry.category == category:
                results.append((entry, embedding))

        results.sort(key=lambda item: item[0].created_at, reverse=True)
        return results

    def upsert_entry(self, entry: DebugEntry) -> None:
        self.index_entry(entry)

    def _parse_list(self, value: str | list) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    def _parse_datetime(self, value: str | None) -> datetime:
        if value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.now().astimezone()

    def _parse_int(self, value: str | int | None, default: int = 0) -> int:
        if isinstance(value, int):
            return value
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _parse_float(
        self,
        value: str | float | int | None,
        default: float = 0.0,
    ) -> float:
        if isinstance(value, (float, int)):
            return float(value)
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _entry_from_metadata(self, entry_id: str, metadata: dict) -> DebugEntry:
        return DebugEntry(
            id=entry_id,
            title=metadata.get("title", ""),
            symptoms=self._parse_list(metadata.get("symptoms", "")),
            root_cause=metadata.get("root_cause", ""),
            fix=metadata.get("fix", ""),
            tags=self._parse_list(metadata.get("tags", "")),
            tech_stack=self._parse_list(metadata.get("tech_stack", "")),
            confidence=self._parse_float(metadata.get("confidence"), default=0.0),
            category=metadata.get("category", "uncategorized"),
            created_at=self._parse_datetime(metadata.get("created_at")),
            updated_at=self._parse_datetime(metadata.get("updated_at")),
            update_count=self._parse_int(metadata.get("update_count"), default=0),
            similarity_reliability=self._parse_float(
                metadata.get("similarity_reliability"),
                default=0.0,
            ),
            related_ids=self._parse_list(metadata.get("related_ids", "")),
            markdown_path=metadata.get("markdown_path") or None,
        )
