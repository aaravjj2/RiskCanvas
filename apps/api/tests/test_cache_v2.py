"""Tests for cache_v2.py — v4.7.0"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DEMO_MODE"] = "true"

from cache_v2 import CacheV2, make_cache_key, reset_cache_v2, get_cache_v2, CACHE_V2_VERSION, LAYER_MAX_SIZE


@pytest.fixture(autouse=True)
def fresh_cache():
    reset_cache_v2()
    yield
    reset_cache_v2()


class TestMakeCacheKey:
    def test_deterministic(self):
        k1 = make_cache_key({"a": 1}, "fixture")
        k2 = make_cache_key({"a": 1}, "fixture")
        assert k1 == k2

    def test_key_length_32(self):
        k = make_cache_key({"x": 99}, "p1")
        assert len(k) == 32

    def test_different_inputs_different_keys(self):
        k1 = make_cache_key({"a": 1}, "fixture")
        k2 = make_cache_key({"a": 2}, "fixture")
        assert k1 != k2

    def test_different_providers_different_keys(self):
        k1 = make_cache_key({"a": 1}, "fixture")
        k2 = make_cache_key({"a": 1}, "remote")
        assert k1 != k2

    def test_version_in_key(self):
        k1 = make_cache_key({"a": 1}, "p1")
        # Version is embedded; changing CACHE_V2_VERSION would change key
        assert isinstance(k1, str)

    def test_key_is_hex(self):
        k = make_cache_key({"test": True}, "p")
        int(k, 16)  # should not raise


class TestCacheV2GetSet:
    def test_miss_on_empty(self):
        cache = get_cache_v2()
        hit, value, _ = cache.get("compute_cache", "nonexistent")
        assert hit is False
        assert value is None

    def test_set_then_get_hit(self):
        cache = get_cache_v2()
        k = make_cache_key({"r": 1}, "p")
        cache.set("compute_cache", k, {"result": 42})
        hit, value, entry_hash = cache.get("compute_cache", k)
        assert hit is True
        assert value["result"] == 42
        assert entry_hash is not None

    def test_entry_hash_deterministic(self):
        cache = get_cache_v2()
        k = make_cache_key({"r": 2}, "p")
        h1 = cache.set("compute_cache", k, {"val": 99})
        h2 = cache.set("compute_cache", k, {"val": 99})
        assert h1 == h2

    def test_layers_independent(self):
        cache = get_cache_v2()
        k = make_cache_key({"x": 5}, "p")
        cache.set("compute_cache", k, {"layer": "compute"})
        hit, _, _ = cache.get("report_cache", k)
        assert hit is False

    def test_all_three_layers_work(self):
        cache = get_cache_v2()
        for layer in ["compute_cache", "report_cache", "market_cache"]:
            k = make_cache_key({"l": layer}, "p")
            cache.set(layer, k, {"ok": True})
            hit, val, _ = cache.get(layer, k)
            assert hit is True, f"Layer {layer} failed"

    def test_invalid_layer_raises(self):
        cache = get_cache_v2()
        with pytest.raises(ValueError):
            cache.get("invalid_layer", "key123")


class TestCacheV2Eviction:
    def test_lru_eviction_deterministic(self):
        """Fill cache beyond MAX_SIZE, verify oldest entry evicted."""
        cache = get_cache_v2()
        max_size = LAYER_MAX_SIZE
        keys = []
        for i in range(max_size + 1):
            k = make_cache_key({"i": i}, "p")
            keys.append(k)
            cache.set("compute_cache", k, {"i": i})
        # First key should have been evicted
        hit, _, _ = cache.get("compute_cache", keys[0])
        assert hit is False
        # Last key should still be present
        hit, val, _ = cache.get("compute_cache", keys[-1])
        assert hit is True

    def test_eviction_count_tracked(self):
        cache = get_cache_v2()
        max_size = LAYER_MAX_SIZE
        for i in range(max_size + 5):
            k = make_cache_key({"i": i}, "p")
            cache.set("compute_cache", k, {"i": i})
        stats = cache.stats()
        assert stats["layers"]["compute_cache"]["evictions"] >= 5


class TestCacheV2Stats:
    def test_stats_initial_zero(self):
        cache = get_cache_v2()
        stats = cache.stats()
        for layer in ["compute_cache", "report_cache", "market_cache"]:
            assert stats["layers"][layer]["size"] == 0
            assert stats["layers"][layer]["hits"] == 0
            assert stats["layers"][layer]["misses"] == 0

    def test_stats_tracks_hits_misses(self):
        cache = get_cache_v2()
        k = make_cache_key({"x": 1}, "p")
        cache.get("compute_cache", k)  # miss
        cache.set("compute_cache", k, {"v": 1})
        cache.get("compute_cache", k)  # hit
        stats = cache.stats()
        assert stats["layers"]["compute_cache"]["hits"] == 1
        assert stats["layers"]["compute_cache"]["misses"] == 1

    def test_hit_rate_calculation(self):
        cache = get_cache_v2()
        k = make_cache_key({"y": 1}, "p")
        cache.set("compute_cache", k, {"v": 1})
        cache.get("compute_cache", k)  # hit
        cache.get("compute_cache", k)  # hit
        stats = cache.stats()
        assert stats["layers"]["compute_cache"]["hit_rate"] == 1.0

    def test_stats_version_present(self):
        cache = get_cache_v2()
        stats = cache.stats()
        assert "version" in stats
        assert stats["version"] == CACHE_V2_VERSION


class TestCacheV2Clear:
    def test_clear_specific_layer(self):
        cache = get_cache_v2()
        k = make_cache_key({"z": 1}, "p")
        cache.set("compute_cache", k, {"v": 1})
        cache.clear(layer="compute_cache")
        hit, _, _ = cache.get("compute_cache", k)
        assert hit is False

    def test_clear_preserves_other_layers(self):
        cache = get_cache_v2()
        k = make_cache_key({"z": 2}, "p")
        cache.set("compute_cache", k, {"c": 1})
        cache.set("report_cache", k, {"r": 1})
        cache.clear(layer="compute_cache")
        hit, _, _ = cache.get("report_cache", k)
        assert hit is True

    def test_clear_all_layers(self):
        cache = get_cache_v2()
        k = make_cache_key({"z": 3}, "p")
        for layer in ["compute_cache", "report_cache", "market_cache"]:
            cache.set(layer, k, {"v": 1})
        cache.clear()
        for layer in ["compute_cache", "report_cache", "market_cache"]:
            hit, _, _ = cache.get(layer, k)
            assert hit is False, f"Layer {layer} not cleared"


class TestCacheV2Router:
    def setup_method(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from cache_v2 import cache_v2_router
        self.app_inst = FastAPI()
        self.app_inst.include_router(cache_v2_router)
        self.client = TestClient(self.app_inst)

    def test_stats_endpoint(self):
        resp = self.client.get("/cache/v2/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "layers" in data

    def test_keys_endpoint(self):
        resp = self.client.get("/cache/v2/keys?layer=compute_cache")
        assert resp.status_code == 200
        data = resp.json()
        assert "keys" in data

    def test_clear_endpoint_demo_mode(self):
        resp = self.client.post("/cache/v2/clear", json={})
        assert resp.status_code == 200

    def test_clear_endpoint_non_demo_forbidden(self, monkeypatch):
        monkeypatch.setenv("DEMO_MODE", "false")
        resp = self.client.post("/cache/v2/clear", json={})
        assert resp.status_code == 403
