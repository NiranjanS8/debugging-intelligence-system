from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DebugAddRequest(BaseModel):
    raw_input: str = Field(
        ...,
        min_length=10,
        max_length=10_000,
        description="Raw debugging text: stack traces, error logs, notes, fixes.",
        examples=[
            "TypeError: undefined is not a function\n"
            "Fix: forgot to bind this in React component"
        ],
    )


class StructuredDebugData(BaseModel):
    """LLM-structured representation of a debugging session."""

    title: str = Field(..., min_length=3, max_length=200)
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str = Field(..., min_length=3)
    fix: str = Field(..., min_length=3)
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("tags", "tech_stack", mode="before")
    @classmethod
    def _normalize_list(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            v = [item.strip() for item in v.split(",") if item.strip()]
        return [item.lower().strip() for item in v]

    @field_validator("title", "root_cause", "fix")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        return v.strip()


class DebugEntry(BaseModel):
    """Persisted debug knowledge entry."""

    id: str
    title: str
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str
    fix: str
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    raw_input: str = ""
    category: str = "uncategorized"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    update_count: int = Field(default=0, ge=0)
    similarity_reliability: float = Field(default=0.0, ge=0.0, le=1.0)
    related_ids: list[str] = Field(default_factory=list)
    markdown_path: Optional[str] = None


class SimilarEntry(BaseModel):
    id: str
    title: str
    root_cause: str
    fix: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class DuplicateCandidate(BaseModel):
    id: str
    title: str
    root_cause: str
    fix: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)


class DebugEntryResponse(BaseModel):
    entry: DebugEntry
    similar_entries: list[SimilarEntry] = Field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: str | None = None
    duplicate_entry: DuplicateCandidate | None = None
    message: str = "Debug entry processed successfully."
