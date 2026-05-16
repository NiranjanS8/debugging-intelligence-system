from __future__ import annotations

from app.config import get_settings, LLMProvider
from app.llm.base import BaseLLMProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)

_provider_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Return a cached LLM provider instance based on config."""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    settings = get_settings()
    provider_type = settings.llm_provider

    if provider_type == LLMProvider.GEMINI:
        from app.llm.gemini_provider import GeminiProvider
        _provider_instance = GeminiProvider()
        logger.info("LLM provider: Gemini")

    elif provider_type == LLMProvider.OPENAI:
        from app.llm.openai_provider import OpenAIProvider
        _provider_instance = OpenAIProvider()
        logger.info("LLM provider: OpenAI")

    else:
        from app.llm.fallback_provider import FallbackProvider
        _provider_instance = FallbackProvider()
        logger.info("LLM provider: Fallback (rule-based)")

    return _provider_instance
