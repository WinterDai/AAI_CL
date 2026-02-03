"""Factory helpers for constructing LLM clients."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from llm_clients.anthropic_client import AnthropicMessagesClient
    from llm_clients.base import BaseLLMClient
    from llm_clients.openai_client import OpenAIChatClient
    from llm_clients.jedai_client import JedAIClient
except ImportError:
    from AutoGenChecker.llm_clients.anthropic_client import AnthropicMessagesClient
    from AutoGenChecker.llm_clients.base import BaseLLMClient
    from AutoGenChecker.llm_clients.openai_client import OpenAIChatClient
    from AutoGenChecker.llm_clients.jedai_client import JedAIClient


def create_llm_client(provider: str, **kwargs: Any) -> BaseLLMClient:
    """Instantiate an LLM client for the given provider string.
    
    Supported providers:
    - openai, gpt, gpt-4, gpt-4.1: OpenAI GPT models (requires OPENAI_API_KEY)
    - anthropic, claude, claude-3: Anthropic Claude models (requires ANTHROPIC_API_KEY)
    - jedai, cadence, internal: Cadence JEDAI internal API (uses LDAP auth, no external API key needed)
    
    Args:
        provider: LLM provider name
        **kwargs: Provider-specific options. Common ones:
            - model: Model name (will be mapped to default_model for some clients)
            - verbose: Enable debug output
    """
    # Map 'model' to 'default_model' for clients that use that parameter name
    if 'model' in kwargs:
        kwargs['default_model'] = kwargs.pop('model')

    normalized = provider.lower().strip()
    if normalized in {"openai", "gpt", "gpt-4", "gpt-4.1"}:
        return OpenAIChatClient(**kwargs)
    if normalized in {"anthropic", "claude", "claude-3"}:
        return AnthropicMessagesClient(**kwargs)
    if normalized in {"jedai", "cadence", "internal"}:
        # JEDAI verbose is off by default (use --verbose or verbose=True to enable)
        if 'verbose' not in kwargs:
            kwargs['verbose'] = False
        return JedAIClient(**kwargs)
    raise ValueError(f"Unsupported LLM provider: {provider}. Supported: openai, anthropic, jedai")
