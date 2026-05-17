from __future__ import annotations

from app.graph.service import GraphService
from app.llm.factory import get_llm_provider
from app.models.explanation import (
    DebugExplainRequest,
    DebugExplanationResponse,
    ExplanationSource,
)
from app.retrieval.service import RetrievalService


class DebugExplanationService:
    def __init__(self):
        self.retrieval = RetrievalService()
        self.graph = GraphService()
        self.provider = get_llm_provider()

    async def explain(self, request: DebugExplainRequest) -> DebugExplanationResponse:
        results = self.retrieval.hybrid_search(request.raw_input, top_k=request.top_k)
        sources = [
            ExplanationSource(
                id=result.id,
                title=result.title,
                similarity_score=result.similarity_score,
                root_cause=result.root_cause,
                fix=result.fix,
            )
            for result in results
        ]
        graph_used = False
        graph_observations: list[str] = []
        if request.include_graph_context and sources and self.graph.enabled:
            neighborhood = self.graph.get_entry_neighborhood(sources[0].id)
            graph_used = neighborhood.graph_enabled and neighborhood.total_nodes > 0
            if graph_used:
                graph_observations = [
                    f"{edge.source} -[{edge.relationship}]-> {edge.target}"
                    for edge in neighborhood.edges[:5]
                ]

        retrieval_context = self._build_context(request.raw_input, sources, graph_observations)
        explanation = await self.provider.explain_debug_issue(request.raw_input, retrieval_context)
        explanation.supporting_entries = sources
        explanation.graph_context_used = graph_used
        explanation.graph_observations = graph_observations
        return explanation

    def _build_context(
        self,
        raw_input: str,
        sources: list[ExplanationSource],
        graph_observations: list[str],
    ) -> str:
        lines = [f"Raw Input: {raw_input}", ""]
        if sources:
            lines.append("Retrieved Similar Entries:")
            for source in sources:
                lines.extend([
                    f"Title: {source.title}",
                    f"ID: {source.id}",
                    f"Similarity: {source.similarity_score}",
                    f"Root Cause: {source.root_cause}",
                    f"Fix: {source.fix}",
                    "",
                ])
        if graph_observations:
            lines.append("Graph Observations:")
            lines.extend(graph_observations)
        return "\n".join(lines).strip()
