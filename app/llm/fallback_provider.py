from __future__ import annotations

import re
import json

from app.llm.base import BaseLLMProvider
from app.models.debug_entry import StructuredDebugData
from app.utils.text_processing import extract_error_type
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Patterns for extracting fix descriptions from raw text
_FIX_PATTERNS = [
    re.compile(r"(?:fix|fixed|solution|resolved|workaround)[:\s-]+(.+)", re.IGNORECASE),
    re.compile(r"(?:changed|replaced|switched|used|added)[:\s]+(.+)", re.IGNORECASE),
]

_CAUSE_PATTERNS = [
    re.compile(r"(?:cause|caused by|root cause|reason|because)[:\s-]+(.+)", re.IGNORECASE),
    re.compile(r"(?:forgot|missing|incorrect|wrong|invalid)[:\s]+(.+)", re.IGNORECASE),
]

_TECH_KEYWORDS = {
    "react", "vue", "angular", "next", "nextjs", "node", "express",
    "python", "django", "flask", "fastapi", "java", "spring",
    "javascript", "typescript", "go", "rust", "ruby", "rails",
    "docker", "kubernetes", "aws", "postgres", "redis", "mongodb",
    "graphql", "rest", "grpc", "webpack", "vite", "css", "html",
}


class FallbackProvider(BaseLLMProvider):
    """Rule-based structuring when no LLM API key is configured."""

    async def structure_debug_input(self, raw_text: str) -> StructuredDebugData:
        logger.info("Using fallback provider (rule-based extraction)")

        lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]

        error_type = extract_error_type(raw_text)
        title = self._extract_title(lines, error_type)
        symptoms = self._extract_symptoms(lines, error_type)
        root_cause = self._extract_match(_CAUSE_PATTERNS, raw_text) or self._infer_cause(lines)
        fix = self._extract_match(_FIX_PATTERNS, raw_text) or self._infer_fix(lines)
        tech_stack = self._extract_tech(raw_text)
        tags = self._build_tags(error_type, symptoms)

        return StructuredDebugData(
            title=title,
            symptoms=symptoms,
            root_cause=root_cause,
            fix=fix,
            tags=tags,
            tech_stack=tech_stack,
            confidence=0.4,
        )

    async def health_check(self) -> bool:
        return True

    def _extract_title(self, lines: list[str], error_type: str | None) -> str:
        if error_type:
            # Use the error line as title basis
            for line in lines:
                if error_type in line:
                    title = line[:120].strip()
                    if ":" in title:
                        return title.split(":", 1)[0] + " Error"
                    return title
            return f"{error_type} Debug Entry"

        # Use first meaningful line
        for line in lines:
            if len(line) > 10 and not line.startswith(("fix", "Fix", "FIX", "cause", "Cause")):
                return line[:120]

        return "Debug Entry"

    def _extract_symptoms(self, lines: list[str], error_type: str | None) -> list[str]:
        symptoms = []
        if error_type:
            symptoms.append(f"{error_type} encountered")

        for line in lines[:5]:
            lower = line.lower()
            if any(kw in lower for kw in ("crash", "fail", "error", "broken", "undefined", "null", "timeout")):
                if line not in symptoms and len(symptoms) < 5:
                    symptoms.append(line[:100])

        return symptoms or ["error encountered"]

    def _extract_match(self, patterns: list[re.Pattern], text: str) -> str | None:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                result = match.group(1).strip()
                if len(result) >= 3:
                    return result[:300]
        return None

    def _infer_cause(self, lines: list[str]) -> str:
        # If no explicit cause found, use the error line or a generic message
        for line in lines:
            if any(kw in line.lower() for kw in ("error", "exception", "traceback", "undefined")):
                return line[:200]
        return "root cause not identified from raw input"

    def _infer_fix(self, lines: list[str]) -> str:
        for line in lines:
            lower = line.lower()
            if any(kw in lower for kw in ("fix", "solved", "resolved", "changed", "updated")):
                return line[:200]
        return "fix not identified from raw input"

    def _extract_tech(self, text: str) -> list[str]:
        words = set(re.findall(r'\b\w+\b', text.lower()))
        return sorted(words & _TECH_KEYWORDS)

    def _build_tags(self, error_type: str | None, symptoms: list[str]) -> list[str]:
        tags = []
        if error_type:
            tags.append(error_type.lower())

        symptom_text = " ".join(symptoms).lower()
        tag_map = {
            "null": "null-error", "undefined": "undefined-error",
            "timeout": "timeout", "async": "async-issue",
            "crash": "crash", "memory": "memory-issue",
            "permission": "permissions", "auth": "auth-error",
        }
        for keyword, tag in tag_map.items():
            if keyword in symptom_text and tag not in tags:
                tags.append(tag)

        return tags or ["untagged"]
