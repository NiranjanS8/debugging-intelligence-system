from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    FALLBACK = "fallback"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Debugging Intelligence System"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    llm_provider: LLMProvider = LLMProvider.FALLBACK

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    embedding_model: str = "all-MiniLM-L6-v2"

    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "debug_knowledge"

    knowledge_base_dir: str = "./knowledge_base"
    projection_queue_dir: str = "./projection_queue"
    search_index_dir: str = "./search_index"

    neo4j_enabled: bool = False
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    default_top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    deduplication_threshold: float = Field(default=0.92, ge=0.0, le=1.0)
    wiki_link_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    wiki_max_links: int = Field(default=5, ge=1, le=20)

    cluster_distance_threshold: float = Field(default=1.0, gt=0.0)
    min_cluster_size: int = Field(default=2, ge=2)

    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.JSON

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.chroma_persist_dir).resolve()

    @property
    def knowledge_base_path(self) -> Path:
        return Path(self.knowledge_base_dir).resolve()

    @property
    def projection_queue_path(self) -> Path:
        return Path(self.projection_queue_dir).resolve()

    @property
    def search_index_path(self) -> Path:
        return Path(self.search_index_dir).resolve()

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_provider(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower().strip()
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
