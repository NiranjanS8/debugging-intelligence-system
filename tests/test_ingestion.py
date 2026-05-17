from __future__ import annotations

from app.ingestion.parser import DebugInputParser
from app.models.debug_entry import DebugEntry, SimilarEntry, StructuredDebugData


def test_parser_trims_large_stack_traces() -> None:
    parser = DebugInputParser()
    raw = "Traceback\n" + "\n".join(f"at frame {index}" for index in range(40))
    parsed = parser.parse(raw)
    assert "frames omitted" in parsed


def test_linker_updates_related_ids(monkeypatch) -> None:
    from app.retrieval.linker import RetrievalLinker

    entry = DebugEntry(
        id="new-entry",
        title="New entry",
        root_cause="wrong binding",
        fix="use arrow function",
        tags=["react"],
        markdown_path="frontend/new-entry.md",
    )
    similar = [
        SimilarEntry(
            id="existing",
            title="Existing entry",
            root_cause="wrong binding",
            fix="bind handler",
            similarity_score=0.92,
            tags=["react"],
        )
    ]

    updates: list[tuple[str, list[str]]] = []

    class DummyStorage:
        def update_related_links(self, relative_path: str, related_entries: list[SimilarEntry]) -> None:
            updates.append((relative_path, [item.id for item in related_entries]))

    class DummyRetrieval:
        def __init__(self):
            self.entries = {
                "existing": DebugEntry(
                    id="existing",
                    title="Existing entry",
                    root_cause="wrong binding",
                    fix="bind handler",
                    tags=["react"],
                    markdown_path="frontend/existing.md",
                )
            }
            self.upserts: list[str] = []

        def get_entry(self, entry_id: str) -> DebugEntry | None:
            return self.entries.get(entry_id)

        def upsert_entry(self, value: DebugEntry) -> None:
            self.upserts.append(value.id)

    monkeypatch.setattr("app.retrieval.linker.MarkdownStorage", DummyStorage)
    monkeypatch.setattr("app.retrieval.linker.RetrievalService", DummyRetrieval)

    linker = RetrievalLinker()
    related_ids = linker.link_entry(entry, similar)

    assert related_ids == ["existing"]
    assert ("frontend/new-entry.md", ["existing"]) in updates
    assert ("frontend/existing.md", ["new-entry"]) in updates
