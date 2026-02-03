"""Settings API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
from pathlib import Path

router = APIRouter()

# Import LLM client manager for settings sync
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from llm_client_manager import llm_client_manager

# Settings file path
SETTINGS_FILE = _backend_dir / "config" / "settings.json"


class Settings(BaseModel):
    """Settings model."""
    llm_provider: str = "jedai"
    llm_model: str = "claude-sonnet-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retry_attempts: int = 3
    auto_save: bool = True
    auto_test: bool = False
    dark_mode: bool = False


class TestConnectionRequest(BaseModel):
    """Test connection request model."""
    provider: str
    model: str


def load_settings() -> dict:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Settings] Failed to load settings: {e}")
    return {}


def save_settings(settings: dict):
    """Save settings to file."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        print(f"[Settings] Saved to {SETTINGS_FILE}")
    except Exception as e:
        print(f"[Settings] Failed to save settings: {e}")


# Global settings instance (loaded at startup)
_global_settings = load_settings()


def get_global_settings() -> dict:
    """Get global settings (for use by other modules)."""
    return _global_settings


@router.get("/", response_model=Settings)
async def get_settings():
    """Get current settings."""
    global _global_settings
    _global_settings = load_settings()
    
    # Merge with LLM manager settings
    llm_settings = llm_client_manager.get_current_settings()
    
    return Settings(
        llm_provider=_global_settings.get('llm_provider', llm_settings.get('llm_provider', 'jedai')),
        llm_model=_global_settings.get('llm_model', llm_settings.get('llm_model', 'claude-sonnet-4')),
        temperature=_global_settings.get('temperature', 0.7),
        max_tokens=_global_settings.get('max_tokens', 4096),
        max_retry_attempts=_global_settings.get('max_retry_attempts', 3),
        auto_save=_global_settings.get('auto_save', True),
        auto_test=_global_settings.get('auto_test', False),
        dark_mode=_global_settings.get('dark_mode', False)
    )


@router.put("/", response_model=Settings)
async def update_settings(settings: Settings):
    """Update settings and sync with LLM client manager."""
    global _global_settings
    
    # Convert to dict and save
    settings_dict = settings.model_dump()
    save_settings(settings_dict)
    _global_settings = settings_dict
    
    # Update LLM client manager settings
    settings_changed = llm_client_manager.update_settings(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model
    )
    
    if settings_changed:
        print(f"[Settings API] ✅ LLM settings updated: {settings.llm_provider}/{settings.llm_model}")
    
    return settings


@router.post("/test-llm-connection")
async def test_llm_connection(request: TestConnectionRequest):
    """Test LLM connection with specified provider and model."""
    try:
        # For JEDAI, we can't fully test without password
        # But we can check if the URL is reachable
        if request.provider == 'jedai':
            import socket
            import requests
            
            # Try to detect JEDAI URL
            hostname = socket.gethostname()
            
            # Determine which URL to use
            dpc_patterns = ['dpc', 'nfdpc', 'ssgdpc', 'atl', 'cadence.com', 'sjc', 'aus', 'rtp']
            is_dpc = any(pattern in hostname.lower() for pattern in dpc_patterns)
            
            if is_dpc:
                jedai_url = "http://ssgdpc-jedai.cadence.com:5000"
            else:
                jedai_url = "http://sjf-dsgdspr-084.cadence.com:5668"
            
            # Try health check
            try:
                response = requests.get(f"{jedai_url}/health", timeout=5)
                if response.status_code == 200:
                    return {
                        "success": True,
                        "model": request.model,
                        "message": f"JEDAI server reachable at {jedai_url}",
                        "environment": "DPC" if is_dpc else "Non-DPC"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"JEDAI returned status {response.status_code}"
                    }
            except requests.exceptions.Timeout:
                return {
                    "success": False,
                    "error": f"Connection timeout to {jedai_url}"
                }
            except requests.exceptions.ConnectionError:
                return {
                    "success": False,
                    "error": f"Cannot connect to {jedai_url}"
                }
        
        elif request.provider == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return {
                    "success": False,
                    "error": "OPENAI_API_KEY environment variable not set"
                }
            return {
                "success": True,
                "model": request.model,
                "message": "OpenAI API key found"
            }
        
        elif request.provider == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                return {
                    "success": False,
                    "error": "ANTHROPIC_API_KEY environment variable not set"
                }
            return {
                "success": True,
                "model": request.model,
                "message": "Anthropic API key found"
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown provider: {request.provider}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/llm-cache-info")
async def get_llm_cache_info():
    """Get LLM client manager cache information (for debugging)."""
    return llm_client_manager.get_cache_info()


@router.post("/llm-cache-clear")
async def clear_llm_cache(provider: Optional[str] = None):
    """
    Clear LLM client cache.
    
    Args:
        provider: If specified, only clear clients for this provider.
                 If None, clear all clients.
    """
    llm_client_manager.clear_cache(provider)
    return {
        "status": "success",
        "message": f"Cleared cache for {provider if provider else 'all providers'}",
        "cache_info": llm_client_manager.get_cache_info()
    }


@router.get("/llm-models")
async def get_llm_models(provider: str):
    """Get available LLM models for a provider."""
    models = {
        "jedai": [
            {"value": "claude-opus-4", "label": "Claude Opus 4 (Most Capable)"},
            {"value": "claude-sonnet-4", "label": "Claude Sonnet 4 (Recommended)"},
            {"value": "gemini-2-5-pro", "label": "Gemini 2.5 Pro"},
            {"value": "gemini-2-5-flash", "label": "Gemini 2.5 Flash (Fast)"},
        ],
        "openai": [
            {"value": "gpt-4-turbo", "label": "GPT-4 Turbo"},
            {"value": "gpt-4", "label": "GPT-4"},
            {"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
        ],
        "anthropic": [
            {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet"},
            {"value": "claude-3-opus-20240229", "label": "Claude 3 Opus"},
        ]
    }
    return {"models": models.get(provider, [])}
