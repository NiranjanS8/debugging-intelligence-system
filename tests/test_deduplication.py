from __future__ import annotations

from app.models.debug_entry import DuplicateCandidate
from app.retrieval.service import RetrievalService


def test_find_duplicate_candidate_returns_match_above_threshold(monkeypatch) -> None:
    class DummyStore:
        def count(self) -> int:
            return 3

        def query(self, query_embedding: list[float], top_k: int = 1, where: dict | None = None) -> dict:
            return {
                "ids": [["existing111"]],
                "metadatas": [[{
                    "title": "CORS issue in local dev",
                    "root_cause": "cors misconfiguration",
                    "fix": "allow frontend origin",
                    "tags": "cors",
                    "tech_stack": "react,fastapi",
                }]],
                "distances": [[0.03]],
            }

    class DummyEmbeddingService:
        def generate(
            self,
            title: str,
            root_cause: str,
            fix: str,
            symptoms: list[str],
            tags: list[str] | None = None,
        ) -> list[float]:
            return [0.1, 0.2]

    class DummySettings:
        deduplication_threshold = 0.92

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)
    monkeypatch.setattr("app.retrieval.service.get_settings", lambda: DummySettings())

    service = RetrievalService()
    candidate = service.find_duplicate_candidate(
        title="CORS Error",
        root_cause="cors misconfiguration",
        fix="add middleware",
        symptoms=["request blocked"],
        tags=["cors"],
        tech_stack=["react", "fastapi"],
    )

    assert isinstance(candidate, DuplicateCandidate)
    assert candidate.id == "existing111"
    assert candidate.similarity_score == 0.97


def test_find_duplicate_candidate_returns_none_below_threshold(monkeypatch) -> None:
    class DummyStore:
        def count(self) -> int:
            return 1

        def query(self, query_embedding: list[float], top_k: int = 1, where: dict | None = None) -> dict:
            return {
                "ids": [["existing111"]],
                "metadatas": [[{
                    "title": "Different bug",
                    "root_cause": "different cause",
                    "fix": "different fix",
                    "tags": "other",
                    "tech_stack": "python",
                }]],
                "distances": [[0.2]],
            }

    class DummyEmbeddingService:
        def generate(
            self,
            title: str,
            root_cause: str,
            fix: str,
            symptoms: list[str],
            tags: list[str] | None = None,
        ) -> list[float]:
            return [0.1, 0.2]

    class DummySettings:
        deduplication_threshold = 0.92

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)
    monkeypatch.setattr("app.retrieval.service.get_settings", lambda: DummySettings())

    service = RetrievalService()
    candidate = service.find_duplicate_candidate(
        title="CORS Error",
        root_cause="cors misconfiguration",
        fix="add middleware",
        symptoms=["request blocked"],
        tags=["cors"],
        tech_stack=["react", "fastapi"],
    )

    assert candidate is None
