from __future__ import annotations

import json

from google import genai

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


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def structure_debug_input(self, raw_text: str) -> StructuredDebugData:
        logger.info("Structuring via Gemini", extra={"operation": "llm_call"})

        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{_SYSTEM_PROMPT}\n\nRaw debugging input:\n{raw_text}",
        )

        raw_json = response.text.strip()
        # Strip markdown fences if the model wraps them anyway
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[1]
            raw_json = raw_json.rsplit("```", 1)[0]

        data = json.loads(raw_json)
        return StructuredDebugData(**data)

    async def health_check(self) -> bool:
        try:
            settings = get_settings()
            return bool(settings.gemini_api_key)
        except Exception:
            return False

    async def explain_debug_issue(
        self,
        raw_text: str,
        retrieval_context: str,
    ) -> DebugExplanationResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                f"{_EXPLAIN_PROMPT}\n\n"
                f"Raw debugging input:\n{raw_text}\n\n"
                f"Retrieved context:\n{retrieval_context}"
            ),
        )
        raw_json = response.text.strip()
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[1]
            raw_json = raw_json.rsplit("```", 1)[0]
        data = json.loads(raw_json)
        return DebugExplanationResponse(**data)
