from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.retrieval.service import RetrievalService
from app.models.query import DebugQueryRequest, DebugQueryResponse
from app.models.debug_entry import SimilarEntry
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])

_service: RetrievalService | None = None


def _get_service() -> RetrievalService:
    global _service
    if _service is None:
        _service = RetrievalService()
    return _service


@router.post("/query", response_model=DebugQueryResponse)
async def query_debug_entries(request: DebugQueryRequest) -> DebugQueryResponse:
    try:
        # Build ChromaDB where filter from optional fields
        where = _build_where_filter(request)

        results = _get_service().semantic_search(
            query=request.query,
            top_k=request.top_k,
            where=where,
        )

        # Apply confidence filter in-memory (simpler than ChromaDB compound where)
        if request.min_confidence is not None:
            results = [r for r in results if r.confidence >= request.min_confidence]

        return DebugQueryResponse(
            query=request.query,
            results=results,
            total_results=len(results),
        )

    except Exception as e:
        logger.error(f"Query failed: {e}", extra={"operation": "query"})
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/similar/{entry_id}", response_model=list[SimilarEntry])
async def get_similar_entries(entry_id: str, top_k: int = 5) -> list[SimilarEntry]:
    try:
        results = _get_service().find_similar(entry_id, top_k=top_k)
        if not results:
            raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found or no similar entries")
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity search failed: {e}", extra={"entry_id": entry_id})
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


def _build_where_filter(request: DebugQueryRequest) -> dict | None:
    """Build a ChromaDB where clause from optional filter fields."""
    conditions = []

    if request.tags:
        # Match entries containing any of the requested tags
        for tag in request.tags:
            conditions.append({"tags": {"$contains": tag}})

    if request.tech_stack:
        for tech in request.tech_stack:
            conditions.append({"tech_stack": {"$contains": tech}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
