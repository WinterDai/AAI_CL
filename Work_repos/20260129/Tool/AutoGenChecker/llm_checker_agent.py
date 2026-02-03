"""High-level orchestration for LLM-powered checker generation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

# Setup import path
_parent_dir = Path(__file__).parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from context_collectors import (
        BaseContextCollector,
        CheckerExampleCollector,
        TaskSpecCollector,
    )
    from llm_clients import BaseLLMClient, create_llm_client
    from prompt_templates import build_checker_prompt_v2 as build_checker_prompt
    from utils.models import (
        CheckerAgentRequest,
        ContextFragment,
        GeneratedChecker,
        LLMCallConfig,
    )
except ImportError:
    from AutoGenChecker.context_collectors import (
        BaseContextCollector,
        CheckerExampleCollector,
        TaskSpecCollector,
    )
    from AutoGenChecker.llm_clients import BaseLLMClient, create_llm_client
    from AutoGenChecker.prompt_templates import build_checker_prompt_v2 as build_checker_prompt
    from AutoGenChecker.utils.models import (
        CheckerAgentRequest,
        ContextFragment,
        GeneratedChecker,
        LLMCallConfig,
    )


class LLMCheckerAgent:
    """
    Generate checker stubs by combining project context with an LLM.
    
    Now using build_checker_prompt_v2 with DEVELOPER_TASK_PROMPTS.md v1.1.0:
    - BLOCK 1-4 structured instructions
    - Template Library v1.1.0 enforcement
    - Step 2.5 file analysis support
    """

    DEFAULT_INSTRUCTIONS = (
        "Follow the CHECKLIST BaseChecker conventions and Template Library v1.1.0.\n"
        "- Use WaiverHandlerMixin + OutputBuilderMixin (MANDATORY)\n"
        "- Implement all 4 type methods with build_complete_output()\n"
        "- Use validate_input_files() and raise ConfigurationError\n"
        "- Follow BLOCK 1-4 structure from DEVELOPER_TASK_PROMPTS.md"
    )

    def __init__(
        self,
        llm_client: BaseLLMClient,
        *,
        collectors: Sequence[BaseContextCollector] | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._collectors = list(collectors) if collectors else self._default_collectors()
        self._prompt_builder = build_checker_prompt
        self._last_prompt: str | None = None
        self._last_context: list[ContextFragment] = []

    def generate_checker(
        self,
        request: CheckerAgentRequest | dict[str, object],
        *,
        config: LLMCallConfig | None = None,
        instructions: str | None = None,
        extra_notes: Iterable[str] | None = None,
    ) -> GeneratedChecker:
        """Produce checker code using the configured LLM client."""

        normalized = self._normalize_request(request)
        context_fragments = self._gather_context(normalized)
        prompt = self._prompt_builder(
            normalized,
            context_fragments,
            instructions=instructions or self.DEFAULT_INSTRUCTIONS,
            extra_notes=extra_notes,
        )
        self._last_prompt = prompt

        response = self._llm_client.complete(prompt, config=config)
        code, notes = self._split_llm_output(response.text)
        return GeneratedChecker.from_response(
            checker_code=code,
            response=response,
            design_notes=notes,
        )

    def send_message(self, prompt: str, *, config: LLMCallConfig | None = None) -> str:
        """
        Send a simple message to the LLM and get the response text.
        
        This is a simplified interface for direct prompting, useful for
        code modifications and adjustments in the interactive workflow.
        
        Args:
            prompt: The prompt to send to the LLM
            config: Optional LLM call configuration
            
        Returns:
            The raw response text from the LLM
        """
        response = self._llm_client.complete(prompt, config=config)
        return response.text

    def get_last_prompt(self) -> str | None:
        """Return the most recent prompt sent to the LLM."""

        return self._last_prompt

    def get_last_context(self) -> list[ContextFragment]:
        """Return the most recent set of context fragments."""

        return list(self._last_context)

    def _gather_context(self, request: CheckerAgentRequest) -> list[ContextFragment]:
        fragments = []
        for collector in self._collectors:
            fragments.extend(collector.safe_collect(request))
        self._last_context = fragments
        return fragments

    def _normalize_request(
        self, request: CheckerAgentRequest | dict[str, object]
    ) -> CheckerAgentRequest:
        if isinstance(request, CheckerAgentRequest):
            return request
        if isinstance(request, dict):
            return CheckerAgentRequest(**request)
        msg = "Request must be CheckerAgentRequest or mapping."
        raise TypeError(msg)

    def _split_llm_output(self, text: str) -> tuple[str, str]:
        """
        Split LLM output into code and notes.
        
        Handles multiple formats:
        1. Raw code starting with #### (preferred)
        2. Code wrapped in ```python ... ```
        """
        # Check if output is raw code (starts with file header)
        if text.strip().startswith('####'):
            return text.strip(), ""
        
        # Try to find code block
        code_block = _CODE_BLOCK_RE.search(text)
        if not code_block:
            return text.strip(), ""

        code = code_block.group("code").strip()
        pre = text[: code_block.start()].strip()
        post = text[code_block.end() :].strip()
        notes = "\n\n".join(part for part in (pre, post) if part)
        return code, notes

    def _default_collectors(self) -> list[BaseContextCollector]:
        return [
            TaskSpecCollector(), 
            CheckerExampleCollector(
                max_examples=3,
                exclude_ai_generated=False,  # Include all examples (AI + human)
            )
        ]


def build_agent_from_provider(provider: str, **client_kwargs: object) -> LLMCheckerAgent:
    """Helper to bootstrap an agent with a named LLM provider."""

    client = create_llm_client(provider, **client_kwargs)
    return LLMCheckerAgent(client)


_CODE_BLOCK_RE = re.compile(
    r"```(?:python)?\n(?P<code>.*?)(?:```|$)",
    re.IGNORECASE | re.DOTALL,
)
