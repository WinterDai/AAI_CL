"""Abstract LLM client interface for the checker agent."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from utils.models import LLMCallConfig, LLMResponse
except ImportError:
    from AutoGenChecker.utils.models import LLMCallConfig, LLMResponse


class BaseLLMClient(ABC):
    """Normalized interface around vendor specific SDKs."""

    def __init__(self, default_model: str | None = None) -> None:
        self._default_model = default_model

    @abstractmethod
    def complete(self, prompt: str, *, config: LLMCallConfig | None = None) -> LLMResponse:
        """Execute a single prompt-completion request."""

    def resolve_config(self, config: LLMCallConfig | None = None) -> LLMCallConfig:
        if config is None:
            return LLMCallConfig(model=self._default_model or "gpt-4.1")
        if not config.model and self._default_model:
            config.model = self._default_model
        return config
