from __future__ import annotations

from app.clustering.engine import ClusteringEngine
from app.models.analytics import ClusterResponse
from app.retrieval.service import RetrievalService


class ClusteringService:
    def __init__(self):
        self.retrieval = RetrievalService()
        self.engine = ClusteringEngine()

    def cluster_entries(self, category: str | None = None) -> ClusterResponse:
        entries_with_embeddings = self.retrieval.get_entries_with_embeddings(category=category)
        return self.engine.cluster(entries_with_embeddings)
