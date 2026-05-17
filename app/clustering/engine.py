from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from app.config import get_settings
from app.models.analytics import ClusterInfo, ClusterResponse
from app.models.debug_entry import DebugEntry


class ClusteringEngine:
    def __init__(self):
        self.settings = get_settings()

    def cluster(
        self,
        entries_with_embeddings: list[tuple[DebugEntry, list[float]]],
    ) -> ClusterResponse:
        total_entries = len(entries_with_embeddings)
        if total_entries == 0:
            return ClusterResponse()

        if total_entries < 2:
            return ClusterResponse(
                total_entries=total_entries,
                total_clusters=0,
                noise_entries=total_entries,
            )

        matrix = np.array([embedding for _, embedding in entries_with_embeddings], dtype=float)
        model = AgglomerativeClustering(
            n_clusters=None,
            metric="cosine",
            linkage="average",
            distance_threshold=self.settings.cluster_distance_threshold,
        )
        labels = model.fit_predict(matrix)

        grouped: dict[int, list[DebugEntry]] = defaultdict(list)
        for label, (entry, _) in zip(labels, entries_with_embeddings):
            grouped[int(label)].append(entry)

        clusters: list[ClusterInfo] = []
        noise_entries = 0

        for label, entries in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True):
            if len(entries) < self.settings.min_cluster_size:
                noise_entries += len(entries)
                continue

            tags = Counter(tag for entry in entries for tag in entry.tags)
            tech_stack = Counter(tech for entry in entries for tech in entry.tech_stack)
            clusters.append(
                ClusterInfo(
                    cluster_id=label,
                    label=self._build_label(entries, tags, tech_stack),
                    entry_ids=[entry.id for entry in entries],
                    entry_titles=[entry.title for entry in entries],
                    size=len(entries),
                    common_tags=[name for name, _ in tags.most_common(5)],
                    common_tech_stack=[name for name, _ in tech_stack.most_common(5)],
                )
            )

        return ClusterResponse(
            clusters=clusters,
            total_entries=total_entries,
            total_clusters=len(clusters),
            noise_entries=noise_entries,
        )

    def _build_label(
        self,
        entries: list[DebugEntry],
        tags: Counter[str],
        tech_stack: Counter[str],
    ) -> str:
        if tags:
            return f"{tags.most_common(1)[0][0]} pattern"
        if tech_stack:
            return f"{tech_stack.most_common(1)[0][0]} issues"

        causes = Counter(entry.root_cause.strip().lower() for entry in entries if entry.root_cause.strip())
        if causes:
            return causes.most_common(1)[0][0][:80]
        return "related debugging issues"
