"""
Developer Agent - LLM Client Implementation
Based on Agent_Development_Spec.md v1.1

Integrates with JEDAI LangChain for LLM calls.
References: Work/Agent/JEDAI/jedai_langchain.py

NOTE: Mock LLM has been removed. Only real JEDAI calls are supported.
Default model: claude-sonnet-4-5 (Claude Sonnet 4.5)

Available models (use --model to switch):
  - claude-sonnet-4-5    : Claude Sonnet 4.5 (default, recommended)
  - claude-opus-4        : Claude Opus 4
  - claude-3-7-sonnet    : Claude 3.7 Sonnet
  - azure-gpt-4o         : Azure GPT-4o
  - gemini-2-5-pro       : Gemini 2.5 Pro
  - deepseek-r1          : DeepSeek R1
"""
import sys
from pathlib import Path
from typing import Tuple, Any, List

# Add JEDAI path
JEDAI_PATH = Path(__file__).parent.parent / "JEDAI"
if str(JEDAI_PATH) not in sys.path:
    sys.path.insert(0, str(JEDAI_PATH))

from state import LLMConfig

# Default model: Claude Sonnet 4.5 (JEDAI name: claude-sonnet-4-5)
DEFAULT_MODEL = "claude-sonnet-4-5"

# Available models for user selection
AVAILABLE_MODELS = [
    ("claude-sonnet-4-5", "Claude Sonnet 4.5 (default, recommended)"),
    ("claude-opus-4", "Claude Opus 4"),
    ("claude-opus-4-1", "Claude Opus 4.1"),
    ("claude-3-7-sonnet", "Claude 3.7 Sonnet"),
    ("azure-gpt-4o", "Azure GPT-4o"),
    ("azure-gpt-5", "Azure GPT-5"),
    ("gemini-2-5-pro", "Gemini 2.5 Pro"),
    ("gemini-3-pro-preview", "Gemini 3 Pro Preview"),
    ("deepseek-r1-0528-maas", "DeepSeek R1"),
    ("llama-3-3-70b-instruct-maas", "Llama 3.3 70B"),
]


def list_available_models() -> List[Tuple[str, str]]:
    """Return list of available models with descriptions"""
    return AVAILABLE_MODELS


class LLMClient:
    """
    Unified LLM Client that uses JEDAI LangChain
    
    Default model: Claude Sonnet 4.5 (claude-sonnet-4-5)
    """
    
    def __init__(self, config: LLMConfig = None):
        """
        Initialize LLM Client
        
        Args:
            config: LLM configuration. If None, uses default JEDAI with Claude Sonnet 4.5
        """
        if config is None:
            # Default configuration: JEDAI with Claude Sonnet 4.5
            config = LLMConfig(
                provider="jedai",
                model=DEFAULT_MODEL,
                temperature=0.7,
                max_tokens=4096
            )
        self.config = config
        self._jedai = None
        self._llm = None
    
    def _get_jedai_client(self):
        """Get or create JEDAI LangChain client"""
        if self._jedai is None:
            try:
                from jedai_langchain import JedaiLangChain
                self._jedai = JedaiLangChain()
            except ImportError as e:
                raise ImportError(
                    f"Failed to import JEDAI LangChain: {e}\n"
                    "Make sure JEDAI modules are available at: {JEDAI_PATH}"
                )
        return self._jedai
    
    def _ensure_llm(self):
        """Ensure LLM is initialized"""
        if self._llm is None:
            jedai = self._get_jedai_client()
            self._llm = jedai.create_llm(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
        return self._llm
    
    def invoke(self, prompt: str) -> str:
        """
        Invoke LLM with a prompt and return the response
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response text from the LLM
        """
        if self.config.provider == "jedai":
            return self._invoke_jedai(prompt)
        elif self.config.provider == "openai":
            return self._invoke_openai(prompt)
        elif self.config.provider == "anthropic":
            return self._invoke_anthropic(prompt)
        elif self.config.provider == "azure":
            return self._invoke_azure(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    def _invoke_jedai(self, prompt: str) -> str:
        """Invoke JEDAI LLM (default)"""
        llm = self._ensure_llm()
        response = llm.invoke(prompt)
        return response.content
    
    def _invoke_openai(self, prompt: str) -> str:
        """Invoke OpenAI LLM"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI not installed. Run: pip install openai")
        
        client = OpenAI()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content
    
    def _invoke_anthropic(self, prompt: str) -> str:
        """Invoke Anthropic LLM"""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Anthropic not installed. Run: pip install anthropic")
        
        client = Anthropic()
        response = client.messages.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.content[0].text
    
    def _invoke_azure(self, prompt: str) -> str:
        """Invoke Azure OpenAI LLM"""
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("OpenAI not installed. Run: pip install openai")
        
        client = AzureOpenAI()
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        return response.choices[0].message.content


def get_llm_client(config: LLMConfig = None) -> Tuple[Any, dict]:
    """
    Create LLM client and call parameters based on configuration
    
    This function is kept for compatibility with the spec document.
    For new code, prefer using LLMClient class directly.
    
    Args:
        config: LLM configuration. If None, uses default JEDAI with Claude Sonnet 4.5
        
    Returns:
        Tuple of (client, call_params)
    """
    if config is None:
        config = LLMConfig(
            provider="jedai",
            model=DEFAULT_MODEL,
            temperature=0.7,
            max_tokens=4096
        )
    
    call_params = {
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens
    }
    
    if config.provider == "jedai":
        # Return JEDAI-compatible wrapper
        return _JedaiClientWrapper(config), call_params
    elif config.provider == "openai":
        from openai import OpenAI
        return OpenAI(), call_params
    elif config.provider == "anthropic":
        from anthropic import Anthropic
        return Anthropic(), call_params
    elif config.provider == "azure":
        from openai import AzureOpenAI
        return AzureOpenAI(), call_params
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


class _JedaiClientWrapper:
    """
    Wrapper to make JEDAI client compatible with OpenAI-style interface
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._jedai = None
        self._llm = None
    
    def _ensure_llm(self):
        """Ensure LLM is initialized"""
        if self._llm is None:
            from jedai_langchain import JedaiLangChain
            self._jedai = JedaiLangChain()
            self._llm = self._jedai.create_llm(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
    
    @property
    def chat(self):
        """Return self for OpenAI-style chat.completions.create() calls"""
        return self
    
    @property
    def completions(self):
        """Return self for OpenAI-style chat.completions.create() calls"""
        return self
    
    def create(self, messages, **kwargs):
        """
        OpenAI-compatible create method
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (ignored for JEDAI)
            
        Returns:
            OpenAI-compatible response object
        """
        self._ensure_llm()
        
        # Extract user message
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break
        
        # Invoke LLM
        response = self._llm.invoke(prompt)
        
        # Wrap in OpenAI-compatible response
        return _JedaiResponse(response.content)


class _JedaiResponse:
    """OpenAI-compatible response wrapper"""
    
    def __init__(self, content: str):
        self.choices = [_JedaiChoice(content)]


class _JedaiChoice:
    """OpenAI-compatible choice wrapper"""
    
    def __init__(self, content: str):
        self.message = _JedaiMessage(content)


class _JedaiMessage:
    """OpenAI-compatible message wrapper"""
    
    def __init__(self, content: str):
        self.content = content


def create_default_client() -> LLMClient:
    """
    Create default LLM client with Claude Sonnet 4.5
    
    Returns:
        LLMClient configured with JEDAI and claude-sonnet-4
    """
    return LLMClient(LLMConfig(
        provider="jedai",
        model=DEFAULT_MODEL,
        temperature=0.7,
        max_tokens=4096
    ))
