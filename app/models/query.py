from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DebugQueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=1_000,
        examples=["null errors in React", "issues caused by incorrect binding"],
    )
    top_k: int = Field(default=5, ge=1, le=50)
    tags: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None
    min_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class QueryResult(BaseModel):
    id: str
    title: str
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    fix: str
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    related_ids: list[str] = Field(default_factory=list)


class DebugQueryResponse(BaseModel):
    query: str
    results: list[QueryResult] = Field(default_factory=list)
    total_results: int = 0
    message: str = "Query executed successfully."
