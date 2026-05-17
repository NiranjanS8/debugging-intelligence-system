from __future__ import annotations

from app.models.debug_entry import DebugEntry, SimilarEntry
from app.models.graph import GraphNeighborhoodResponse, GraphSummaryResponse


def test_graph_service_disabled_by_default() -> None:
    from app.graph.service import GraphService

    service = GraphService()
    assert service.get_summary() == GraphSummaryResponse(graph_enabled=False)


def test_graph_sync_writes_expected_relationships(monkeypatch) -> None:
    from app.graph.service import GraphService

    executed: list[tuple[str, dict]] = []

    class DummyStore:
        enabled = True

        def ensure_schema(self) -> None:
            return None

        def run(self, query: str, parameters: dict | None = None) -> list[dict]:
            executed.append((query, parameters or {}))
            return []

    monkeypatch.setattr("app.graph.service.GraphStore", DummyStore)

    service = GraphService()
    entry = DebugEntry(
        id="bug-1",
        title="CORS error",
        symptoms=["request blocked"],
        root_cause="cors misconfiguration",
        fix="add middleware",
        tags=["cors"],
        tech_stack=["fastapi", "react"],
        category="frontend",
    )
    similar = [
        SimilarEntry(
            id="bug-2",
            title="Axios blocked",
            root_cause="cors misconfiguration",
            fix="allow origin",
            similarity_score=0.88,
            tags=["cors"],
        )
    ]

    result = service.sync_entry(entry, similar)

    assert result is True
    assert any("MERGE (b:Bug {id: $id})" in query for query, _ in executed)
    assert any("HAS_ROOT_CAUSE" in query for query, _ in executed)
    assert any("AFFECTS_TECH" in query for query, _ in executed)
    assert any("SIMILAR_TO" in query for query, _ in executed)


def test_graph_routes_can_be_stubbed() -> None:
    from app.api import graph_routes

    class DummyGraphService:
        def get_summary(self) -> GraphSummaryResponse:
            return GraphSummaryResponse(graph_enabled=True, total_bugs=3, total_root_causes=2)

        def get_entry_neighborhood(self, entry_id: str) -> GraphNeighborhoodResponse:
            return GraphNeighborhoodResponse(
                entry_id=entry_id,
                graph_enabled=True,
                total_nodes=2,
                total_edges=1,
            )

    graph_routes._graph_service = DummyGraphService()

    assert graph_routes._get_service().get_summary().total_bugs == 3
    assert graph_routes._get_service().get_entry_neighborhood("bug-1").total_edges == 1
