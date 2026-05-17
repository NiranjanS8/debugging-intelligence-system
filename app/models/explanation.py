from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.debug_entry import SimilarEntry


class ExplanationSource(BaseModel):
    id: str
    title: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    root_cause: str
    fix: str


class DebugExplainRequest(BaseModel):
    raw_input: str = Field(..., min_length=10, max_length=10_000)
    top_k: int = Field(default=3, ge=1, le=10)
    include_graph_context: bool = True


class DebugExplanationResponse(BaseModel):
    summary: str
    probable_root_cause: str
    recommended_fix: str
    reasoning: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    next_steps: list[str] = Field(default_factory=list)
    supporting_entries: list[ExplanationSource] = Field(default_factory=list)
    graph_context_used: bool = False
    graph_observations: list[str] = Field(default_factory=list)
    message: str = "Debug explanation generated successfully."
