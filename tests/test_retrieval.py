from __future__ import annotations

from app.models.debug_entry import DebugEntry
from app.models.query import QueryResult
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


def test_hybrid_search_combines_semantic_and_lexical_scores(monkeypatch) -> None:
    class DummyStore:
        def __init__(self):
            pass

    class DummySearchIndex:
        def search(self, query: str, top_k: int = 10, tags=None, tech_stack=None) -> list[dict]:
            return [
                {"id": "a", "score": 0.8, "document": {}},
                {"id": "b", "score": 0.7, "document": {}},
            ]

    class DummyEmbeddingService:
        pass

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.SearchIndex", DummySearchIndex)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)

    service = RetrievalService()

    monkeypatch.setattr(
        service,
        "semantic_search",
        lambda query, top_k=5, where=None: [
            QueryResult(
                id="a",
                title="React CORS error",
                symptoms=["request blocked"],
                root_cause="cors misconfiguration",
                fix="allow localhost",
                tags=["cors"],
                tech_stack=["react", "fastapi"],
                confidence=0.8,
                similarity_score=0.7,
                related_ids=["x"],
            )
        ],
    )
    monkeypatch.setattr(
        service,
        "list_entries",
        lambda category=None: [
            DebugEntry(
                id="a",
                title="React CORS error",
                symptoms=["request blocked"],
                root_cause="cors misconfiguration",
                fix="allow localhost",
                tags=["cors"],
                tech_stack=["react", "fastapi"],
                confidence=0.8,
                related_ids=["x"],
            ),
            DebugEntry(
                id="b",
                title="CORS issue in local dev",
                symptoms=["browser blocked request"],
                root_cause="missing middleware",
                fix="configure cors",
                tags=["cors"],
                tech_stack=["react"],
                confidence=0.7,
            ),
        ],
    )

    results = service.hybrid_search("react cors blocked request", top_k=2)

    assert len(results) == 2
    assert results[0].id == "a"
    assert results[0].similarity_score > 0.7
    assert results[1].id == "b"


def test_hybrid_search_respects_metadata_filters(monkeypatch) -> None:
    class DummyStore:
        def __init__(self):
            pass

    class DummySearchIndex:
        def search(self, query: str, top_k: int = 10, tags=None, tech_stack=None) -> list[dict]:
            return [
                {"id": "a", "score": 0.9, "document": {}},
                {"id": "b", "score": 0.8, "document": {}},
            ]

    class DummyEmbeddingService:
        pass

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.SearchIndex", DummySearchIndex)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)

    service = RetrievalService()
    monkeypatch.setattr(service, "semantic_search", lambda query, top_k=5, where=None: [])
    monkeypatch.setattr(
        service,
        "list_entries",
        lambda category=None: [
            DebugEntry(
                id="a",
                title="React issue",
                root_cause="binding",
                fix="arrow function",
                tags=["react"],
                tech_stack=["react"],
                confidence=0.6,
            ),
            DebugEntry(
                id="b",
                title="Spring issue",
                root_cause="null check missing",
                fix="guard clause",
                tags=["backend"],
                tech_stack=["spring"],
                confidence=0.6,
            ),
        ],
    )

    results = service.hybrid_search(
        "react binding issue",
        top_k=5,
        tags=["react"],
        tech_stack=["react"],
    )

    assert [result.id for result in results] == ["a"]


def test_index_entry_updates_bm25_index(monkeypatch) -> None:
    calls: list[str] = []

    class DummyStore:
        def upsert(self, entry_id: str, embedding: list[float], metadata: dict, document: str) -> None:
            calls.append("vector")

    class DummySearchIndex:
        def index_entry(self, entry: DebugEntry) -> None:
            calls.append("lexical")

    class DummyEmbeddingService:
        def generate(self, title: str, root_cause: str, fix: str, symptoms: list[str], tags=None) -> list[float]:
            return [0.1, 0.2]

    monkeypatch.setattr("app.retrieval.service.ChromaStore", DummyStore)
    monkeypatch.setattr("app.retrieval.service.SearchIndex", DummySearchIndex)
    monkeypatch.setattr("app.retrieval.service.EmbeddingService", DummyEmbeddingService)

    service = RetrievalService()
    service.index_entry(
        DebugEntry(
            id="abc",
            title="React Error",
            root_cause="bad binding",
            fix="use arrow function",
            symptoms=["crash"],
            tags=["react"],
            tech_stack=["react"],
        )
    )

    assert calls == ["vector", "lexical"]
