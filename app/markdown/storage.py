from __future__ import annotations

import re
from pathlib import Path

from app.config import get_settings
from app.models.debug_entry import SimilarEntry
from app.utils.text_processing import generate_slug
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownStorage:
    def __init__(self):
        self.base_path = get_settings().knowledge_base_path

    def save(self, entry_id: str, title: str, category: str, content: str) -> str:
        """Save markdown to knowledge_base/{category}/{slug}.md. Returns relative path."""
        slug = generate_slug(title)
        filename = f"{slug}.md"
        dir_path = self.base_path / category
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / filename

        # Append ID reference at the bottom
        content_with_ref = content.rstrip() + f"\n\n<!-- entry_id: {entry_id} -->\n"
        file_path.write_text(content_with_ref, encoding="utf-8")

        rel_path = f"{category}/{filename}"
        logger.info(f"Saved markdown: {rel_path}", extra={"entry_id": entry_id})
        return rel_path

    def read(self, relative_path: str) -> str | None:
        file_path = self.base_path / relative_path
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None

    def list_entries(self, category: str | None = None) -> list[str]:
        """List all markdown file paths, optionally filtered by category."""
        if category:
            search_path = self.base_path / category
            if not search_path.exists():
                return []
            return [f"{category}/{f.name}" for f in search_path.glob("*.md")]

        results = []
        for subdir in ("frontend", "backend", "infra", "uncategorized"):
            dir_path = self.base_path / subdir
            if dir_path.exists():
                results.extend(f"{subdir}/{f.name}" for f in dir_path.glob("*.md"))
        return results

    def update_related_links(
        self,
        relative_path: str,
        related_entries: list[SimilarEntry],
    ) -> None:
        existing = self.read(relative_path)
        if existing is None:
            return

        related_section = self._build_related_section(related_entries)
        entry_id_match = re.search(r"\n<!-- entry_id: .*? -->\s*$", existing, re.DOTALL)
        entry_id_block = entry_id_match.group(0).strip() if entry_id_match else ""
        body = re.sub(
            r"\n## Related Entries\n.*?(?=\n<!-- entry_id:|\Z)",
            "\n",
            existing,
            flags=re.DOTALL,
        ).rstrip()

        parts = [body]
        if related_section:
            parts.append(related_section)
        if entry_id_block:
            parts.append(entry_id_block)

        file_path = self.base_path / relative_path
        file_path.write_text("\n\n".join(part for part in parts if part).rstrip() + "\n", encoding="utf-8")

    def find_by_entry_id(self, entry_id: str) -> str | None:
        marker = f"<!-- entry_id: {entry_id} -->"
        for relative_path in self.list_entries():
            content = self.read(relative_path)
            if content and marker in content:
                return relative_path
        return None

    def _build_related_section(self, related_entries: list[SimilarEntry]) -> str:
        if not related_entries:
            return ""

        lines = ["## Related Entries"]
        for entry in related_entries:
            slug = generate_slug(entry.title)
            lines.append(f"- [[{slug}|{entry.title}]] ({entry.id})")
        return "\n".join(lines)
