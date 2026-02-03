"""Text helpers for prompt preparation and LLM output post-processing."""

from __future__ import annotations

import textwrap


def condense_whitespace(value: str) -> str:
    """Collapse consecutive blank lines to keep prompts compact."""

    lines = [line.rstrip() for line in value.splitlines()]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                compact.append("")
            blank = True
        else:
            compact.append(line)
            blank = False
    return "\n".join(compact).strip()


def truncate(value: str, *, max_chars: int = 1600) -> str:
    """Clip text to a safe length for inclusion inside prompts."""

    if len(value) <= max_chars:
        return value
    trailer = "\n...\n" if max_chars > 8 else ""
    return f"{value[: max_chars - len(trailer)]}{trailer}"


def indent_block(block: str, indent: int = 2) -> str:
    """Indent a text block for readability."""

    return textwrap.indent(block, " " * indent)
