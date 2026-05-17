from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.models.projection import ProjectionTask
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectionOutbox:
    def __init__(self):
        self.base_path = get_settings().projection_queue_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def enqueue(self, task: ProjectionTask) -> str:
        path = self._task_path(task.task_id)
        path.write_text(task.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Queued projection task", extra={"task_id": task.task_id})
        return task.task_id

    def get(self, task_id: str) -> ProjectionTask | None:
        path = self._task_path(task_id)
        if not path.exists():
            return None
        return ProjectionTask.model_validate_json(path.read_text(encoding="utf-8"))

    def list_pending(self) -> list[ProjectionTask]:
        tasks: list[ProjectionTask] = []
        for path in sorted(self.base_path.glob("*.json")):
            task = ProjectionTask.model_validate_json(path.read_text(encoding="utf-8"))
            if task.status != "completed":
                tasks.append(task)
        return tasks

    def mark_running(self, task_id: str) -> ProjectionTask | None:
        task = self.get(task_id)
        if task is None:
            return None
        task.status = "running"
        task.attempts += 1
        task.updated_at = datetime.now(timezone.utc)
        self._save(task)
        return task

    def mark_completed(self, task_id: str) -> None:
        task = self.get(task_id)
        if task is None:
            return
        task.status = "completed"
        task.last_error = None
        task.updated_at = datetime.now(timezone.utc)
        self._save(task)

    def mark_failed(self, task_id: str, error: str) -> None:
        task = self.get(task_id)
        if task is None:
            return
        task.status = "failed"
        task.last_error = error[:1000]
        task.updated_at = datetime.now(timezone.utc)
        self._save(task)

    def _save(self, task: ProjectionTask) -> None:
        self._task_path(task.task_id).write_text(task.model_dump_json(indent=2), encoding="utf-8")

    def _task_path(self, task_id: str) -> Path:
        return self.base_path / f"{task_id}.json"
