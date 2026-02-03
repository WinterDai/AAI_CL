"""JEDAI (Cadence Internal) LLM client implementation.

This client uses Cadence's internal JEDAI API with LDAP authentication,
eliminating the need for external API keys.

Features:
- Auto-detects DPC vs non-DPC environment
- Uses LDAP authentication (your Cadence credentials)
- Supports Claude Opus 4, Claude Sonnet 4, Gemini 2.5 Pro/Flash
- Automatic URL fallback for reliability
"""

from __future__ import annotations

import getpass
import json
import os
import re
import socket
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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

try:
    import requests
except ImportError:
    requests = None


# Available JEDAI models (Auto-generated from API - 37 models total)
JEDAI_MODELS = {
    # GEMINI models
    "gemini-2-5-pro": {
        "name": "Gemini 2.5 Pro",
        "family": "GEMINI",
        "location": "us-central1",
        "deployment": "gemini-2.5-pro",
    },
    "gemini-2-5-flash": {
        "name": "Gemini 2.5 Flash",
        "family": "GEMINI",
        "location": "us-central1",
        "deployment": "gemini-2.5-flash",
    },
    "gemini-2-5-flash-lite": {
        "name": "Gemini 2.5 Flash Lite",
        "family": "GEMINI",
        "location": "us-central1",
        "deployment": "gemini-2.5-flash-lite",
    },
    "gemini-1-5-pro": {
        "name": "Gemini 1.5 Pro",
        "family": "GEMINI",
        "location": "us-central1",
        "deployment": "gemini-1.5-pro",
    },
    # Claude models
    "claude-sonnet-4-5": {
        "name": "Claude Sonnet 4.5",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-sonnet-4-5",
    },
    "claude-sonnet-4": {
        "name": "Claude Sonnet 4",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-sonnet-4",
    },
    "claude-haiku-4-5": {
        "name": "Claude Haiku 4.5",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-haiku-4-5",
    },
    "claude-opus-4-1": {
        "name": "Claude Opus 4.1",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-opus-4-1",
    },
    "claude-opus-4": {
        "name": "Claude Opus 4",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-opus-4",
    },
    "claude-3-7-sonnet": {
        "name": "Claude 3.7 Sonnet",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-3-7-sonnet",
    },
    "claude-3-5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-3-5-sonnet",
    },
    "claude-3-opus": {
        "name": "Claude 3 Opus",
        "family": "Claude",
        "location": "us-east5",
        "deployment": "claude-3-opus",
    },
    # Meta-Llama models
    "meta-llama-3-1-8b-instruct": {
        "name": "Meta Llama 3.1 8B Instruct",
        "family": "Meta-Llama",
        "location": "us-central1",
        "deployment": "meta/llama-3.1-8b-instruct-maas",
    },
    "meta-llama-3-1-70b-instruct": {
        "name": "Meta Llama 3.1 70B Instruct",
        "family": "Meta-Llama",
        "location": "us-central1",
        "deployment": "meta/llama-3.1-70b-instruct-maas",
    },
    "meta-llama-3-1-405b-instruct": {
        "name": "Meta Llama 3.1 405B Instruct",
        "family": "Meta-Llama",
        "location": "us-central1",
        "deployment": "meta/llama-3.1-405b-instruct-maas",
    },
    "meta-llama-3-3-70b-instruct": {
        "name": "Meta Llama 3.3 70B Instruct",
        "family": "Meta-Llama",
        "location": "us-central1",
        "deployment": "meta/llama-3.3-70b-instruct-maas",
    },
    "meta-llama-4-scout-17b": {
        "name": "Meta Llama 4 Scout 17B",
        "family": "Meta-Llama",
        "location": "us-east5",
        "deployment": "meta/llama-4-scout-17b-16e-instruct-maas",
    },
    "meta-llama-4-maverick-17b": {
        "name": "Meta Llama 4 Maverick 17B",
        "family": "Meta-Llama",
        "location": "us-east5",
        "deployment": "meta/llama-4-maverick-17b-128e-instruct-maas",
    },
    # Qwen models
    "qwen3-coder-480b": {
        "name": "Qwen3 Coder 480B",
        "family": "Qwen",
        "location": "us-south1",
        "deployment": "qwen/qwen3-coder-480b-a35b-instruct-maas",
    },
    "qwen3-235b-instruct": {
        "name": "Qwen3 235B Instruct",
        "family": "Qwen",
        "location": "us-south1",
        "deployment": "qwen/qwen3-235b-a22b-instruct-2507-maas",
    },
    # DeepSeek models
    "deepseek-r1": {
        "name": "DeepSeek R1",
        "family": "DeepSeek",
        "location": "us-central1",
        "deployment": "deepseek-ai/deepseek-r1-0528-maas",
    },
    "deepseek-v3-1": {
        "name": "DeepSeek V3.1",
        "family": "DeepSeek",
        "location": "us-central1",
        "deployment": "deepseek-ai/deepseek-v3.1-maas",
    },
    # Azure OpenAI models (require Azure-specific parameters)
    "azure-gpt-4o": {
        "name": "Azure GPT-4o",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "gpt-4o",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    "azure-o4-mini": {
        "name": "Azure o4-mini",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "o4-mini",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    "azure-gpt-5": {
        "name": "Azure GPT-5",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "gpt-5",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    "azure-gpt-5-mini": {
        "name": "Azure GPT-5 Mini",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "gpt-5-mini",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    "azure-gpt-5-2": {
        "name": "Azure GPT-5.2",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "gpt-5-2",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    "azure-gpt-4-vision": {
        "name": "Azure GPT-4 Vision",
        "family": "AzureOpenAI",
        "location": "westus",
        "deployment": "rnd01-gpt4-vision",
        "endpoint": "https://llmtest01-westus.openai.azure.com",
    },
    "azure-gpt-4-turbo": {
        "name": "Azure GPT-4 Turbo",
        "family": "AzureOpenAI",
        "location": "eastus2",
        "deployment": "gpt-4-turbo",
        "endpoint": "https://llmtest01-eastus2.openai.azure.com",
    },
    # OnPremise models
    "onprem-gpt-oss-120b": {
        "name": "On-Prem GPT OSS 120B",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_openai/gpt-oss-120b",
    },
    "onprem-gpt-oss-120b-sj": {
        "name": "On-Prem GPT OSS 120B (SJ)",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_sj_openai/gpt-oss-120b",
    },
    "onprem-gpt-oss-20b": {
        "name": "On-Prem GPT OSS 20B",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_openai/gpt-oss-20b",
    },
    "onprem-llama-3-1-chat": {
        "name": "On-Prem Llama 3.1 Chat",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_llama3.1_JEDAI_MODEL_CHAT_2",
    },
    "onprem-llama-3-3-chat": {
        "name": "On-Prem Llama 3.3 Chat",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_llama3.3_JEDAI_MODEL_CHAT_2",
    },
    "onprem-qwen3-32b": {
        "name": "On-Prem Qwen3 32B",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_Qwen3-32B",
    },
    "onprem-llama-3-3-nemotron-49b": {
        "name": "On-Prem Llama 3.3 Nemotron 49B",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_nvidia/llama-3_3-nemotron-super-49b-v1_5",
    },
    "onprem-gpt-oss-70b": {
        "name": "On-Prem GPT OSS 70B",
        "family": "OnPremise",
        "location": "local",
        "deployment": "on_prem_openai/gpt-oss-70b",
    },
}

# Model aliases for convenience
MODEL_ALIASES = {
    # Gemini
    "gemini": "gemini-2-5-pro",
    "gemini-pro": "gemini-2-5-pro",
    "gemini-flash": "gemini-2-5-flash",
    # Claude
    "claude": "claude-opus-4",
    "opus": "claude-opus-4",
    "sonnet": "claude-sonnet-4",
    "haiku": "claude-haiku-4-5",
    # Llama
    "llama": "meta-llama-3-3-70b-instruct",
    "llama-3": "meta-llama-3-3-70b-instruct",
    "llama-4": "meta-llama-4-scout-17b",
    # Qwen
    "qwen": "qwen3-coder-480b",
    # DeepSeek
    "deepseek": "deepseek-v3-1",
    "deepseek-r1": "deepseek-r1",
    # Azure OpenAI
    "gpt-4o": "azure-gpt-4o",
    "gpt-5": "azure-gpt-5",
    "gpt-5-mini": "azure-gpt-5-mini",
    "gpt-5-2": "azure-gpt-5-2",
    "o4-mini": "azure-o4-mini",
    "gpt-4-vision": "azure-gpt-4-vision",
    # On-Premise
    "onprem-gpt": "onprem-gpt-oss-120b",
    "onprem-llama": "onprem-llama-3-3-chat",
}


def detect_environment() -> bool:
    """Detect if running in DPC or non-DPC environment."""
    hostname = socket.gethostname()

    # Extended DPC patterns based on common Cadence hostname patterns
    dpc_patterns = [
        "dpc", "nfdpc", "ssgdpc", "atl", "cadence.com",
        "sjc", "aus", "rtp", "bng", "kor", "jpn",
        "ssg", "nf", "ip", "da", "rmpipg",
    ]

    # Check hostname patterns
    is_dpc = any(pattern in hostname.lower() for pattern in dpc_patterns)

    # Additional environment variable checks
    if not is_dpc:
        env_indicators = [
            os.environ.get("CADENCE_HOME"),
            os.environ.get("CDS_HOME"),
            os.environ.get("CADENCE_ROOT"),
            os.environ.get("CDS_ROOT"),
        ]
        is_dpc = any(indicator for indicator in env_indicators)

    return is_dpc


def get_jedai_url() -> str:
    """Get appropriate JEDAI URL based on environment."""
    # Try the new working URLs first
    return "http://jedai-ai.cadence.com:5668"


def get_all_jedai_urls() -> list[str]:
    """Get all possible JEDAI URLs for fallback."""
    return [
        # New working URLs (priority)
        "http://jedai-ai.cadence.com:5668",
        "https://jedai-ai:2513",
        # Legacy URLs (fallback)
        "http://ssgdpc-jedai.cadence.com:5000",
        "http://jedai.cadence.com:5000",
        "http://sjf-dsgdspr-084.cadence.com:5668",
        "http://sjc-dsgdspr-084.cadence.com:5668",
        "http://rmpipg302.cadence.com:5668",
    ]


class JedAIClient(BaseLLMClient):
    """
    Wrapper for Cadence JEDAI internal LLM API.

    Uses LDAP authentication - no external API keys required.
    Automatically detects DPC vs non-DPC environment.
    """

    _DEFAULT_SYSTEM = (
        "You are an expert VLSI implementation engineer who writes Python checkers."
    )

    def __init__(
        self,
        *,
        default_model: str = "claude-opus-4",
        jedai_url: str | None = None,
        system_prompt: str | None = None,
        username: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        verbose: bool = False,
    ) -> None:
        """
        Initialize JEDAI client.

        Args:
            default_model: Default model to use (claude-opus-4, gemini-2-5-pro, etc.)
            jedai_url: Override auto-detected JEDAI URL
            system_prompt: Custom system prompt for the LLM
            username: LDAP username (default: current system user or from .env)
            password: LDAP password (will prompt if not provided and no token)
            access_token: Pre-authenticated JEDAI access token (from .env)
            verbose: Print debug information
        """
        if requests is None:
            raise ImportError(
                "The requests package is required. Install it via 'pip install requests'."
            )

        # Resolve model aliases
        resolved_model = MODEL_ALIASES.get(default_model, default_model)
        if resolved_model not in JEDAI_MODELS:
            available = ", ".join(JEDAI_MODELS.keys())
            raise ValueError(
                f"Unknown model: {default_model}. Available: {available}"
            )

        super().__init__(default_model=resolved_model)

        # Load credentials from environment variables if not provided
        self._load_env_credentials()
        
        self._jedai_url = jedai_url or os.environ.get("JEDAI_URL") or get_jedai_url()
        self._system_prompt = system_prompt or self._DEFAULT_SYSTEM
        self._username = username or os.environ.get("JEDAI_USERNAME") or getpass.getuser()
        self._password = password or os.environ.get("JEDAI_PASSWORD")
        self._access_token: str | None = access_token or os.environ.get("JEDAI_ACCESS_TOKEN")
        self._working_url: str | None = None
        self._verbose = verbose

        # Track if we've printed init message (to avoid repeats)
        self._init_printed = False
        
        # Always print init info once (brief, single line)
        self._print_init_info(resolved_model)

    def _print_init_info(self, model: str) -> None:
        """Print initialization info once."""
        if not self._init_printed:
            model_info = JEDAI_MODELS.get(model, {})
            print(f"🌐 JEDAI: {model_info.get('name', model)} @ {self._jedai_url}")
            self._init_printed = True

    def _load_env_credentials(self) -> None:
        """Load credentials from .env file if available."""
        try:
            # Try to find .env in config directory
            config_dir = Path(__file__).parent.parent / "config"
            env_file = config_dir / ".env"
            
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if value and key not in os.environ:
                                os.environ[key] = value
        except Exception:
            # Silently fail - environment variable loading is optional
            pass

    def _ensure_authenticated(self) -> Tuple[str, str]:
        """Ensure we have a valid access token, authenticate if needed."""
        # If we already have a token and working URL, reuse them
        if self._access_token and self._working_url:
            # Try to verify the token is still valid
            if self._verify_token(self._access_token, self._working_url):
                return self._access_token, self._working_url
            else:
                # Token expired, clear it and re-authenticate
                if self._verbose:
                    print("⚠️ Token expired, re-authenticating...")
                self._access_token = None
                self._working_url = None
        
        # If we have a token but no working URL, try to find a working URL
        if self._access_token and not self._working_url:
            urls_to_try = [self._jedai_url] + [
                url for url in get_all_jedai_urls() if url != self._jedai_url
            ]
            for url in urls_to_try:
                if self._verify_token(self._access_token, url):
                    self._working_url = url
                    if self._verbose:
                        print(f"✅ Using saved token with URL: {url}")
                    return self._access_token, self._working_url
            # Token invalid for all URLs, clear it
            if self._verbose:
                print("⚠️ Saved token is invalid, re-authenticating...")
            self._access_token = None

        # Get password if not provided and no token available
        if not self._password:
            self._password = getpass.getpass(
                f"JEDAI Password for {self._username}: "
            )

        # Try to authenticate with fallback URLs
        urls_to_try = [self._jedai_url] + [
            url for url in get_all_jedai_urls() if url != self._jedai_url
        ]

        for i, url in enumerate(urls_to_try):
            try:
                if i > 0 and self._verbose:
                    print(f"🔄 Trying fallback URL: {url}")

                response = requests.post(
                    f"{url}/api/v1/security/login",
                    headers={"Content-Type": "application/json"},
                    json={
                        "username": self._username,
                        "password": self._password,
                        "provider": "LDAP",
                    },
                    timeout=15,
                )

                if response.status_code == 200:
                    self._access_token = response.json()["access_token"]
                    self._working_url = url
                    if self._verbose:
                        print(f"✅ Authenticated to JEDAI: {url}")
                    
                    # Optionally save token to .env for future use
                    self._save_token_to_env()
                    
                    return self._access_token, self._working_url
                else:
                    if self._verbose:
                        print(f"❌ Login failed for {url}: {response.status_code}")

            except requests.exceptions.RequestException as e:
                if self._verbose:
                    print(f"❌ Connection failed for {url}: {str(e)}")
                continue

        raise ConnectionError(
            f"Failed to authenticate to JEDAI. Tried: {', '.join(urls_to_try)}"
        )

    def _verify_token(self, token: str, url: str) -> bool:
        """
        Verify if an access token is still valid.
        
        Args:
            token: The access token to verify
            url: The JEDAI URL to test against
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Try a lightweight API call to verify token
            response = requests.get(
                f"{url}/api/v1/security/user",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def _save_token_to_env(self) -> None:
        """
        Save the current access token and password to .env file for persistence.
        This allows automatic re-authentication without prompting for password.
        """
        try:
            config_dir = Path(__file__).parent.parent / "config"
            env_file = config_dir / ".env"
            
            # Read existing content
            existing_content = {}
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            existing_content[key.strip()] = value.strip()
            
            # Update with new token and credentials
            existing_content["JEDAI_ACCESS_TOKEN"] = f'"{self._access_token}"'
            existing_content["JEDAI_USERNAME"] = f'"{self._username}"'
            if self._working_url:
                existing_content["JEDAI_URL"] = f'"{self._working_url}"'
            
            # Save password for automatic re-authentication when token expires
            # WARNING: Password is stored in plaintext. Keep .env file secure!
            if self._password:
                existing_content["JEDAI_PASSWORD"] = f'"{self._password}"'
            
            # Write back
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# JEDAI Authentication Configuration\n")
                f.write("# Auto-generated by jedai_client.py\n")
                f.write("# WARNING: Contains credentials - keep this file secure!\n\n")
                for key, value in existing_content.items():
                    f.write(f"{key}={value}\n")
            
            if self._verbose:
                print(f"💾 Token and credentials saved to {env_file}")
                
        except Exception as e:
            # Don't fail if we can't save - just log if verbose
            if self._verbose:
                print(f"⚠️  Could not save credentials: {e}")

    def complete(
        self, prompt: str, *, config: LLMCallConfig | None = None
    ) -> LLMResponse:
        """
        Execute a completion request to JEDAI.

        Args:
            prompt: The user prompt to send
            config: Optional LLM configuration (model, temperature, etc.)

        Returns:
            LLMResponse with the AI's response
        """
        resolved = self.resolve_config(config)

        # Get model info - use default model if invalid model specified
        model_key = resolved.model
        if model_key in MODEL_ALIASES:
            model_key = MODEL_ALIASES[model_key]

        # If model is not a JEDAI model (e.g., gpt-4.1 from default), use our default
        if model_key not in JEDAI_MODELS:
            if self._verbose:
                print(f"⚠️  Model {model_key} not supported by JEDAI, using {self._default_model}")
            model_key = self._default_model

        model_info = JEDAI_MODELS[model_key]

        # Ensure authenticated
        token, url = self._ensure_authenticated()

        # Build request body
        body = {
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": prompt},
            ],
            "model": model_info["family"],
            "location": model_info["location"],
            "project": "gcp-cdns-llm-test",
            "deployment": model_info["deployment"],
            "max_tokens": resolved.max_tokens,
            "temperature": resolved.temperature,
            "top_p": resolved.extra_options.get("top_p", 1),
        }

        #if self._verbose:
            #print(f"📤 Request URL: {url}/api/copilot/v1/llm/chat/completions")
            #print(f"📤 Model: {model_info['family']}, Deployment: {model_info['deployment']}")
            #print(f"📤 Location: {model_info['location']}")

        # Send request
        response = requests.post(
            f"{url}/api/copilot/v1/llm/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            json=body,
            timeout=300,  # LLM calls can take a while (5 minutes for large prompts)
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"JEDAI request failed: {response.status_code} - {response.text}"
            )

        result = response.json()

        # Parse response (handle different formats)
        text = self._extract_text_from_response(result)

        # Extract usage info if available
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")

        return LLMResponse(
            text=text,
            model=model_key,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usage=usage if usage else None,
        )

    def _extract_text_from_response(self, result: Dict[str, Any]) -> str:
        """Extract text content from various response formats."""
        # Format 1: Gemini-style (candidates)
        if "candidates" in result:
            try:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                pass

        # Format 2: OpenAI-style (choices)
        if "choices" in result:
            try:
                return result["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                pass

        # Format 3: Anthropic-style (content)
        if "content" in result:
            try:
                if isinstance(result["content"], list):
                    return result["content"][0]["text"]
                return result["content"]
            except (KeyError, IndexError):
                pass

        raise ValueError(f"Unknown response format: {json.dumps(result, indent=2)[:500]}")

    def list_models(self) -> Dict[str, Dict[str, str]]:
        """Return available JEDAI models."""
        return JEDAI_MODELS.copy()

    def test_connection(self, timeout: int = 5) -> bool:
        """Test if JEDAI is accessible."""
        try:
            response = requests.get(
                f"{self._jedai_url}/health",
                timeout=timeout,
            )
            return response.status_code == 200
        except:
            return False

    @classmethod
    def get_environment_info(cls) -> Dict[str, Any]:
        """Get environment detection information."""
        is_dpc = detect_environment()
        hostname = socket.gethostname()

        return {
            "hostname": hostname,
            "is_dpc": is_dpc,
            "environment": "DPC" if is_dpc else "Non-DPC",
            "primary_url": get_jedai_url(),
            "all_urls": get_all_jedai_urls(),
        }
