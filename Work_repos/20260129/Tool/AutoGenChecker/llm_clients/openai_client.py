"""OpenAI chat client implementation."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

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
    import openai  # type: ignore
except ImportError:  # pragma: no cover - descriptive error at runtime
    openai = None


class OpenAIChatClient(BaseLLMClient):
    """Thin wrapper around the OpenAI chat completion API."""

    _DEFAULT_SYSTEM = (
        "You are an expert VLSI implementation engineer who writes Python checkers."
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        default_model: str = "gpt-4.1",
        base_url: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        if openai is None:
            raise ImportError(
                "The openai package is required. Install it via 'pip install openai'."
            )

        super().__init__(default_model=default_model)
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY.")

        client_kwargs: Dict[str, Any] = {"api_key": self._api_key}
        if organization:
            client_kwargs["organization"] = organization
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = openai.OpenAI(**client_kwargs)
        self._system_prompt = system_prompt or self._DEFAULT_SYSTEM

    def complete(
        self, prompt: str, *, config: LLMCallConfig | None = None
    ) -> LLMResponse:  # type: ignore[override]
        resolved = self.resolve_config(config)
        response = self._client.chat.completions.create(
            model=resolved.model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=resolved.temperature,
            max_tokens=resolved.max_tokens,
            **resolved.extra_options,
        )

        message_obj = response.choices[0].message
        message = getattr(message_obj, "content", None) or message_obj.get("content", "")
        usage_obj = getattr(response, "usage", None)
        prompt_tokens = getattr(usage_obj, "prompt_tokens", None)
        completion_tokens = getattr(usage_obj, "completion_tokens", None)
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
            text=message,
            model=resolved.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usage=usage_dict,
        )
