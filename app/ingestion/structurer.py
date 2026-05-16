from __future__ import annotations

from app.llm.base import BaseLLMProvider
from app.models.debug_entry import StructuredDebugData
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DebugStructurer:
    """Orchestrates LLM-based structuring of parsed debug text."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def structure(self, parsed_text: str) -> StructuredDebugData:
        logger.info("Structuring debug input", extra={"operation": "structure"})

        try:
            result = await self.provider.structure_debug_input(parsed_text)
            logger.info(
                f"Structured: {result.title}",
                extra={"operation": "structure", "confidence": result.confidence},
            )
            return result

        except Exception as e:
            logger.error(f"LLM structuring failed: {e}", extra={"operation": "structure"})
            raise
