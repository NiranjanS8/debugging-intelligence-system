from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
async def add_debug_entry(request: DebugAddRequest) -> DebugEntryResponse:
    try:
        result = await _get_service().ingest(request.raw_input)
        return result
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", extra={"operation": "add"})
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
