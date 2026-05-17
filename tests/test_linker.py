from __future__ import annotations

from app.models.debug_entry import DebugEntry, SimilarEntry


def test_relink_all_updates_existing_pages(monkeypatch) -> None:
    from app.retrieval.linker import RetrievalLinker

    entries = [
        DebugEntry(
            id="a",
            title="React CORS error",
            root_cause="cors misconfiguration",
            fix="allow origin",
            tags=["cors"],
            tech_stack=["react", "fastapi"],
            category="frontend",
            markdown_path="frontend/a.md",
        ),
        DebugEntry(
            id="b",
            title="Local dev CORS issue",
            root_cause="cors misconfiguration",
            fix="configure middleware",
            tags=["cors"],
            tech_stack=["react", "fastapi"],
            category="frontend",
            markdown_path="frontend/b.md",
        ),
    ]

    updates: list[tuple[str, list[str]]] = []

    class DummyStorage:
        def update_related_links(self, relative_path: str, related_entries: list[SimilarEntry]) -> None:
            updates.append((relative_path, [entry.id for entry in related_entries]))

    class DummyRetrieval:
        def list_entries(self) -> list[DebugEntry]:
            return entries

        def get_entry(self, entry_id: str) -> DebugEntry | None:
            return next((entry for entry in entries if entry.id == entry_id), None)

        def upsert_entry(self, entry: DebugEntry) -> None:
            return None

    class DummyGraphService:
        def get_related_bug_ids(self, entry_id: str, limit: int = 5) -> list[str]:
            return ["b"] if entry_id == "a" else ["a"]

    monkeypatch.setattr("app.retrieval.linker.MarkdownStorage", DummyStorage)
    monkeypatch.setattr("app.retrieval.linker.RetrievalService", DummyRetrieval)
    monkeypatch.setattr("app.retrieval.linker.GraphService", DummyGraphService)

    linker = RetrievalLinker()
    stats = linker.relink_all()

    assert stats == {"processed_entries": 2, "updated_pages": 2}
    assert ("frontend/a.md", ["b"]) in updates
    assert ("frontend/b.md", ["a"]) in updates


def test_select_related_filters_weak_candidates(monkeypatch) -> None:
    from app.retrieval.linker import RetrievalLinker

    base_entry = DebugEntry(
        id="a",
        title="Database timeout",
        root_cause="stale connection pool",
        fix="recreate pool",
        tags=["timeout"],
        tech_stack=["python", "postgres"],
        category="backend",
    )
    weak_candidate = SimilarEntry(
        id="b",
        title="Unrelated CSS issue",
        root_cause="missing stylesheet",
        fix="load stylesheet",
        similarity_score=0.2,
        tags=["css"],
    )

    class DummyRetrieval:
        def get_entry(self, entry_id: str) -> DebugEntry | None:
            return DebugEntry(
                id="b",
                title="Unrelated CSS issue",
                root_cause="missing stylesheet",
                fix="load stylesheet",
                tags=["css"],
                tech_stack=["css"],
                category="frontend",
            )

    class DummyGraphService:
        def get_related_bug_ids(self, entry_id: str, limit: int = 5) -> list[str]:
            return []

    monkeypatch.setattr("app.retrieval.linker.RetrievalService", DummyRetrieval)
    monkeypatch.setattr("app.retrieval.linker.GraphService", DummyGraphService)

    linker = RetrievalLinker()
    assert linker._select_related(base_entry, [weak_candidate]) == []
