"""
LLM Client Manager - Singleton pattern for web backend.

This manager ensures LLM clients are reused across requests,
avoiding repeated authentication and token regeneration.

Features:
- Client caching and reuse
- Integration with settings API
- Automatic cache invalidation on settings change
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
_tool_dir = Path(__file__).resolve().parent.parent.parent
if str(_tool_dir) not in sys.path:
    sys.path.insert(0, str(_tool_dir))


class LLMClientManager:
    """
    Singleton manager for LLM clients with settings integration.
    
    Maintains a cache of LLM client instances keyed by (provider, model).
    This avoids creating new clients for every request, which would trigger
    repeated authentication and token saving.
    
    Integrates with settings to:
    - Use default provider/model from settings
    - Clear cache when settings change
    - Support per-user settings
    """
    
    _instance: Optional['LLMClientManager'] = None
    _clients: Dict[tuple, Any] = {}
    _current_settings: Dict[str, Any] = {
        'llm_provider': 'jedai',
        'llm_model': 'claude-sonnet-4-5'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def update_settings(self, llm_provider: str = None, llm_model: str = None):
        """
        Update settings and clear affected clients from cache.
        
        Args:
            llm_provider: New LLM provider (if changed)
            llm_model: New LLM model (if changed)
        """
        old_provider = self._current_settings.get('llm_provider')
        old_model = self._current_settings.get('llm_model')
        
        settings_changed = False
        
        if llm_provider and llm_provider != old_provider:
            print(f"[LLM Manager] 🔄 Provider changed: {old_provider} → {llm_provider}")
            self._current_settings['llm_provider'] = llm_provider
            settings_changed = True
            
            # Clear all clients for old provider
            keys_to_remove = [k for k in self._clients.keys() if k[0] == old_provider]
            for key in keys_to_remove:
                del self._clients[key]
                print(f"[LLM Manager] 🗑️ Removed cached client: {key}")
        
        if llm_model and llm_model != old_model:
            print(f"[LLM Manager] 🔄 Model changed: {old_model} → {llm_model}")
            self._current_settings['llm_model'] = llm_model
            settings_changed = True
            
            # Clear client for old model (if exists)
            old_key = (old_provider, old_model)
            if old_key in self._clients:
                del self._clients[old_key]
                print(f"[LLM Manager] 🗑️ Removed cached client: {old_key}")
        
        if settings_changed:
            print(f"[LLM Manager] ✅ Settings updated: {self._current_settings}")
        
        return settings_changed
    
    def get_client(self, provider: str = None, model: str = None, verbose: bool = False):
        """
        Get or create an LLM client for the given provider and model.
        
        If provider/model not specified, uses current settings.
        
        Args:
            provider: LLM provider (e.g., 'jedai', 'openai'), defaults to settings
            model: Model name (e.g., 'claude-sonnet-4-5'), defaults to settings
            verbose: Enable verbose logging
            
        Returns:
            LLM client instance (reused if already created)
        """
        # Use settings as defaults
        if provider is None:
            provider = self._current_settings.get('llm_provider', 'jedai')
        if model is None:
            model = self._current_settings.get('llm_model', 'claude-sonnet-4-5')
        
        cache_key = (provider, model)
        
        # Return cached client if available
        if cache_key in self._clients:
            print(f"[LLM Manager] ♻️ Reusing {provider} client (model: {model})")
            print(f"[LLM Manager] 💡 Note: Client may auto-refresh token if expired")
            return self._clients[cache_key]
        
        # Create new client
        print(f"[LLM Manager] 🆕 Creating {provider} client (model: {model})")
        
        try:
            from llm_clients.factory import create_llm_client
        except ImportError:
            from AutoGenChecker.llm_clients.factory import create_llm_client
        
        client = create_llm_client(provider, model=model, verbose=verbose)
        
        # Cache the client
        self._clients[cache_key] = client
        
        return client
    
    def clear_cache(self, provider: str = None):
        """
        Clear cached LLM clients.
        
        Args:
            provider: If specified, only clear clients for this provider.
                     If None, clear all clients.
        """
        if provider:
            keys_to_remove = [k for k in self._clients.keys() if k[0] == provider]
            for key in keys_to_remove:
                del self._clients[key]
            print(f"[LLM Manager] 🗑️ Cleared {len(keys_to_remove)} client(s) for provider: {provider}")
        else:
            count = len(self._clients)
            self._clients.clear()
            print(f"[LLM Manager] 🗑️ Cleared all {count} cached client(s)")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current LLM settings."""
        return self._current_settings.copy()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached clients."""
        return {
            "cached_clients": len(self._clients),
            "clients": [
                {"provider": provider, "model": model}
                for provider, model in self._clients.keys()
            ],
            "current_settings": self._current_settings
        }


# Global singleton instance
llm_client_manager = LLMClientManager()
