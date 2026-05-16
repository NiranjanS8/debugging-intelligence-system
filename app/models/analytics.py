from __future__ import annotations

from pydantic import BaseModel, Field


class ClusterInfo(BaseModel):
    cluster_id: int
    label: str
    entry_ids: list[str] = Field(default_factory=list)
    entry_titles: list[str] = Field(default_factory=list)
    size: int = 0
    common_tags: list[str] = Field(default_factory=list)
    common_tech_stack: list[str] = Field(default_factory=list)


class ClusterResponse(BaseModel):
    clusters: list[ClusterInfo] = Field(default_factory=list)
    total_entries: int = 0
    total_clusters: int = 0
    noise_entries: int = 0


class PatternStat(BaseModel):
    name: str
    count: int
    percentage: float = Field(ge=0.0, le=100.0)
    examples: list[str] = Field(default_factory=list)


class FailurePatternResponse(BaseModel):
    top_root_causes: list[PatternStat] = Field(default_factory=list)
    top_tags: list[PatternStat] = Field(default_factory=list)
    top_tech_stack: list[PatternStat] = Field(default_factory=list)
    total_entries: int = 0


class AnalyticsSummary(BaseModel):
    total_entries: int = 0
    total_categories: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = 0.0
    tech_stack_distribution: dict[str, int] = Field(default_factory=dict)
    tag_distribution: dict[str, int] = Field(default_factory=dict)
    most_common_root_causes: list[str] = Field(default_factory=list)
    recent_entries: list[str] = Field(default_factory=list)
