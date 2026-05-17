from __future__ import annotations

from app.models.debug_entry import DebugEntry
from app.models.projection import ProjectionTask


def test_projection_outbox_round_trip(tmp_path, monkeypatch) -> None:
    class DummySettings:
        @property
        def projection_queue_path(self):
            return tmp_path

    monkeypatch.setattr("app.projections.outbox.get_settings", lambda: DummySettings())

    from app.projections.outbox import ProjectionOutbox

    outbox = ProjectionOutbox()
    task = ProjectionTask(
        task_id="abc123",
        entry=DebugEntry(id="bug1", title="Bug", root_cause="cause", fix="fix"),
    )
    outbox.enqueue(task)
    loaded = outbox.get("abc123")

    assert loaded is not None
    assert loaded.task_id == "abc123"
    assert loaded.status == "pending"


def test_projection_service_processes_task(monkeypatch) -> None:
    processed: list[str] = []

    class DummyOutbox:
        def __init__(self):
            self.task = ProjectionTask(
                task_id="task1",
                entry=DebugEntry(id="bug1", title="Bug", root_cause="cause", fix="fix"),
            )

        def mark_running(self, task_id: str):
            self.task.status = "running"
            self.task.attempts += 1
            return self.task

        def mark_completed(self, task_id: str):
            processed.append("completed")

        def mark_failed(self, task_id: str, error: str):
            processed.append("failed")

    class DummyRetrieval:
        def index_entry(self, entry):
            processed.append("indexed")

    class DummyLinker:
        def link_entry(self, entry, similar_entries):
            processed.append("linked")

    class DummyGraph:
        def sync_entry(self, entry, similar_entries):
            processed.append("graphed")

    monkeypatch.setattr("app.projections.service.ProjectionOutbox", DummyOutbox)
    monkeypatch.setattr("app.projections.service.RetrievalService", DummyRetrieval)
    monkeypatch.setattr("app.projections.service.RetrievalLinker", DummyLinker)
    monkeypatch.setattr("app.projections.service.GraphService", DummyGraph)

    from app.projections.service import ProjectionService

    service = ProjectionService()
    assert service.process_task("task1") is True
    assert processed == ["indexed", "linked", "graphed", "completed"]
