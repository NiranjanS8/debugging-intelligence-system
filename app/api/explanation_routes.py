from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.explanations.service import DebugExplanationService
from app.models.explanation import DebugExplainRequest, DebugExplanationResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])

_service: DebugExplanationService | None = None


def _get_service() -> DebugExplanationService:
    global _service
    if _service is None:
        _service = DebugExplanationService()
    return _service


@router.post("/explain", response_model=DebugExplanationResponse)
async def explain_debug_issue(request: DebugExplainRequest) -> DebugExplanationResponse:
    try:
        return await _get_service().explain(request)
    except Exception as exc:
        logger.error(f"Debug explanation failed: {exc}", extra={"operation": "debug_explain"})
        raise HTTPException(status_code=500, detail=f"Debug explanation failed: {str(exc)}")
