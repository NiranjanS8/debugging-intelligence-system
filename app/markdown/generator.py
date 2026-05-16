from __future__ import annotations

from app.models.debug_entry import StructuredDebugData


class MarkdownGenerator:
    def generate(self, data: StructuredDebugData) -> str:
        sections = [f"# {data.title}", ""]

        if data.symptoms:
            sections.append("## Symptoms")
            for s in data.symptoms:
                sections.append(f"- {s}")
            sections.append("")

        sections.append("## Root Cause")
        sections.append(data.root_cause)
        sections.append("")

        sections.append("## Fix")
        sections.append(data.fix)
        sections.append("")

        if data.tags:
            sections.append("## Tags")
            sections.append(", ".join(f"`{t}`" for t in data.tags))
            sections.append("")

        if data.tech_stack:
            sections.append("## Tech Stack")
            sections.append(", ".join(f"`{t}`" for t in data.tech_stack))
            sections.append("")

        sections.append(f"---\n*Confidence: {data.confidence:.0%}*\n")

        return "\n".join(sections)
