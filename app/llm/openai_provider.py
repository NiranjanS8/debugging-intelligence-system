from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.base import BaseLLMProvider
from app.models.debug_entry import StructuredDebugData
from app.models.explanation import DebugExplanationResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are a debugging intelligence engine. Given raw debugging input (stack traces, error logs, developer notes, fixes), extract structured information.

Return ONLY valid JSON with this exact schema:
{
  "title": "concise descriptive title",
  "symptoms": ["observable symptom 1", "symptom 2"],
  "root_cause": "the underlying cause of the bug",
  "fix": "the fix or workaround applied",
  "tags": ["tag1", "tag2"],
  "tech_stack": ["technology1", "technology2"],
  "confidence": 0.0 to 1.0
}

Rules:
- title: short, specific, starts with the tech/component name
- symptoms: what the developer observed (crashes, wrong output, etc.)
- root_cause: WHY it happened, not WHAT happened
- fix: the actual solution, be specific
- tags: lowercase descriptive categories
- tech_stack: lowercase technology names
- confidence: how confident you are in the structuring (0.0-1.0)
- Return raw JSON only, no markdown fences, no explanation"""

_EXPLAIN_PROMPT = """You are a debugging explanation engine.

Use the provided retrieval context as grounding evidence. Do not invent sources.
Return ONLY valid JSON with this schema:
{
  "summary": "short explanation",
  "probable_root_cause": "likely underlying cause",
  "recommended_fix": "most likely next fix",
  "reasoning": "why you think this, grounded in the retrieved evidence",
  "confidence": 0.0,
  "next_steps": ["step 1", "step 2"]
}
"""


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def structure_debug_input(self, raw_text: str) -> StructuredDebugData:
        logger.info("Structuring via OpenAI", extra={"operation": "llm_call"})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content.strip()
        data = json.loads(raw_json)
        return StructuredDebugData(**data)

    async def health_check(self) -> bool:
        try:
            settings = get_settings()
            return bool(settings.openai_api_key)
        except Exception:
            return False

    async def explain_debug_issue(
        self,
        raw_text: str,
        retrieval_context: str,
    ) -> DebugExplanationResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _EXPLAIN_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Raw debugging input:\n{raw_text}\n\n"
                        f"Retrieved context:\n{retrieval_context}"
                    ),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        return DebugExplanationResponse(**data)
