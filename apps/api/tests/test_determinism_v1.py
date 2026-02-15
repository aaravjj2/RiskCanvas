"""
Determinism tests for the v1.0 API endpoints.

Verifies that every computational endpoint returns identical results
on repeated invocations (same input → same output, per CLAUDE.md).
"""

import hashlib
import json
import sys
import os
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

# Ensure engine + app are importable
_api_dir = os.path.join(os.path.dirname(__file__), "..")
_engine_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "packages" / "engine")
for p in (_api_dir, _engine_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app  # noqa: E402

RUNS = 5  # number of repeat calls

# Keys that are non-deterministic by design (unique per request)
_VOLATILE_KEYS = {"request_id", "timestamp"}


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def _strip_volatile(obj):
    """Recursively strip volatile keys from a JSON-serializable object."""
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in obj.items() if k not in _VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip_volatile(v) for v in obj]
    return obj


def _hash(obj) -> str:
    cleaned = _strip_volatile(obj)
    return hashlib.sha256(json.dumps(cleaned, sort_keys=True).encode()).hexdigest()


# ── /price/option ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_price_option(client):
    payload = {"S": 100, "K": 105, "T": 0.25, "r": 0.05, "sigma": 0.2, "option_type": "call"}
    hashes = set()
    for _ in range(RUNS):
        resp = await client.post("/price/option", json=payload)
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1, f"Non-deterministic /price/option: got {len(hashes)} distinct hashes"


# ── /analyze/portfolio ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_analyze_portfolio(client):
    payload = {
        "portfolio": {
            "assets": [
                {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0},
                {"symbol": "TSLA", "type": "stock", "quantity": 5, "price": 250.0},
            ]
        }
    }
    hashes = set()
    for _ in range(RUNS):
        resp = await client.post("/analyze/portfolio", json=payload)
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1, f"Non-deterministic /analyze/portfolio"


# ── /risk/var ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_risk_var(client):
    payload = {
        "portfolio_value": 1_000_000,
        "volatility": 0.15,
        "confidence_level": 0.95,
        "time_horizon_days": 1,
    }
    hashes = set()
    for _ in range(RUNS):
        resp = await client.post("/risk/var", json=payload)
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1, f"Non-deterministic /risk/var"


# ── /scenario/run ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_scenario_run(client):
    payload = {
        "positions": [
            {"type": "stock", "quantity": 10, "current_price": 100, "symbol": "AAPL"}
        ],
        "scenarios": [
            {"name": "crash", "shock_type": "price", "parameters": {"factor": 0.8}},
        ],
    }
    hashes = set()
    for _ in range(RUNS):
        resp = await client.post("/scenario/run", json=payload)
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1, f"Non-deterministic /scenario/run"


# ── /determinism/check ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_check_endpoint(client):
    """The dedicated determinism endpoint itself must be deterministic."""
    hashes = set()
    for _ in range(RUNS):
        resp = await client.post("/determinism/check")
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed"] is True
        hashes.add(body["overall_hash"])
    assert len(hashes) == 1, f"Non-deterministic /determinism/check hash"


# ── /health & /version ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_determinism_health(client):
    hashes = set()
    for _ in range(RUNS):
        resp = await client.get("/health")
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1


@pytest.mark.asyncio
async def test_determinism_version(client):
    hashes = set()
    for _ in range(RUNS):
        resp = await client.get("/version")
        assert resp.status_code == 200
        hashes.add(_hash(resp.json()))
    assert len(hashes) == 1
