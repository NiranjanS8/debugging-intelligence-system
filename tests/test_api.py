from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.analytics import AnalyticsSummary, ClusterInfo, ClusterResponse, FailurePatternResponse, PatternStat
from app.models.debug_entry import DebugEntry, DebugEntryResponse, DuplicateCandidate, SimilarEntry
from app.models.explanation import DebugExplanationResponse, ExplanationSource
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


def test_debug_add_flags_semantic_duplicate() -> None:
    from app.api import debug_routes

    class DummyIngestionService:
        async def ingest(self, raw_input: str) -> DebugEntryResponse:
            return DebugEntryResponse(
                entry=DebugEntry(
                    id="new999",
                    title="CORS Error",
                    root_cause="cors misconfiguration",
                    fix="add middleware",
                    tags=["cors"],
                    tech_stack=["react", "fastapi"],
                    category="frontend",
                ),
                is_duplicate=True,
                duplicate_of="existing111",
                duplicate_entry=DuplicateCandidate(
                    id="existing111",
                    title="CORS issue in local dev",
                    root_cause="cors misconfiguration",
                    fix="allow frontend origin",
                    similarity_score=0.96,
                    tags=["cors"],
                    tech_stack=["react", "fastapi"],
                ),
                message="Likely semantic duplicate detected.",
            )

    debug_routes._service = DummyIngestionService()

    client = TestClient(create_app())
    response = client.post(
        "/debug/add",
        json={"raw_input": "CORS error blocked by access-control-allow-origin\nFix: add middleware"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_duplicate"] is True
    assert payload["duplicate_of"] == "existing111"
    assert payload["duplicate_entry"]["similarity_score"] == 0.96
    assert payload["message"] == "Likely semantic duplicate detected."


def test_debug_explain_returns_grounded_response() -> None:
    from app.api import explanation_routes

    class DummyExplanationService:
        async def explain(self, request) -> DebugExplanationResponse:
            return DebugExplanationResponse(
                summary="This looks like a CORS configuration issue.",
                probable_root_cause="Missing or incorrect CORS middleware configuration.",
                recommended_fix="Allow the frontend origin in the backend CORS settings.",
                reasoning="The retrieved incidents show the same symptom and were resolved by aligning allowed origins.",
                confidence=0.86,
                next_steps=["Check allowed origins.", "Retry the failing request."],
                supporting_entries=[
                    ExplanationSource(
                        id="cors-1",
                        title="Local dev CORS error",
                        similarity_score=0.93,
                        root_cause="cors misconfiguration",
                        fix="allow localhost origin",
                    )
                ],
                graph_context_used=True,
                graph_observations=["cors-1 -[HAS_ROOT_CAUSE]-> cors misconfiguration"],
            )

    explanation_routes._service = DummyExplanationService()

    client = TestClient(create_app())
    response = client.post(
        "/debug/explain",
        json={"raw_input": "CORS error blocked by access-control-allow-origin", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["probable_root_cause"] == "Missing or incorrect CORS middleware configuration."
    assert payload["supporting_entries"][0]["id"] == "cors-1"
    assert payload["graph_context_used"] is True
