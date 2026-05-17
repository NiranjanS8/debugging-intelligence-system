from __future__ import annotations

from collections import Counter

from app.models.analytics import AnalyticsSummary, FailurePatternResponse, PatternStat
from app.models.debug_entry import DebugEntry
from app.retrieval.service import RetrievalService


class AnalyticsService:
    def __init__(self):
        self.retrieval = RetrievalService()

    def get_summary(self) -> AnalyticsSummary:
        entries = self.retrieval.list_entries()
        if not entries:
            return AnalyticsSummary()

        categories = Counter(entry.category for entry in entries)
        tags = Counter(tag for entry in entries for tag in entry.tags)
        tech_stack = Counter(tech for entry in entries for tech in entry.tech_stack)
        root_causes = Counter(
            self._normalize_root_cause(entry.root_cause) for entry in entries if entry.root_cause
        )

        avg_confidence = sum(entry.confidence for entry in entries) / len(entries)

        return AnalyticsSummary(
            total_entries=len(entries),
            total_categories=dict(categories),
            avg_confidence=round(avg_confidence, 4),
            tech_stack_distribution=dict(tech_stack.most_common()),
            tag_distribution=dict(tags.most_common()),
            most_common_root_causes=[name for name, _ in root_causes.most_common(5)],
            recent_entries=[entry.title for entry in entries[:5]],
        )

    def get_failure_patterns(self, limit: int = 5) -> FailurePatternResponse:
        entries = self.retrieval.list_entries()
        if not entries:
            return FailurePatternResponse()

        return FailurePatternResponse(
            top_root_causes=self._build_pattern_stats(
                entries,
                lambda entry: self._normalize_root_cause(entry.root_cause),
                limit=limit,
            ),
            top_tags=self._build_pattern_stats(
                entries,
                lambda entry: entry.tags,
                limit=limit,
            ),
            top_tech_stack=self._build_pattern_stats(
                entries,
                lambda entry: entry.tech_stack,
                limit=limit,
            ),
            total_entries=len(entries),
        )

    def _build_pattern_stats(
        self,
        entries: list[DebugEntry],
        extractor,
        limit: int,
    ) -> list[PatternStat]:
        counts: Counter[str] = Counter()
        examples: dict[str, list[str]] = {}

        for entry in entries:
            values = extractor(entry)
            if isinstance(values, str):
                values = [values] if values else []

            for value in values:
                normalized = value.strip().lower()
                if not normalized:
                    continue
                counts[normalized] += 1
                examples.setdefault(normalized, [])
                if entry.title not in examples[normalized] and len(examples[normalized]) < 3:
                    examples[normalized].append(entry.title)

        total_entries = len(entries)
        results: list[PatternStat] = []
        for name, count in counts.most_common(limit):
            results.append(
                PatternStat(
                    name=name,
                    count=count,
                    percentage=round((count / total_entries) * 100, 2),
                    examples=examples.get(name, []),
                )
            )
        return results

    def _normalize_root_cause(self, value: str) -> str:
        return value.strip().lower()
