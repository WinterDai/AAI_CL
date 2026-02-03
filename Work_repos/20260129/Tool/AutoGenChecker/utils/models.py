"""Shared dataclasses for the AutoGenChecker LLM agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass(slots=True)
class ContextFragment:
    """Atomic unit of contextual knowledge that informs the LLM prompt."""

    title: str
    content: str
    source: str | None = None
    importance: str = "medium"


@dataclass(slots=True)
class CheckerAgentRequest:
    """User request describing the checker that needs to be generated."""

    module: str
    item_id: str
    item_name: str | None = None
    priority: str | None = None
    target_files: List[str] = field(default_factory=list)
    notes: str | None = None

    def brief(self) -> str:
        """Return a compact summary for logging and prompts."""

        meta: List[str] = [self.module, self.item_id]
        if self.item_name:
            meta.append(self.item_name)
        if self.priority:
            meta.append(f"priority={self.priority}")
        if self.target_files:
            meta.append(",".join(self.target_files))
        return " | ".join(meta)


@dataclass(slots=True)
class LLMCallConfig:
    """Runtime configuration for an individual LLM request."""

    max_tokens: int = 1800
    temperature: float = 0.2
    model: str = "gpt-4.1"
    extra_options: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    """Normalized response object produced by an LLM client."""

    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    usage: dict[str, int] | None = None


@dataclass(slots=True)
class GeneratedChecker:
    """Structured result returned by the checker agent."""

    checker_code: str
    design_notes: str
    llm_response: LLMResponse

    @classmethod
    def from_response(
        cls,
        checker_code: str,
        response: LLMResponse,
        design_notes: str | None = None,
    ) -> "GeneratedChecker":
        return cls(
            checker_code=checker_code,
            design_notes=design_notes or "",
            llm_response=response,
        )


def merge_fragments(*groups: Iterable[ContextFragment]) -> list[ContextFragment]:
    """Flatten multiple fragment iterables while preserving order."""

    merged: list[ContextFragment] = []
    for group in groups:
        merged.extend(group)
    return merged
