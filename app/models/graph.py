from __future__ import annotations

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    node_id: str
    label: str
    properties: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    properties: dict[str, str | int | float | bool] = Field(default_factory=dict)


class GraphNeighborhoodResponse(BaseModel):
    entry_id: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    graph_enabled: bool = False


class GraphSummaryResponse(BaseModel):
    graph_enabled: bool = False
    total_bugs: int = 0
    total_root_causes: int = 0
    total_technologies: int = 0
    total_symptoms: int = 0
    total_tags: int = 0
    total_similarity_edges: int = 0
