from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.analytics.service import AnalyticsService
from app.clustering.service import ClusteringService
from app.models.analytics import AnalyticsSummary, ClusterResponse, FailurePatternResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

_analytics_service: AnalyticsService | None = None
_clustering_service: ClusteringService | None = None


def _get_analytics_service() -> AnalyticsService:
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service


def _get_clustering_service() -> ClusteringService:
    global _clustering_service
    if _clustering_service is None:
        _clustering_service = ClusteringService()
    return _clustering_service


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary() -> AnalyticsSummary:
    try:
        return _get_analytics_service().get_summary()
    except Exception as e:
        logger.error(f"Analytics summary failed: {e}", extra={"operation": "analytics_summary"})
        raise HTTPException(status_code=500, detail=f"Analytics summary failed: {str(e)}")


@router.get("/patterns", response_model=FailurePatternResponse)
async def get_patterns(limit: int = 5) -> FailurePatternResponse:
    try:
        return _get_analytics_service().get_failure_patterns(limit=limit)
    except Exception as e:
        logger.error(f"Failure pattern analysis failed: {e}", extra={"operation": "analytics_patterns"})
        raise HTTPException(status_code=500, detail=f"Failure pattern analysis failed: {str(e)}")


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_entries(category: str | None = None) -> ClusterResponse:
    try:
        return _get_clustering_service().cluster_entries(category=category)
    except Exception as e:
        logger.error(f"Clustering failed: {e}", extra={"operation": "analytics_cluster"})
        raise HTTPException(status_code=500, detail=f"Clustering failed: {str(e)}")
