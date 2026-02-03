"""Anthropic Claude client implementation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from llm_clients.base import BaseLLMClient
    from utils.models import LLMCallConfig, LLMResponse
except ImportError:
    from AutoGenChecker.llm_clients.base import BaseLLMClient
    from AutoGenChecker.utils.models import LLMCallConfig, LLMResponse

try:  # Optional dependency guard.
    import anthropic  # type: ignore
except ImportError:  # pragma: no cover - descriptive error raised at runtime
    anthropic = None


class AnthropicMessagesClient(BaseLLMClient):
    """Wrapper for the Anthropic messages API."""

    _DEFAULT_SYSTEM = (
        "You are an expert VLSI implementation engineer who writes Python checkers."
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        default_model: str = "claude-3-5-sonnet-20241022",
        base_url: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        if anthropic is None:
            raise ImportError(
                "The anthropic package is required. Install it via 'pip install anthropic'."
            )

        super().__init__(default_model=default_model)
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY.")

        client_kwargs = {"api_key": self._api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = anthropic.Anthropic(**client_kwargs)
        self._system_prompt = system_prompt or self._DEFAULT_SYSTEM

    def complete(
        self, prompt: str, *, config: LLMCallConfig | None = None
    ) -> LLMResponse:  # type: ignore[override]
        resolved = self.resolve_config(config)
        response = self._client.messages.create(
            model=resolved.model,
            max_tokens=resolved.max_tokens,
            temperature=resolved.temperature,
            system=self._system_prompt,
            messages=[{"role": "user", "content": prompt}],
            **resolved.extra_options,
        )

        text_parts = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(getattr(block, "text", ""))
        text = "".join(text_parts)

        usage_obj = getattr(response, "usage", None)
        prompt_tokens = getattr(usage_obj, "input_tokens", None)
        completion_tokens = getattr(usage_obj, "output_tokens", None)
        usage_dict = None
        if usage_obj is not None:
            for attr in ("model_dump", "to_dict"):
                maybe = getattr(usage_obj, attr, None)
                if callable(maybe):
                    usage_dict = maybe()
                    break
            if usage_dict is None and isinstance(usage_obj, dict):
                usage_dict = usage_obj

        return LLMResponse(
            text=text,
            model=resolved.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usage=usage_dict,
        )
