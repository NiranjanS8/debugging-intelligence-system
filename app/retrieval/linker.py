from __future__ import annotations

from app.config import get_settings
from app.markdown.storage import MarkdownStorage
from app.models.debug_entry import DebugEntry, SimilarEntry
from app.retrieval.service import RetrievalService


class RetrievalLinker:
    def __init__(self):
        self.settings = get_settings()
        self.storage = MarkdownStorage()
        self.retrieval = RetrievalService()

    def link_entry(
        self,
        entry: DebugEntry,
        similar_entries: list[SimilarEntry],
    ) -> list[str]:
        selected = self._select_related(entry, similar_entries)
        entry.related_ids = [item.id for item in selected]
        if entry.markdown_path:
            self.storage.update_related_links(entry.markdown_path, selected)

        for related in selected:
            related_entry = self.retrieval.get_entry(related.id)
            if related_entry is None or not related_entry.markdown_path:
                continue

            related_ids = list(dict.fromkeys(related_entry.related_ids + [entry.id]))
            related_entry.related_ids = related_ids
            backlink = SimilarEntry(
                id=entry.id,
                title=entry.title,
                root_cause=entry.root_cause,
                fix=entry.fix,
                similarity_score=related.similarity_score,
                tags=entry.tags,
            )
            merged_links = self._merge_related_entries(related_entry.related_ids, backlink, selected)
            self.storage.update_related_links(related_entry.markdown_path, merged_links)
            self.retrieval.upsert_entry(related_entry)

        self.retrieval.upsert_entry(entry)
        return entry.related_ids

    def _select_related(
        self,
        entry: DebugEntry,
        similar_entries: list[SimilarEntry],
    ) -> list[SimilarEntry]:
        selected: list[SimilarEntry] = []
        for candidate in similar_entries:
            shared_tags = bool(set(entry.tags) & set(candidate.tags))
            if candidate.similarity_score >= self.settings.similarity_threshold or shared_tags:
                selected.append(candidate)
            if len(selected) == 3:
                break
        return selected

    def _merge_related_entries(
        self,
        existing_ids: list[str],
        backlink: SimilarEntry,
        candidates: list[SimilarEntry],
    ) -> list[SimilarEntry]:
        candidate_map = {candidate.id: candidate for candidate in candidates}
        candidate_map[backlink.id] = backlink

        merged: list[SimilarEntry] = []
        for related_id in existing_ids:
            related = candidate_map.get(related_id)
            if related is None:
                related_entry = self.retrieval.get_entry(related_id)
                if related_entry is None:
                    continue
                related = SimilarEntry(
                    id=related_entry.id,
                    title=related_entry.title,
                    root_cause=related_entry.root_cause,
                    fix=related_entry.fix,
                    similarity_score=0.0,
                    tags=related_entry.tags,
                )
            merged.append(related)
            if len(merged) == 5:
                break
        return merged
