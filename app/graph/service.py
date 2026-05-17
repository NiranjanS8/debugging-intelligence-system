from __future__ import annotations

from app.graph.store import GraphStore
from app.models.debug_entry import DebugEntry, SimilarEntry
from app.models.graph import (
    GraphEdge,
    GraphNeighborhoodResponse,
    GraphNode,
    GraphSummaryResponse,
)
from app.utils.logger import get_logger
from app.utils.text_processing import generate_slug

logger = get_logger(__name__)


class GraphService:
    def __init__(self):
        self.store = GraphStore()
        self.enabled = self.store.enabled
        if self.enabled:
            self.store.ensure_schema()

    def sync_entry(self, entry: DebugEntry, similar_entries: list[SimilarEntry]) -> bool:
        if not self.enabled:
            return False

        try:
            self._upsert_bug(entry)
            self._link_root_cause(entry)
            self._link_tech_stack(entry)
            self._link_symptoms(entry)
            self._link_tags(entry)
            self._link_similar_entries(entry, similar_entries)
            return True
        except Exception as exc:
            logger.warning(
                f"Graph sync failed: {exc}",
                extra={"operation": "graph_sync", "entry_id": entry.id},
            )
            return False

    def get_summary(self) -> GraphSummaryResponse:
        if not self.enabled:
            return GraphSummaryResponse(graph_enabled=False)

        query = """
        RETURN
          size([(b:Bug) | b]) AS total_bugs,
          size([(r:RootCause) | r]) AS total_root_causes,
          size([(t:Tech) | t]) AS total_technologies,
          size([(s:Symptom) | s]) AS total_symptoms,
          size([(g:Tag) | g]) AS total_tags,
          size([()-[rel:SIMILAR_TO]->() | rel]) AS total_similarity_edges
        """
        rows = self.store.run(query)
        if not rows:
            return GraphSummaryResponse(graph_enabled=True)

        return GraphSummaryResponse(graph_enabled=True, **rows[0])

    def get_entry_neighborhood(self, entry_id: str) -> GraphNeighborhoodResponse:
        if not self.enabled:
            return GraphNeighborhoodResponse(entry_id=entry_id, graph_enabled=False)

        query = """
        MATCH (b:Bug {id: $entry_id})
        OPTIONAL MATCH (b)-[r1]->(n1)
        OPTIONAL MATCH (n2)-[r2]->(b)
        WITH b,
             collect(DISTINCT {source: b.id, target: coalesce(n1.id, n1.name), relationship: type(r1), properties: properties(r1)}) AS outgoing,
             collect(DISTINCT {source: coalesce(n2.id, n2.name), target: b.id, relationship: type(r2), properties: properties(r2)}) AS incoming,
             collect(DISTINCT b) + collect(DISTINCT n1) + collect(DISTINCT n2) AS nodes
        RETURN nodes, outgoing + incoming AS edges
        """
        rows = self.store.run(query, {"entry_id": entry_id})
        if not rows:
            return GraphNeighborhoodResponse(entry_id=entry_id, graph_enabled=True)

        raw_nodes = rows[0].get("nodes", [])
        raw_edges = rows[0].get("edges", [])

        nodes: list[GraphNode] = []
        seen_nodes: set[str] = set()
        for node in raw_nodes:
            if node is None:
                continue
            labels = list(getattr(node, "labels", []))
            props = dict(node)
            node_key = str(props.get("id") or props.get("name") or props.get("slug"))
            if not node_key or node_key in seen_nodes:
                continue
            seen_nodes.add(node_key)
            nodes.append(
                GraphNode(
                    node_id=node_key,
                    label=labels[0] if labels else "Node",
                    properties={key: value for key, value in props.items()},
                )
            )

        edges: list[GraphEdge] = []
        seen_edges: set[tuple[str, str, str]] = set()
        for edge in raw_edges:
            if not edge or not edge.get("relationship"):
                continue
            edge_key = (str(edge["source"]), str(edge["target"]), str(edge["relationship"]))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(
                GraphEdge(
                    source=str(edge["source"]),
                    target=str(edge["target"]),
                    relationship=str(edge["relationship"]),
                    properties=edge.get("properties", {}),
                )
            )

        return GraphNeighborhoodResponse(
            entry_id=entry_id,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
            graph_enabled=True,
        )

    def _upsert_bug(self, entry: DebugEntry) -> None:
        query = """
        MERGE (b:Bug {id: $id})
        SET b.title = $title,
            b.category = $category,
            b.root_cause = $root_cause,
            b.fix = $fix,
            b.confidence = $confidence,
            b.similarity_reliability = $similarity_reliability,
            b.update_count = $update_count,
            b.markdown_path = $markdown_path,
            b.slug = $slug,
            b.created_at = $created_at,
            b.updated_at = $updated_at
        """
        self.store.run(
            query,
            {
                "id": entry.id,
                "title": entry.title,
                "category": entry.category,
                "root_cause": entry.root_cause,
                "fix": entry.fix,
                "confidence": entry.confidence,
                "similarity_reliability": entry.similarity_reliability,
                "update_count": entry.update_count,
                "markdown_path": entry.markdown_path or "",
                "slug": generate_slug(entry.title),
                "created_at": entry.created_at.isoformat(),
                "updated_at": entry.updated_at.isoformat(),
            },
        )

    def _link_root_cause(self, entry: DebugEntry) -> None:
        query = """
        MATCH (b:Bug {id: $entry_id})
        MERGE (r:RootCause {name: $name})
        MERGE (b)-[:HAS_ROOT_CAUSE]->(r)
        """
        self.store.run(query, {"entry_id": entry.id, "name": entry.root_cause.strip().lower()})

    def _link_tech_stack(self, entry: DebugEntry) -> None:
        query = """
        MATCH (b:Bug {id: $entry_id})
        MERGE (t:Tech {name: $name})
        MERGE (b)-[:AFFECTS_TECH]->(t)
        """
        for tech in entry.tech_stack:
            self.store.run(query, {"entry_id": entry.id, "name": tech.strip().lower()})

    def _link_symptoms(self, entry: DebugEntry) -> None:
        query = """
        MATCH (b:Bug {id: $entry_id})
        MERGE (s:Symptom {name: $name})
        MERGE (b)-[:HAS_SYMPTOM]->(s)
        """
        for symptom in entry.symptoms:
            self.store.run(query, {"entry_id": entry.id, "name": symptom.strip().lower()})

    def _link_tags(self, entry: DebugEntry) -> None:
        query = """
        MATCH (b:Bug {id: $entry_id})
        MERGE (t:Tag {name: $name})
        MERGE (b)-[:TAGGED_WITH]->(t)
        """
        for tag in entry.tags:
            self.store.run(query, {"entry_id": entry.id, "name": tag.strip().lower()})

    def _link_similar_entries(
        self,
        entry: DebugEntry,
        similar_entries: list[SimilarEntry],
    ) -> None:
        query = """
        MATCH (a:Bug {id: $source_id})
        MATCH (b:Bug {id: $target_id})
        MERGE (a)-[rel:SIMILAR_TO]->(b)
        SET rel.score = $score
        """
        for similar in similar_entries:
            self.store.run(
                query,
                {
                    "source_id": entry.id,
                    "target_id": similar.id,
                    "score": similar.similarity_score,
                },
            )
