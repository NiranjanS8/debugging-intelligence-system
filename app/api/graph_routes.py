from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.graph.service import GraphService
from app.models.graph import GraphNeighborhoodResponse, GraphSummaryResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph"])

_graph_service: GraphService | None = None


def _get_service() -> GraphService:
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service


@router.get("/summary", response_model=GraphSummaryResponse)
async def get_graph_summary() -> GraphSummaryResponse:
    try:
        return _get_service().get_summary()
    except Exception as exc:
        logger.error(f"Graph summary failed: {exc}", extra={"operation": "graph_summary"})
        raise HTTPException(status_code=500, detail=f"Graph summary failed: {str(exc)}")


@router.get("/entry/{entry_id}", response_model=GraphNeighborhoodResponse)
async def get_graph_entry(entry_id: str) -> GraphNeighborhoodResponse:
    try:
        return _get_service().get_entry_neighborhood(entry_id)
    except Exception as exc:
        logger.error(
            f"Graph entry lookup failed: {exc}",
            extra={"operation": "graph_entry", "entry_id": entry_id},
        )
        raise HTTPException(status_code=500, detail=f"Graph entry lookup failed: {str(exc)}")
