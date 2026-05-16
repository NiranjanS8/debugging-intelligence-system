from __future__ import annotations

import re

from slugify import slugify

_FRONTEND_KEYWORDS = frozenset({
    "react", "vue", "angular", "svelte", "next", "nextjs", "nuxt",
    "javascript", "typescript", "css", "html", "dom", "browser",
    "webpack", "vite", "tailwind", "redux", "zustand",
})

_BACKEND_KEYWORDS = frozenset({
    "python", "java", "go", "rust", "node", "express", "fastapi",
    "django", "flask", "spring", "dotnet", "ruby", "rails",
    "graphql", "rest", "grpc", "celery", "rabbitmq", "kafka",
})

_INFRA_KEYWORDS = frozenset({
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "terraform",
    "ci", "cd", "jenkins", "github-actions", "nginx", "redis",
    "postgres", "mysql", "mongodb", "elasticsearch", "prometheus",
    "grafana", "helm", "linux", "networking",
})

_ERROR_PATTERNS = [
    r"(\w+Error):\s",
    r"(\w+Exception):\s",
    r"(\w+Exception)\b",
    r"(E\d{4})",
    r"(FATAL|PANIC|CRITICAL):",
]


def infer_category(tech_stack: list[str], tags: list[str]) -> str:
    """Infer KB category. Priority: frontend > backend > infra > uncategorized."""
    combined = {item.lower().strip() for item in tech_stack + tags}

    if combined & _FRONTEND_KEYWORDS:
        return "frontend"
    if combined & _BACKEND_KEYWORDS:
        return "backend"
    if combined & _INFRA_KEYWORDS:
        return "infra"
    return "uncategorized"


def normalize_text(text: str) -> str:
    text = text.strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def build_embedding_document(
    title: str,
    root_cause: str,
    fix: str,
    symptoms: list[str],
    tags: list[str] | None = None,
) -> str:
    """Concatenate key fields into a single string for embedding."""
    parts = [
        f"Title: {title}",
        f"Root Cause: {root_cause}",
        f"Fix: {fix}",
    ]

    if symptoms:
        parts.append(f"Symptoms: {', '.join(symptoms)}")

    if tags:
        parts.append(f"Tags: {', '.join(tags)}")

    return " | ".join(parts)


def generate_slug(title: str, max_length: int = 80) -> str:
    return slugify(title, max_length=max_length)


def extract_error_type(raw_text: str) -> str | None:
    """Extract the primary error type (e.g. TypeError, NullPointerException)."""
    for pattern in _ERROR_PATTERNS:
        match = re.search(pattern, raw_text)
        if match:
            return match.group(1)
    return None
