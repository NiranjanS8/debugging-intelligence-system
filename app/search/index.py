from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.config import get_settings
from app.models.debug_entry import DebugEntry
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SearchIndex:
    def __init__(self):
        self.base_path = get_settings().search_index_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_path / "bm25_index.json"
        self._documents: dict[str, dict] = {}
        self._bm25: BM25Okapi | None = None
        self._doc_ids: list[str] = []
        self._corpus_tokens: list[list[str]] = []
        self._load()

    def index_entry(self, entry: DebugEntry) -> None:
        self._documents[entry.id] = {
            "title": entry.title,
            "root_cause": entry.root_cause,
            "fix": entry.fix,
            "symptoms": entry.symptoms,
            "tags": entry.tags,
            "tech_stack": entry.tech_stack,
            "category": entry.category,
            "confidence": entry.confidence,
            "related_ids": entry.related_ids,
            "markdown_path": entry.markdown_path,
        }
        self._rebuild_model()
        self._save()

    def rebuild(self, entries: list[DebugEntry]) -> None:
        self._documents = {
            entry.id: {
                "title": entry.title,
                "root_cause": entry.root_cause,
                "fix": entry.fix,
                "symptoms": entry.symptoms,
                "tags": entry.tags,
                "tech_stack": entry.tech_stack,
                "category": entry.category,
                "confidence": entry.confidence,
                "related_ids": entry.related_ids,
                "markdown_path": entry.markdown_path,
            }
            for entry in entries
        }
        self._rebuild_model()
        self._save()

    def search(
        self,
        query: str,
        top_k: int = 10,
        *,
        tags: list[str] | None = None,
        tech_stack: list[str] | None = None,
    ) -> list[dict]:
        if self._bm25 is None or not self._doc_ids:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        max_score = max(scores) if len(scores) > 0 else 0.0
        results: list[dict] = []

        normalized_tags = {item.lower().strip() for item in tags or []}
        normalized_tech = {item.lower().strip() for item in tech_stack or []}

        for index, doc_id in enumerate(self._doc_ids):
            doc = self._documents.get(doc_id)
            if doc is None:
                continue
            if normalized_tags and not (set(doc.get("tags", [])) & normalized_tags):
                continue
            if normalized_tech and not (set(doc.get("tech_stack", [])) & normalized_tech):
                continue

            raw_score = float(scores[index])
            normalized_score = raw_score / max_score if max_score > 0 else 0.0
            if normalized_score <= 0.0:
                continue
            results.append({"id": doc_id, "score": round(normalized_score, 4), "document": doc})

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def get_document(self, entry_id: str) -> dict | None:
        return self._documents.get(entry_id)

    def _load(self) -> None:
        if not self.index_file.exists():
            self._rebuild_model()
            return

        try:
            payload = json.loads(self.index_file.read_text(encoding="utf-8"))
            self._documents = payload.get("documents", {})
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                f"Failed to load search index, rebuilding empty index: {exc}",
                extra={"operation": "search_index_load"},
            )
            self._documents = {}
        self._rebuild_model()

    def _save(self) -> None:
        payload = {"documents": self._documents}
        self.index_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _rebuild_model(self) -> None:
        self._doc_ids = list(self._documents.keys())
        self._corpus_tokens = [
            self._tokenize(self._document_text(self._documents[doc_id]))
            for doc_id in self._doc_ids
        ]
        non_empty = [tokens if tokens else ["_empty_"] for tokens in self._corpus_tokens]
        self._bm25 = BM25Okapi(non_empty) if non_empty else None

    def _document_text(self, doc: dict) -> str:
        return " ".join(
            [
                doc.get("title", ""),
                doc.get("root_cause", ""),
                doc.get("fix", ""),
                " ".join(doc.get("symptoms", [])),
                " ".join(doc.get("tags", [])),
                " ".join(doc.get("tech_stack", [])),
            ]
        )

    def _tokenize(self, text: str) -> list[str]:
        return [
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 1
        ]
