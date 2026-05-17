from __future__ import annotations

from app.models.explanation import DebugExplainRequest, DebugExplanationResponse
from app.models.query import QueryResult


def test_explanation_service_builds_sources_and_graph_context(monkeypatch) -> None:
    from app.explanations.service import DebugExplanationService

    class DummyRetrievalService:
        def hybrid_search(self, query: str, top_k: int = 5, tags=None, tech_stack=None, where=None):
            return [
                QueryResult(
                    id="bug-1",
                    title="CORS error",
                    symptoms=["request blocked"],
                    root_cause="cors misconfiguration",
                    fix="add middleware",
                    tags=["cors"],
                    tech_stack=["react", "fastapi"],
                    confidence=0.8,
                    similarity_score=0.91,
                    related_ids=[],
                )
            ]

    class DummyGraphService:
        enabled = True

        def get_entry_neighborhood(self, entry_id: str):
            from app.models.graph import GraphNeighborhoodResponse, GraphEdge
            return GraphNeighborhoodResponse(
                entry_id=entry_id,
                graph_enabled=True,
                total_nodes=2,
                total_edges=1,
                edges=[
                    GraphEdge(
                        source="bug-1",
                        target="cors misconfiguration",
                        relationship="HAS_ROOT_CAUSE",
                    )
                ],
            )

    class DummyProvider:
        async def explain_debug_issue(self, raw_text: str, retrieval_context: str) -> DebugExplanationResponse:
            assert "CORS error" in retrieval_context
            assert "HAS_ROOT_CAUSE" in retrieval_context
            return DebugExplanationResponse(
                summary="summary",
                probable_root_cause="cause",
                recommended_fix="fix",
                reasoning="reasoning",
                confidence=0.7,
                next_steps=["step"],
            )

    monkeypatch.setattr("app.explanations.service.RetrievalService", DummyRetrievalService)
    monkeypatch.setattr("app.explanations.service.GraphService", DummyGraphService)
    monkeypatch.setattr("app.explanations.service.get_llm_provider", lambda: DummyProvider())

    service = DebugExplanationService()
    result = __import__("asyncio").run(
        service.explain(
            DebugExplainRequest(
                raw_input="CORS error blocked by access-control-allow-origin",
                top_k=3,
                include_graph_context=True,
            )
        )
    )

    assert result.supporting_entries[0].id == "bug-1"
    assert result.graph_context_used is True
    assert result.graph_observations[0] == "bug-1 -[HAS_ROOT_CAUSE]-> cors misconfiguration"
