from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.analytics import AnalyticsSummary, ClusterInfo, ClusterResponse, FailurePatternResponse, PatternStat
from app.models.debug_entry import DebugEntry, DebugEntryResponse, SimilarEntry
from main import create_app


def test_analytics_and_knowledge_routes(monkeypatch) -> None:
    from app.api import analytics_routes, knowledge_routes

    class DummyAnalyticsService:
        def get_summary(self) -> AnalyticsSummary:
            return AnalyticsSummary(total_entries=2, avg_confidence=0.7)

        def get_failure_patterns(self, limit: int = 5) -> FailurePatternResponse:
            return FailurePatternResponse(
                total_entries=2,
                top_tags=[PatternStat(name="react", count=1, percentage=50.0, examples=["A"])],
            )

    class DummyClusteringService:
        def cluster_entries(self, category: str | None = None) -> ClusterResponse:
            return ClusterResponse(
                total_entries=2,
                total_clusters=1,
                clusters=[
                    ClusterInfo(
                        cluster_id=0,
                        label="react pattern",
                        entry_ids=["a", "b"],
                        entry_titles=["A", "B"],
                        size=2,
                    )
                ],
            )

    class DummyRetrievalService:
        def list_entries(self, category: str | None = None) -> list:
            return []

        def get_entry(self, entry_id: str):
            return None

    class DummyMarkdownStorage:
        def read(self, relative_path: str) -> str | None:
            return "# Example"

    analytics_routes._analytics_service = DummyAnalyticsService()
    analytics_routes._clustering_service = DummyClusteringService()
    knowledge_routes._retrieval_service = DummyRetrievalService()
    knowledge_routes._markdown_storage = DummyMarkdownStorage()

    client = TestClient(create_app())

    summary = client.get("/analytics/summary")
    assert summary.status_code == 200
    assert summary.json()["total_entries"] == 2

    patterns = client.get("/analytics/patterns")
    assert patterns.status_code == 200
    assert patterns.json()["top_tags"][0]["name"] == "react"

    cluster = client.post("/analytics/cluster")
    assert cluster.status_code == 200
    assert cluster.json()["total_clusters"] == 1

    knowledge_list = client.get("/knowledge/list")
    assert knowledge_list.status_code == 200
    assert knowledge_list.json()["total_entries"] == 0


def test_debug_add_returns_similar_bug_suggestions(monkeypatch) -> None:
    from app.api import debug_routes

    class DummyIngestionService:
        async def ingest(self, raw_input: str) -> DebugEntryResponse:
            return DebugEntryResponse(
                entry=DebugEntry(
                    id="new123",
                    title="TypeError Error",
                    root_cause="incorrect handler binding",
                    fix="use an arrow function",
                    tags=["react"],
                    tech_stack=["react", "javascript"],
                    category="frontend",
                ),
                similar_entries=[
                    SimilarEntry(
                        id="old456",
                        title="Undefined handler in React",
                        root_cause="method was not bound to component instance",
                        fix="bind in constructor or use an arrow function",
                        similarity_score=0.91,
                        tags=["react", "undefined-error"],
                    )
                ],
            )

    debug_routes._service = DummyIngestionService()

    client = TestClient(create_app())
    response = client.post(
        "/debug/add",
        json={"raw_input": "TypeError: undefined is not a function\nFix: use arrow function"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["entry"]["id"] == "new123"
    assert len(payload["similar_entries"]) == 1
    assert payload["similar_entries"][0]["id"] == "old456"
    assert payload["similar_entries"][0]["similarity_score"] == 0.91
