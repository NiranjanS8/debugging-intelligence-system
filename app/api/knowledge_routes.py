from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.markdown.storage import MarkdownStorage
from app.retrieval.service import RetrievalService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

_retrieval_service: RetrievalService | None = None
_markdown_storage: MarkdownStorage | None = None


def _get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


def _get_markdown_storage() -> MarkdownStorage:
    global _markdown_storage
    if _markdown_storage is None:
        _markdown_storage = MarkdownStorage()
    return _markdown_storage


@router.get("/list")
async def list_knowledge_entries(category: str | None = None) -> dict:
    entries = _get_retrieval_service().list_entries(category=category)
    return {
        "entries": [
            {
                "id": entry.id,
                "title": entry.title,
                "category": entry.category,
                "confidence": entry.confidence,
                "tags": entry.tags,
                "tech_stack": entry.tech_stack,
                "markdown_path": entry.markdown_path,
                "related_ids": entry.related_ids,
            }
            for entry in entries
        ],
        "total_entries": len(entries),
    }


@router.get("/{entry_id}")
async def get_knowledge_entry(entry_id: str) -> dict:
    entry = _get_retrieval_service().get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Entry '{entry_id}' not found")

    markdown_content = None
    if entry.markdown_path:
        markdown_content = _get_markdown_storage().read(entry.markdown_path)

    return {
        "entry": entry.model_dump(),
        "markdown_content": markdown_content,
    }
