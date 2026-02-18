"""
Caching Module (v1.9)
Deterministic cache layer for computation results.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# In-memory cache storage
_cache: Dict[str, Dict[str, Any]] = {}
_cache_hits: int = 0
_cache_misses: int = 0


def deterministic_cache_key(canonical_request: Dict[str, Any], engine_version: str) -> str:
    """
    Generate deterministic cache key from canonical request and engine version.
    
    Args:
        canonical_request: Normalized request dict (sorted keys)
        engine_version: Engine version string (e.g., "0.1.0")
    
    Returns:
        SHA256 hash as hex string
    """
    # Sort keys for determinism
    canonical_json = json.dumps(canonical_request, sort_keys=True, separators=(',', ':'))
    
    # Include engine version in hash
    hash_input = f"{engine_version}:{canonical_json}"
    
    # SHA256 hash
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def cache_get(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached result by key.
    
    Returns:
        Cached entry dict or None if not found
    """
    global _cache_hits, _cache_misses
    
    if cache_key in _cache:
        _cache_hits += 1
        return _cache[cache_key]
    else:
        _cache_misses += 1
        return None


def cache_set(cache_key: str, output: Any, metadata: Dict[str, Any]) -> None:
    """
    Store result in cache.
    
    Args:
        cache_key: Cache key from deterministic_cache_key()
        output: Computation result (any JSON-serializable type)
        metadata: Additional metadata (e.g., computation_time, timestamp)
    """
    # Use E2E_MODE check for deterministic timestamps
    e2e_mode = os.getenv("E2E_MODE", "false").lower() == "true"
    
    if e2e_mode:
        timestamp = "2025-01-01T00:00:00Z"
    else:
        timestamp = datetime.utcnow().isoformat() + "Z"
    
    _cache[cache_key] = {
        "output": output,
        "metadata": metadata,
        "timestamp": timestamp,
        "cache_key": cache_key
    }


def cache_clear() -> int:
    """
    Clear all cache entries.
    
    Returns:
        Number of entries cleared
    """
    global _cache, _cache_hits, _cache_misses
    
    count = len(_cache)
    _cache.clear()
    _cache_hits = 0
    _cache_misses = 0
    
    return count


def cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dict with size, hits, misses, hit_rate
    """
    total_requests = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total_requests) if total_requests > 0 else 0.0
    
    return {
        "size": len(_cache),
        "hits": _cache_hits,
        "misses": _cache_misses,
        "hit_rate": round(hit_rate, 4)
    }


def reset_caching() -> None:
    """
    Reset caching module state (for E2E testing).
    Clears cache and resets stats.
    """
    cache_clear()
