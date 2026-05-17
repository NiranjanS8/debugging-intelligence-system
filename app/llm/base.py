from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.debug_entry import StructuredDebugData
from app.models.explanation import DebugExplanationResponse


class BaseLLMProvider(ABC):
    """Interface that all LLM providers must implement."""

    @abstractmethod
    async def structure_debug_input(self, raw_text: str) -> StructuredDebugData:
        """Convert raw debugging text into a structured debug entry."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and configured."""
        ...

    @abstractmethod
    async def explain_debug_issue(
        self,
        raw_text: str,
        retrieval_context: str,
    ) -> DebugExplanationResponse:
        """Generate a grounded debug explanation using retrieved context."""
        ...
