from __future__ import annotations

import re
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.markdown.storage import MarkdownStorage
from app.models.debug_entry import DebugEntry
from app.retrieval.linker import RetrievalLinker
from app.retrieval.service import RetrievalService
from app.utils.text_processing import infer_category


def _extract_section(content: str, header: str) -> str:
    pattern = rf"## {re.escape(header)}\n(.*?)(?=\n## |\n---|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_bullet_section(content: str, header: str) -> list[str]:
    block = _extract_section(content, header)
    values = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith("- "):
            values.append(line[2:].strip())
    return values


def _extract_inline_tags(content: str, header: str) -> list[str]:
    block = _extract_section(content, header)
    return [item.strip("` ").lower() for item in block.split(",") if item.strip()]


def _extract_confidence(content: str) -> float:
    match = re.search(r"\*Confidence:\s+(\d+)%\*", content)
    if not match:
        return 0.5
    return round(int(match.group(1)) / 100, 2)


def _extract_title(content: str) -> str:
    first_line = content.splitlines()[0].strip()
    return first_line.lstrip("# ").strip()


def _extract_entry_id(content: str, fallback: str) -> str:
    match = re.search(r"<!-- entry_id:\s*([a-zA-Z0-9_-]+)\s*-->", content)
    return match.group(1) if match else fallback


def main() -> None:
    storage = MarkdownStorage()
    retrieval = RetrievalService()
    linker = RetrievalLinker()

    markdown_paths = storage.list_entries()
    if not markdown_paths:
        print("No markdown entries found to reindex.")
        return

    print(f"Reindexing {len(markdown_paths)} markdown knowledge pages...")
    for path in markdown_paths:
        content = storage.read(path)
        if not content:
            continue

        title = _extract_title(content)
        root_cause = _extract_section(content, "Root Cause")
        fix = _extract_section(content, "Fix")
        symptoms = _extract_bullet_section(content, "Symptoms")
        tags = _extract_inline_tags(content, "Tags")
        tech_stack = _extract_inline_tags(content, "Tech Stack")
        entry_id = _extract_entry_id(content, path.replace("/", "-").replace(".md", ""))

        entry = DebugEntry(
            id=entry_id,
            title=title,
            symptoms=symptoms,
            root_cause=root_cause,
            fix=fix,
            tags=tags,
            tech_stack=tech_stack,
            confidence=_extract_confidence(content),
            category=infer_category(tech_stack, tags),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            markdown_path=path,
        )
        retrieval.upsert_entry(entry)
        print(f"- Reindexed {entry.id}: {entry.title}")

    retrieval.rebuild_search_index()
    print("Rebuilt BM25 search index.")

    relink_stats = linker.relink_all()
    print(
        f"Relinked wiki pages for {relink_stats['processed_entries']} entries "
        f"and updated {relink_stats['updated_pages']} markdown files."
    )
    print("Reindex complete.")


if __name__ == "__main__":
    main()
