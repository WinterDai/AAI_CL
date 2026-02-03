################################################################################
# Script Name: result_cache_manager.py
#
# Purpose:
#   Manage CheckResult caching with support for:
#   - In-memory cache (fast, single process)
#   - File-based cache (persistent, cross-process)
#   - Redis cache (distributed, network-based)
#   - Cache size limits and eviction
#   - Performance statistics
#
# Cache Priority (auto-detection):
#   1. Redis (if available and configured)
#   2. In-memory (fallback)
#   3. File-based (only if CHECKLIST_USE_FILE_CACHE=1)
#
# Redis Configuration (optional):
#   Environment variables:
#   - CHECKLIST_REDIS_HOST: Redis server host (default: localhost)
#   - CHECKLIST_REDIS_PORT: Redis server port (default: 6379)
#   - CHECKLIST_REDIS_DB: Redis database number (default: 0)
#   - CHECKLIST_REDIS_PASSWORD: Redis password (default: None)
#   - CHECKLIST_REDIS_TTL: Cache TTL in seconds (default: 3600)
#
# Author: yyin
# Date:   2025-11-10
################################################################################
import json
import pickle
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import OrderedDict
import threading

# Try to import redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    evictions: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'writes': self.writes,
            'evictions': self.evictions,
            'hit_rate': f"{self.hit_rate:.2f}%",
            'total_requests': self.hits + self.misses
        }


class ResultCacheManager:
    """
    Manage CheckResult caching with multiple backends.
    
    Supports (in priority order):
    1. Redis cache - distributed, network-based (if available)
    2. Memory cache (L1) - fastest, single process
    3. File cache (L2) - persistent, cross-process (optional)
    
    Redis auto-detection:
    - If redis module is installed and server is reachable, uses Redis
    - Otherwise falls back to memory + file cache
    - No configuration required for fallback
    
    Redis configuration (optional environment variables):
    - CHECKLIST_REDIS_HOST: default 'localhost'
    - CHECKLIST_REDIS_PORT: default 6379
    - CHECKLIST_REDIS_DB: default 0
    - CHECKLIST_REDIS_PASSWORD: default None
    - CHECKLIST_REDIS_TTL: default 3600 seconds
    
    Usage:
        cache = ResultCacheManager(cache_dir=Path("cache"), max_memory_size=100)
        
        # Store result
        cache.set(item_id, result)
        
        # Retrieve result
        result = cache.get(item_id)
        
        # Get statistics
        stats = cache.get_stats()
    """
    
    def __init__(self, 
                 cache_dir: Optional[Path] = None,
                 max_memory_size: int = 200,
                 enable_file_cache: bool = True,
                 enable_stats: bool = True):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for file cache (None = disabled)
            max_memory_size: Maximum number of items in memory cache
            enable_file_cache: Enable persistent file cache
            enable_stats: Enable performance statistics
        """
        # Redis cache (highest priority)
        self._redis_client: Optional['redis.Redis'] = None
        self._redis_ttl = int(os.environ.get('CHECKLIST_REDIS_TTL', '3600'))
        self._init_redis()
        
        # L1 cache: Memory (OrderedDict for LRU eviction)
        self._memory_cache: OrderedDict = OrderedDict()
        self._max_memory_size = max_memory_size
        self._lock = threading.Lock()
        
        # L2 cache: File-based
        self._cache_dir = cache_dir
        self._enable_file_cache = enable_file_cache and cache_dir is not None
        if self._enable_file_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self._enable_stats = enable_stats
        self._stats = CacheStats()
    
    def _init_redis(self):
        """
        Initialize Redis connection if available.
        
        Auto-detection strategy:
        1. Try to connect to Redis with default/configured settings
        2. If successful: use Redis cache (distributed, high performance)
        3. If failed: silently fall back to file-based cache
        
        No environment variables required - uses smart defaults.
        """
        if not REDIS_AVAILABLE:
            return
        
        try:
            # Read Redis configuration from environment (optional)
            # If not set, uses localhost:6379 (standard Redis defaults)
            host = os.environ.get('CHECKLIST_REDIS_HOST', 'localhost')
            port = int(os.environ.get('CHECKLIST_REDIS_PORT', '6379'))
            db = int(os.environ.get('CHECKLIST_REDIS_DB', '0'))
            password = os.environ.get('CHECKLIST_REDIS_PASSWORD', None)
            
            # Create Redis client with short timeout
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_connect_timeout=1,  # 1 second timeout
                socket_timeout=2,
                decode_responses=False  # We'll handle binary data
            )
            
            # Test connection
            self._redis_client.ping()
            print(f"[INFO] ✓ Redis cache enabled: {host}:{port} (DB {db}) - distributed mode")
            
        except Exception:
            # Redis not available, silently fall back to file cache
            self._redis_client = None
            print(f"[INFO] Redis not available - using shared file cache (still supports distributed)")
    
    def get(self, item_id: str) -> Optional[Any]:
        """
        Get cached result for item.
        
        Lookup order:
        1. Redis cache (if available) - distributed
        2. Memory cache (L1) - fastest, single process
        3. File cache (L2) - slower but persistent
        4. None - cache miss
        
        Args:
            item_id: Item ID to retrieve
            
        Returns:
            Cached CheckResult or None
        """
        with self._lock:
            # Try 1: Redis cache
            if self._redis_client:
                try:
                    data = self._redis_client.get(f"checklist:{item_id}")
                    if data:
                        result = pickle.loads(data)
                        # Promote to L1 memory cache
                        self._set_memory(item_id, result)
                        if self._enable_stats:
                            self._stats.hits += 1
                        return result
                except Exception:
                    pass  # Fall through to memory cache
            
            # Try 2: Memory cache (L1)
            if item_id in self._memory_cache:
                # Move to end (LRU)
                self._memory_cache.move_to_end(item_id)
                if self._enable_stats:
                    self._stats.hits += 1
                return self._memory_cache[item_id]
            
            # Try 3: File cache (L2)
            if self._enable_file_cache:
                result = self._load_from_file(item_id)
                if result is not None:
                    # Promote to L1
                    self._set_memory(item_id, result)
                    if self._enable_stats:
                        self._stats.hits += 1
                    return result
            
            # Cache miss
            if self._enable_stats:
                self._stats.misses += 1
            return None
    
    def set(self, item_id: str, result: Any) -> None:
        """
        Store result in cache.
        
        Storage priority:
        1. Redis (if available) - distributed, fast
        2. Memory - single process, very fast
        3. File (always) - cross-process, persistent
        
        Args:
            item_id: Item ID
            result: CheckResult object to cache
        """
        with self._lock:
            # Store in Redis (highest priority, if available)
            if self._redis_client:
                try:
                    data = pickle.dumps(result)
                    self._redis_client.setex(
                        f"checklist:{item_id}",
                        self._redis_ttl,
                        data
                    )
                except Exception:
                    pass  # Silent failure, will use memory/file cache
            
            # Store in L1: Memory (for same-process access)
            self._set_memory(item_id, result)
            
            # Store in L2: File (ALWAYS - for cross-process/distributed support)
            # This is the fallback that ensures distributed execution works
            # even without Redis
            if self._enable_file_cache:
                self._save_to_file(item_id, result)
            
            if self._enable_stats:
                self._stats.writes += 1
    
    def _set_memory(self, item_id: str, result: Any) -> None:
        """
        Store in memory cache with LRU eviction.
        
        Args:
            item_id: Item ID
            result: CheckResult to cache
        """
        # Add or update
        if item_id in self._memory_cache:
            self._memory_cache.move_to_end(item_id)
        else:
            self._memory_cache[item_id] = result
        
        # Evict oldest if over limit
        while len(self._memory_cache) > self._max_memory_size:
            evicted_id, _ = self._memory_cache.popitem(last=False)
            if self._enable_stats:
                self._stats.evictions += 1
    
    def _save_to_file(self, item_id: str, result: Any) -> None:
        """
        Save result to file cache.
        
        Format: {item_id}.pkl (pickle for full object serialization)
        
        Args:
            item_id: Item ID
            result: CheckResult to save
        """
        try:
            cache_file = self._cache_dir / f"{item_id}.pkl"
            with cache_file.open('wb') as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            # Silently fail - cache is optional
            pass
    
    def _load_from_file(self, item_id: str) -> Optional[Any]:
        """
        Load result from file cache.
        
        Args:
            item_id: Item ID
            
        Returns:
            CheckResult or None if not found
        """
        try:
            cache_file = self._cache_dir / f"{item_id}.pkl"
            if cache_file.exists():
                with cache_file.open('rb') as f:
                    return pickle.load(f)
        except Exception:
            pass
        return None
    
    def clear_memory(self) -> None:
        """Clear memory cache only."""
        with self._lock:
            self._memory_cache.clear()
    
    def clear_file_cache(self) -> int:
        """
        Clear file cache.
        
        Returns:
            Number of files deleted
        """
        if not self._enable_file_cache:
            return 0
        
        count = 0
        try:
            for cache_file in self._cache_dir.glob("*.pkl"):
                cache_file.unlink()
                count += 1
        except Exception:
            pass
        return count
    
    def clear_all(self) -> int:
        """
        Clear both memory and file cache.
        
        Returns:
            Number of files deleted
        """
        self.clear_memory()
        return self.clear_file_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            stats = self._stats.to_dict()
            stats['memory_size'] = len(self._memory_cache)
            stats['memory_limit'] = self._max_memory_size
            stats['file_cache_enabled'] = self._enable_file_cache
            return stats
    
    def print_stats(self) -> None:
        """Print cache statistics to console."""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("Cache Performance Statistics")
        print("="*60)
        print(f"Total Requests:     {stats['total_requests']}")
        print(f"Cache Hits:         {stats['hits']}")
        print(f"Cache Misses:       {stats['misses']}")
        print(f"Hit Rate:           {stats['hit_rate']}")
        print(f"Writes:             {stats['writes']}")
        print(f"Evictions:          {stats['evictions']}")
        print(f"Memory Cache Size:  {stats['memory_size']} / {stats['memory_limit']}")
        print(f"File Cache:         {'Enabled' if stats['file_cache_enabled'] else 'Disabled'}")
        print("="*60 + "\n")


# Global singleton instance (backward compatible with existing code)
_global_cache: Optional[ResultCacheManager] = None


def get_global_cache() -> ResultCacheManager:
    """
    Get or create global cache instance.
    
    Returns:
        Global ResultCacheManager instance
    """
    global _global_cache
    if _global_cache is None:
        # Default configuration: memory-only cache
        _global_cache = ResultCacheManager(
            cache_dir=None,
            max_memory_size=200,
            enable_file_cache=False,
            enable_stats=True
        )
    return _global_cache


def configure_global_cache(cache_dir: Optional[Path] = None,
                          max_memory_size: int = 200,
                          enable_file_cache: bool = True) -> ResultCacheManager:
    """
    Configure and return global cache instance.
    
    Args:
        cache_dir: Directory for file cache
        max_memory_size: Max items in memory
        enable_file_cache: Enable file cache
        
    Returns:
        Configured global cache instance
    """
    global _global_cache
    _global_cache = ResultCacheManager(
        cache_dir=cache_dir,
        max_memory_size=max_memory_size,
        enable_file_cache=enable_file_cache,
        enable_stats=True
    )
    return _global_cache
