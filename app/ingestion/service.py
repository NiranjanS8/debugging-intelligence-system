from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

from app.ingestion.parser import DebugInputParser
from app.ingestion.structurer import DebugStructurer
from app.llm.factory import get_llm_provider
from app.markdown.generator import MarkdownGenerator
from app.markdown.storage import MarkdownStorage
from app.models.debug_entry import DebugEntry, DebugEntryResponse, SimilarEntry
from app.projections.service import ProjectionService
from app.retrieval.service import RetrievalService
from app.utils.id_generator import generate_entry_id
from app.utils.text_processing import infer_category
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PreparedIngestion(NamedTuple):
    response: DebugEntryResponse
    similar_entries: list[SimilarEntry]


class IngestionService:
    def __init__(self):
        self.parser = DebugInputParser()
        self.structurer = DebugStructurer(get_llm_provider())
        self.md_generator = MarkdownGenerator()
        self.md_storage = MarkdownStorage()
        self.retrieval = RetrievalService()
        self.projections = ProjectionService()

    async def prepare_ingest(self, raw_input: str) -> PreparedIngestion:
        parsed = self.parser.parse(raw_input)
        structured = await self.structurer.structure(parsed)

        entry_id = generate_entry_id(structured.title, structured.root_cause)
        category = infer_category(structured.tech_stack, structured.tags)
        duplicate = self.retrieval.find_duplicate_candidate(
            title=structured.title,
            root_cause=structured.root_cause,
            fix=structured.fix,
            symptoms=structured.symptoms,
            tags=structured.tags,
            tech_stack=structured.tech_stack,
        )
        now = datetime.now(timezone.utc)
        similar = self._suggest_similar_entries(structured, duplicate)

        markdown_content = self.md_generator.generate(structured)
        md_path = self.md_storage.save(
            entry_id=entry_id,
            title=structured.title,
            category=category,
            content=markdown_content,
        )

        entry = DebugEntry(
            id=entry_id,
            title=structured.title,
            symptoms=structured.symptoms,
            root_cause=structured.root_cause,
            fix=structured.fix,
            tags=structured.tags,
            tech_stack=structured.tech_stack,
            confidence=structured.confidence,
            raw_input=raw_input,
            category=category,
            created_at=now,
            updated_at=now,
            markdown_path=md_path,
        )

        task_id = self.projections.create_task_for_entry(entry, similar)

        logger.info(
            f"Primary record persisted: {entry.title}",
            extra={
                "entry_id": entry_id,
                "operation": "ingest_prepare",
                "is_duplicate": duplicate is not None,
                "duplicate_of": duplicate.id if duplicate else None,
                "projection_task_id": task_id,
            },
        )

        response = DebugEntryResponse(
            entry=entry,
            similar_entries=similar,
            is_duplicate=duplicate is not None,
            duplicate_of=duplicate.id if duplicate else None,
            duplicate_entry=duplicate,
            projection_task_id=task_id,
            projection_status="queued",
            message=(
                "Primary record persisted and projection queued. Likely semantic duplicate detected."
                if duplicate is not None
                else "Primary record persisted and projection queued."
            ),
        )
        return PreparedIngestion(response=response, similar_entries=similar)

    async def ingest(self, raw_input: str) -> DebugEntryResponse:
        prepared = await self.prepare_ingest(raw_input)
        self.projections.process_task(prepared.response.projection_task_id or "")
        task = self.projections.outbox.get(prepared.response.projection_task_id or "")
        if task is not None:
            prepared.response.projection_status = task.status
        return prepared.response

    def process_projection_task(self, task_id: str) -> bool:
        return self.projections.process_task(task_id)

    def _suggest_similar_entries(self, structured, duplicate) -> list[SimilarEntry]:
        results = self.retrieval.hybrid_search(
            query=" | ".join(
                [
                    structured.title,
                    structured.root_cause,
                    structured.fix,
                    " ".join(structured.symptoms),
                ]
            ),
            top_k=3,
            tags=structured.tags or None,
            tech_stack=structured.tech_stack or None,
        )
        similar_entries = [
            SimilarEntry(
                id=result.id,
                title=result.title,
                root_cause=result.root_cause,
                fix=result.fix,
                similarity_score=result.similarity_score,
                tags=result.tags,
            )
            for result in results
            if duplicate is None or result.id != duplicate.id
        ]
        return similar_entries[:3]
