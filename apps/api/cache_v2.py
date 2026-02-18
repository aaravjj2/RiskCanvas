"""
RiskCanvas v4.7.0 — Cache v2 (Layered + Visible + Provenance-Safe)

Implements a three-layer deterministic cache:
  - compute_cache:  for computation results (/runs/execute, /analyze/*)
  - report_cache:   for report bundles (/reports/build)
  - market_cache:   for market data responses (/market/*)

Keys: sha256(canonical_request + provider_id + version)
Values stored in-memory (DEMO) with deterministic eviction (stable LRU simulation).
No secrets in cache metadata.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ─────────────────────────── Constants ──────────────────────────────────────

CACHE_V2_VERSION = "v2.0"
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
LAYER_MAX_SIZE = int(os.getenv("CACHE_V2_MAX_SIZE", "128"))

# ─────────────────────────── Layer enum ─────────────────────────────────────

LAYER_COMPUTE = "compute_cache"
LAYER_REPORT = "report_cache"
LAYER_MARKET = "market_cache"
ALL_LAYERS = [LAYER_COMPUTE, LAYER_REPORT, LAYER_MARKET]


# ─────────────────────────── Helper ──────────────────────────────────────────

def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def make_cache_key(request_data: Any, provider_id: str = "fixture") -> str:
    """Deterministic cache key: sha256(canonical_request + provider_id + version)."""
    key_input = {
        "request": request_data,
        "provider_id": provider_id,
        "version": CACHE_V2_VERSION,
    }
    return _sha256(key_input)[:32]


def _entry_hash(value: Any) -> str:
    return _sha256(value)[:16]


# ─────────────────────────── CacheV2 ────────────────────────────────────────

class CacheV2:
    """
    Three-layer in-memory cache with deterministic LRU eviction.
    Thread-safety: single-process DEMO only. No secrets stored in metadata.
    """

    def __init__(self) -> None:
        self._layers: Dict[str, OrderedDict] = {
            LAYER_COMPUTE: OrderedDict(),
            LAYER_REPORT: OrderedDict(),
            LAYER_MARKET: OrderedDict(),
        }
        self._hits: Dict[str, int] = {layer: 0 for layer in ALL_LAYERS}
        self._misses: Dict[str, int] = {layer: 0 for layer in ALL_LAYERS}
        self._evictions: Dict[str, int] = {layer: 0 for layer in ALL_LAYERS}

    def get(self, layer: str, key: str) -> Tuple[bool, Optional[Any], Optional[str]]:
        """
        Returns (hit, value, entry_hash).
        Moves accessed key to end (LRU order — recent = end).
        """
        if layer not in self._layers:
            raise ValueError(f"Unknown cache layer: {layer}")
        store = self._layers[layer]
        if key in store:
            store.move_to_end(key)
            self._hits[layer] += 1
            value, eh = store[key]
            return True, value, eh
        self._misses[layer] += 1
        return False, None, None

    def set(self, layer: str, key: str, value: Any) -> str:
        """Stores value, evicts oldest if over limit. Returns entry_hash."""
        if layer not in self._layers:
            raise ValueError(f"Unknown cache layer: {layer}")
        store = self._layers[layer]
        eh = _entry_hash(value)
        store[key] = (value, eh)
        store.move_to_end(key)
        # Deterministic eviction: remove oldest (first) entries
        while len(store) > LAYER_MAX_SIZE:
            store.popitem(last=False)
            self._evictions[layer] += 1
        return eh

    def clear(self, layer: Optional[str] = None) -> None:
        """Clear one or all layers."""
        layers_to_clear = [layer] if layer else ALL_LAYERS
        for lyr in layers_to_clear:
            self._layers[lyr].clear()
            self._hits[lyr] = 0
            self._misses[lyr] = 0
            self._evictions[lyr] = 0

    def stats(self) -> Dict[str, Any]:
        """Returns deterministic stats snapshot."""
        total_hits = sum(self._hits.values())
        total_misses = sum(self._misses.values())
        total_size = sum(len(s) for s in self._layers.values())
        layers = {}
        for lyr in ALL_LAYERS:
            size = len(self._layers[lyr])
            hits = self._hits[lyr]
            misses = self._misses[lyr]
            requests = hits + misses
            layers[lyr] = {
                "size": size,
                "max_size": LAYER_MAX_SIZE,
                "hits": hits,
                "misses": misses,
                "evictions": self._evictions[lyr],
                "hit_rate": round(hits / requests, 4) if requests > 0 else 0.0,
            }
        return {
            "version": CACHE_V2_VERSION,
            "total_size": total_size,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate": round(total_hits / (total_hits + total_misses), 4) if (total_hits + total_misses) > 0 else 0.0,
            "layers": layers,
        }

    def list_keys(self, layer: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns list of cache key metadata (no values exposed)."""
        if layer not in self._layers:
            raise ValueError(f"Unknown cache layer: {layer}")
        store = self._layers[layer]
        # Return most-recently-used keys first
        items = list(store.items())
        items.reverse()
        result = []
        for key, (_, eh) in items[:limit]:
            result.append({"key": key, "entry_hash": eh})
        return result


# ─────────────────────────── Global singleton ────────────────────────────────

_cache_v2_instance: Optional[CacheV2] = None


def get_cache_v2() -> CacheV2:
    global _cache_v2_instance
    if _cache_v2_instance is None:
        _cache_v2_instance = CacheV2()
    return _cache_v2_instance


def reset_cache_v2() -> None:
    global _cache_v2_instance
    _cache_v2_instance = CacheV2()


# ─────────────────────────── Pydantic Schemas ────────────────────────────────

class CacheV2StatsResponse(BaseModel):
    version: str
    total_size: int
    total_hits: int
    total_misses: int
    hit_rate: float
    layers: Dict[str, Any]


class CacheV2ClearResponse(BaseModel):
    cleared: bool
    layer: Optional[str] = None
    message: str


class CacheV2KeysResponse(BaseModel):
    layer: str
    keys: List[Dict[str, Any]]
    count: int


# ─────────────────────────── Router ──────────────────────────────────────────

cache_v2_router = APIRouter(prefix="/cache/v2", tags=["cache_v2"])


@cache_v2_router.get("/stats", response_model=CacheV2StatsResponse)
def cache_v2_stats() -> Dict[str, Any]:
    """Returns cache stats across all layers."""
    return get_cache_v2().stats()


@cache_v2_router.post("/clear", response_model=CacheV2ClearResponse)
def cache_v2_clear(layer: Optional[str] = None) -> Dict[str, Any]:
    """Clears cache layer(s). DEMO only — enforced."""
    demo = os.getenv("DEMO_MODE", "false").lower() == "true"
    if not demo:
        raise HTTPException(status_code=403, detail="Cache clear only available in DEMO_MODE")
    if layer and layer not in ALL_LAYERS:
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}. Valid: {ALL_LAYERS}")
    get_cache_v2().clear(layer)
    return {
        "cleared": True,
        "layer": layer,
        "message": f"Cleared {'layer ' + layer if layer else 'all layers'}",
    }


@cache_v2_router.get("/keys", response_model=CacheV2KeysResponse)
def cache_v2_keys(layer: str = LAYER_COMPUTE, limit: int = 20) -> Dict[str, Any]:
    """Returns list of cache keys for a layer (metadata only, no values)."""
    if layer not in ALL_LAYERS:
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}. Valid: {ALL_LAYERS}")
    keys = get_cache_v2().list_keys(layer, limit=limit)
    return {"layer": layer, "keys": keys, "count": len(keys)}
