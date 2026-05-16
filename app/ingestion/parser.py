from __future__ import annotations

import re

from app.utils.text_processing import normalize_text
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DebugInputParser:
    """Pre-processes raw debugging input before LLM structuring."""

    def parse(self, raw_input: str) -> str:
        text = normalize_text(raw_input)
        text = self._clean_ansi(text)
        text = self._trim_stack_trace(text)
        return text

    def _clean_ansi(self, text: str) -> str:
        return re.sub(r"\x1b\[[0-9;]*m", "", text)

    def _trim_stack_trace(self, text: str, max_frames: int = 15) -> str:
        """Keep only the first and last N frames if the trace is huge."""
        lines = text.splitlines()
        if len(lines) <= max_frames * 2:
            return text

        # Find stack trace boundaries (indented lines starting with "at " or "File ")
        trace_lines = []
        other_lines = []
        in_trace = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("at ", "File ", "Traceback")):
                in_trace = True
                trace_lines.append(line)
            elif in_trace and (stripped.startswith(("at ", "File ")) or not stripped):
                trace_lines.append(line)
            else:
                in_trace = False
                other_lines.append(line)

        if len(trace_lines) > max_frames * 2:
            trimmed = trace_lines[:max_frames] + [f"  ... ({len(trace_lines) - max_frames * 2} frames omitted)"] + trace_lines[-max_frames:]
            return "\n".join(other_lines + trimmed)

        return text
