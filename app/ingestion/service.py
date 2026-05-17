from __future__ import annotations

from app.ingestion.parser import DebugInputParser
from app.ingestion.structurer import DebugStructurer
from app.llm.factory import get_llm_provider
from app.markdown.generator import MarkdownGenerator
from app.markdown.storage import MarkdownStorage
from app.retrieval.service import RetrievalService
from app.models.debug_entry import DebugEntry, DebugEntryResponse
from app.utils.id_generator import generate_entry_id
from app.utils.text_processing import infer_category
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IngestionService:
    def __init__(self):
        self.parser = DebugInputParser()
        self.structurer = DebugStructurer(get_llm_provider())
        self.md_generator = MarkdownGenerator()
        self.md_storage = MarkdownStorage()
        self.retrieval = RetrievalService()

    async def ingest(self, raw_input: str) -> DebugEntryResponse:
        parsed = self.parser.parse(raw_input)
        structured = await self.structurer.structure(parsed)

        entry_id = generate_entry_id(structured.title, structured.root_cause)
        category = infer_category(structured.tech_stack, structured.tags)

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
            markdown_path=md_path,
        )

        # Index in ChromaDB for semantic search
        self.retrieval.index_entry(entry)

        # Find similar entries to return as suggestions
        similar = self.retrieval.find_similar(entry_id, top_k=3)

        logger.info(
            f"Ingested: {entry.title}",
            extra={"entry_id": entry_id, "operation": "ingest"},
        )

        return DebugEntryResponse(entry=entry, similar_entries=similar)
