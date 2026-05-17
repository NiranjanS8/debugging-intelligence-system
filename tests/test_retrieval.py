from __future__ import annotations

from app.models.debug_entry import DebugEntry
from app.retrieval.service import RetrievalService


def test_retrieval_parses_metadata_lists_and_scalars(monkeypatch) -> None:
    class DummyStore:
        def get_all_with_embeddings(self) -> dict:
            return {
                "ids": ["abc123"],
                "metadatas": [{
                    "title": "TypeError Error",
                    "symptoms": "crash,white screen",
                    "root_cause": "bad binding",
                    "fix": "use arrow function",
                    "tags": "react,undefined-error",
                    "tech_stack": "react,javascript",
                    "category": "frontend",
                    "confidence": 0.8,
                    "related_ids": "x1,x2",
                    "markdown_path": "frontend/typeerror-error.md",
                }],
                "embeddings": [[0.1, 0.2]],
            }

    class DummyEmbeddingService:
        pass

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)

    service = RetrievalService()
    entries = service.list_entries()

    assert len(entries) == 1
    entry = entries[0]
    assert isinstance(entry, DebugEntry)
    assert entry.tags == ["react", "undefined-error"]
    assert entry.related_ids == ["x1", "x2"]
    assert entry.markdown_path == "frontend/typeerror-error.md"
