from __future__ import annotations

from app.graph.service import GraphService
from app.models.projection import ProjectionTask
from app.projections.outbox import ProjectionOutbox
from app.retrieval.linker import RetrievalLinker
from app.retrieval.service import RetrievalService
from app.utils.id_generator import generate_content_hash
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectionService:
    def __init__(self):
        self.outbox = ProjectionOutbox()
        self.retrieval = RetrievalService()
        self.linker = RetrievalLinker()
        self.graph = GraphService()

    def create_task(self, task: ProjectionTask) -> str:
        return self.outbox.enqueue(task)

    def create_task_for_entry(self, entry, similar_entries) -> str:
        task_id = generate_content_hash(f"{entry.id}:{entry.updated_at.isoformat()}")[:16]
        task = ProjectionTask(task_id=task_id, entry=entry, similar_entries=similar_entries)
        return self.create_task(task)

    def process_task(self, task_id: str) -> bool:
        task = self.outbox.mark_running(task_id)
        if task is None:
            return False

        try:
            self.retrieval.index_entry(task.entry)
            self.linker.link_entry(task.entry, task.similar_entries)
            self.graph.sync_entry(task.entry, task.similar_entries)
            self.outbox.mark_completed(task_id)
            logger.info("Completed projection task", extra={"task_id": task_id, "entry_id": task.entry.id})
            return True
        except Exception as exc:
            self.outbox.mark_failed(task_id, str(exc))
            logger.error(
                f"Projection task failed: {exc}",
                extra={"task_id": task_id, "entry_id": task.entry.id, "operation": "projection"},
            )
            return False

    def process_pending(self, limit: int | None = None) -> dict[str, int]:
        tasks = self.outbox.list_pending()
        if limit is not None:
            tasks = tasks[:limit]

        processed = 0
        succeeded = 0
        failed = 0
        for task in tasks:
            processed += 1
            if self.process_task(task.task_id):
                succeeded += 1
            else:
                failed += 1
        return {"processed": processed, "succeeded": succeeded, "failed": failed}
