from __future__ import annotations

import re
from datetime import datetime

from app.config import get_settings
from app.embeddings.service import EmbeddingService
from app.retrieval.chroma_store import ChromaStore
from app.models.debug_entry import DebugEntry, DuplicateCandidate, SimilarEntry
from app.models.query import QueryResult
from app.utils.text_processing import build_embedding_document
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self):
        self.settings = get_settings()
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

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        tags: list[str] | None = None,
        tech_stack: list[str] | None = None,
        where: dict | None = None,
    ) -> list[QueryResult]:
        semantic_results = self.semantic_search(
            query=query,
            top_k=max(top_k * 3, top_k),
            where=where,
        )
        all_entries = self.list_entries()
        query_terms = self._tokenize(query)

        scored: dict[str, tuple[QueryResult, float]] = {}

        for result in semantic_results:
            if not self._matches_filters(result, tags=tags, tech_stack=tech_stack):
                continue
            lexical_score = self._lexical_score_for_result(result, query_terms)
            hybrid_score = self._combine_scores(
                semantic_score=result.similarity_score,
                lexical_score=lexical_score,
                graph_boost=self._graph_boost(result),
            )
            scored[result.id] = (self._clone_result(result, hybrid_score), hybrid_score)

        for entry in all_entries:
            candidate = self._query_result_from_entry(entry)
            if not self._matches_filters(candidate, tags=tags, tech_stack=tech_stack):
                continue
            lexical_score = self._lexical_score_for_result(candidate, query_terms)
            if lexical_score <= 0.0:
                continue
            hybrid_score = self._combine_scores(
                semantic_score=0.0,
                lexical_score=lexical_score,
                graph_boost=self._graph_boost(candidate),
            )
            existing = scored.get(candidate.id)
            if existing is None or hybrid_score > existing[1]:
                scored[candidate.id] = (self._clone_result(candidate, hybrid_score), hybrid_score)

        ranked = sorted(scored.values(), key=lambda item: item[1], reverse=True)
        return [result for result, _ in ranked[:top_k]]

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

    def find_duplicate_candidate(
        self,
        *,
        title: str,
        root_cause: str,
        fix: str,
        symptoms: list[str],
        tags: list[str],
        tech_stack: list[str] | None = None,
    ) -> DuplicateCandidate | None:
        if self.store.count() == 0:
            return None

        query_embedding = self.embedding_service.generate(
            title=title,
            root_cause=root_cause,
            fix=fix,
            symptoms=symptoms,
            tags=tags,
        )
        raw = self.store.query(query_embedding, top_k=1)
        if not raw["ids"] or not raw["ids"][0]:
            return None

        meta = raw["metadatas"][0][0] if raw["metadatas"] else {}
        distance = raw["distances"][0][0] if raw["distances"] else 1.0
        similarity = max(0.0, 1.0 - distance)
        if similarity < self.settings.deduplication_threshold:
            return None

        candidate = DuplicateCandidate(
            id=raw["ids"][0][0],
            title=meta.get("title", ""),
            root_cause=meta.get("root_cause", ""),
            fix=meta.get("fix", ""),
            similarity_score=round(similarity, 4),
            tags=self._parse_list(meta.get("tags", "")),
            tech_stack=self._parse_list(meta.get("tech_stack", "")),
        )

        if self._is_same_entry(candidate, title, root_cause, tech_stack or []):
            return candidate
        return None

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

    def _query_result_from_entry(self, entry: DebugEntry) -> QueryResult:
        return QueryResult(
            id=entry.id,
            title=entry.title,
            symptoms=entry.symptoms,
            root_cause=entry.root_cause,
            fix=entry.fix,
            tags=entry.tags,
            tech_stack=entry.tech_stack,
            confidence=entry.confidence,
            similarity_score=0.0,
            related_ids=entry.related_ids,
        )

    def _clone_result(self, result: QueryResult, score: float) -> QueryResult:
        return QueryResult(
            id=result.id,
            title=result.title,
            symptoms=result.symptoms,
            root_cause=result.root_cause,
            fix=result.fix,
            tags=result.tags,
            tech_stack=result.tech_stack,
            confidence=result.confidence,
            similarity_score=round(score, 4),
            related_ids=result.related_ids,
        )

    def _matches_filters(
        self,
        result: QueryResult,
        *,
        tags: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> bool:
        if tags and not (set(result.tags) & {item.lower().strip() for item in tags}):
            return False
        if tech_stack and not (set(result.tech_stack) & {item.lower().strip() for item in tech_stack}):
            return False
        return True

    def _lexical_score_for_result(self, result: QueryResult, query_terms: set[str]) -> float:
        if not query_terms:
            return 0.0
        haystack = " ".join(
            [
                result.title,
                result.root_cause,
                result.fix,
                " ".join(result.symptoms),
                " ".join(result.tags),
                " ".join(result.tech_stack),
            ]
        )
        document_terms = self._tokenize(haystack)
        if not document_terms:
            return 0.0
        overlap = len(query_terms & document_terms)
        phrase_bonus = 0.15 if " ".join(sorted(query_terms)) in haystack.lower() else 0.0
        return min(1.0, overlap / max(len(query_terms), 1) + phrase_bonus)

    def _combine_scores(
        self,
        *,
        semantic_score: float,
        lexical_score: float,
        graph_boost: float = 0.0,
    ) -> float:
        return min(1.0, semantic_score * 0.65 + lexical_score * 0.35 + graph_boost)

    def _graph_boost(self, result: QueryResult) -> float:
        return min(0.05, len(result.related_ids) * 0.01)

    def _tokenize(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 1
        }

    def _is_same_entry(
        self,
        candidate: DuplicateCandidate,
        title: str,
        root_cause: str,
        tech_stack: list[str],
    ) -> bool:
        same_root_cause = candidate.root_cause.strip().lower() == root_cause.strip().lower()
        shared_tech = bool(set(candidate.tech_stack) & {item.strip().lower() for item in tech_stack})
        title_overlap = candidate.title.strip().lower() == title.strip().lower()
        return same_root_cause or shared_tech or title_overlap
