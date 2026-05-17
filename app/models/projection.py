from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.debug_entry import DebugEntry, SimilarEntry


class ProjectionTask(BaseModel):
    task_id: str
    entry: DebugEntry
    similar_entries: list[SimilarEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"
    attempts: int = 0
    last_error: str | None = None
