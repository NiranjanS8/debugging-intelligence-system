from __future__ import annotations

import hashlib


def generate_entry_id(title: str, root_cause: str) -> str:
    """12-char hex prefix of SHA-256(title::root_cause), deterministic."""
    canonical = f"{title.strip().lower()}::{root_cause.strip().lower()}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def generate_content_hash(content: str) -> str:
    """Full SHA-256 hex digest for duplicate/change detection."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
