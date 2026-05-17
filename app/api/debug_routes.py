from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.ingestion.service import IngestionService
from app.models.debug_entry import DebugAddRequest, DebugEntryResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])

_service: IngestionService | None = None


def _get_service() -> IngestionService:
    global _service
    if _service is None:
        _service = IngestionService()
    return _service


@router.post("/add", response_model=DebugEntryResponse)
async def add_debug_entry(
    request: DebugAddRequest,
    background_tasks: BackgroundTasks,
) -> DebugEntryResponse:
    try:
        prepared = await _get_service().prepare_ingest(request.raw_input)
        task_id = prepared.response.projection_task_id
        if task_id:
            background_tasks.add_task(_get_service().process_projection_task, task_id)
        return prepared.response
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", extra={"operation": "add"})
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
