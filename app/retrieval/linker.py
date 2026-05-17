from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.graph.service import GraphService
from app.markdown.storage import MarkdownStorage
from app.models.debug_entry import DebugEntry, SimilarEntry
from app.retrieval.service import RetrievalService


@dataclass
class _ScoredLink:
    entry: SimilarEntry
    score: float


class RetrievalLinker:
    def __init__(self):
        self.settings = get_settings()
        self.storage = MarkdownStorage()
        self.retrieval = RetrievalService()
        self.graph = GraphService()

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

    def relink_all(self) -> dict[str, int]:
        entries = self.retrieval.list_entries()
        if not entries:
            return {"processed_entries": 0, "updated_pages": 0}

        candidate_map = {entry.id: self._build_candidate(entry) for entry in entries}
        related_lookup: dict[str, list[SimilarEntry]] = {}

        for entry in entries:
            neighbors = [
                candidate_map[other.id]
                for other in entries
                if other.id != entry.id
            ]
            selected = self._select_related(entry, neighbors)
            related_lookup[entry.id] = selected

        updated_pages = 0
        for entry in entries:
            selected = related_lookup.get(entry.id, [])
            entry.related_ids = [item.id for item in selected]
            if entry.markdown_path:
                self.storage.update_related_links(entry.markdown_path, selected)
                updated_pages += 1
            self.retrieval.upsert_entry(entry)

        return {"processed_entries": len(entries), "updated_pages": updated_pages}

    def _select_related(
        self,
        entry: DebugEntry,
        similar_entries: list[SimilarEntry],
    ) -> list[SimilarEntry]:
        scored_links: list[_ScoredLink] = []
        graph_ids = set(self.graph.get_related_bug_ids(entry.id, limit=self.settings.wiki_max_links))
        for candidate in similar_entries:
            related_entry = self.retrieval.get_entry(candidate.id)
            if related_entry is None:
                continue

            shared_tags = len(set(entry.tags) & set(candidate.tags))
            shared_tech = len(set(entry.tech_stack) & set(related_entry.tech_stack))
            same_category = 1 if entry.category == related_entry.category else 0
            same_root_cause = (
                1 if entry.root_cause.strip().lower() == related_entry.root_cause.strip().lower() else 0
            )
            graph_bonus = 0.08 if candidate.id in graph_ids else 0.0

            composite_score = (
                candidate.similarity_score * 0.65
                + min(shared_tags, 3) * 0.08
                + min(shared_tech, 3) * 0.06
                + same_category * 0.05
                + same_root_cause * 0.12
                + graph_bonus
            )

            if composite_score >= self.settings.wiki_link_threshold:
                scored_links.append(_ScoredLink(entry=candidate, score=round(composite_score, 4)))

        scored_links.sort(key=lambda item: item.score, reverse=True)
        selected: list[SimilarEntry] = []
        for item in scored_links[: self.settings.wiki_max_links]:
            selected.append(
                SimilarEntry(
                    id=item.entry.id,
                    title=item.entry.title,
                    root_cause=item.entry.root_cause,
                    fix=item.entry.fix,
                    similarity_score=item.score,
                    tags=item.entry.tags,
                )
            )
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
            if len(merged) == self.settings.wiki_max_links:
                break
        return merged

    def _build_candidate(self, entry: DebugEntry) -> SimilarEntry:
        return SimilarEntry(
            id=entry.id,
            title=entry.title,
            root_cause=entry.root_cause,
            fix=entry.fix,
            similarity_score=0.7,
            tags=entry.tags,
        )
