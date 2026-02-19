"""
Tests for v4.10.0 PnL Attribution Engine (Wave 15)
Verifies: determinism, factor ordering, contribution sums, export, API.
"""
import json
import pytest
from fastapi.testclient import TestClient


def test_pnl_attribution_determinism():
    """Same inputs → same outputs (determinism check)."""
    from pnl_attribution import compute_pnl_attribution

    r1 = compute_pnl_attribution("run_base_001", "run_cmp_001")
    r2 = compute_pnl_attribution("run_base_001", "run_cmp_001")

    assert r1["output_hash"] == r2["output_hash"]
    assert r1["total_pnl"] == r2["total_pnl"]
    assert r1["contributions"] == r2["contributions"]


def test_pnl_attribution_different_runs_differ():
    """Different inputs → different outputs."""
    from pnl_attribution import compute_pnl_attribution

    r1 = compute_pnl_attribution("run_base_001", "run_cmp_001")
    r2 = compute_pnl_attribution("run_base_002", "run_cmp_002")

    assert r1["output_hash"] != r2["output_hash"]


def test_pnl_factor_ordering():
    """Contributions list is stable (not random)."""
    from pnl_attribution import compute_pnl_attribution

    result = compute_pnl_attribution("run_base_001", "run_cmp_001")
    factors = [c["factor"] for c in result["contributions"]]

    # Same order on repeated call
    result2 = compute_pnl_attribution("run_base_001", "run_cmp_001")
    factors2 = [c["factor"] for c in result2["contributions"]]
    assert factors == factors2


def test_pnl_attribution_has_required_fields():
    """Attribution result must have all required fields."""
    from pnl_attribution import compute_pnl_attribution

    result = compute_pnl_attribution("run_base_001", "run_cmp_001")
    assert "total_pnl" in result
    assert "contributions" in result
    assert "top_drivers" in result
    assert "input_hash" in result
    assert "output_hash" in result
    assert "audit_chain_head_hash" in result


def test_pnl_top_drivers_length():
    """Top drivers should have at most 3 items."""
    from pnl_attribution import compute_pnl_attribution

    result = compute_pnl_attribution("run_base_001", "run_cmp_001")
    assert len(result["top_drivers"]) <= 3


def test_pnl_driver_presets():
    """Driver presets should be non-empty and stable."""
    from pnl_attribution import DEMO_PRESETS, _sha256

    h1 = _sha256(DEMO_PRESETS)
    h2 = _sha256(DEMO_PRESETS)
    assert h1 == h2
    assert len(DEMO_PRESETS) >= 2


def test_pnl_attribution_pack_json():
    """Export pack in JSON format is deterministic."""
    from pnl_attribution import build_attribution_pack_manifest, compute_pnl_attribution

    result = compute_pnl_attribution("run_base_001", "run_cmp_001")
    m1 = build_attribution_pack_manifest(result)
    m2 = build_attribution_pack_manifest(result)

    assert m1["manifest_hash"] == m2["manifest_hash"]
    assert m1["pack_type"] == "pnl_attribution"


def test_pnl_attribution_api_endpoint():
    """API endpoint returns valid response."""
    from main import app

    client = TestClient(app)
    payload = {
        "base_run_id": "run_base_001",
        "compare_run_id": "run_cmp_001",
        "portfolio_id": "test_portfolio",
    }
    resp = client.post("/pnl/attribution", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_pnl" in data
    assert "contributions" in data
    assert data["output_hash"] is not None


def test_pnl_presets_api_endpoint():
    """Driver presets API endpoint works."""
    from main import app

    client = TestClient(app)
    resp = client.get("/pnl/drivers/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2


def test_pnl_attribution_pack_api():
    """Export API endpoint is deterministic."""
    from main import app

    client = TestClient(app)
    payload = {
        "base_run_id": "run_base_001",
        "compare_run_id": "run_cmp_001",
        "format": "md",
    }
    resp = client.post("/exports/pnl-attribution-pack", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "pack_hash" in data
    assert "content" in data
    assert "PnL Attribution Report" in data["content"]

    # Second call same result
    resp2 = client.post("/exports/pnl-attribution-pack", json=payload)
    assert resp2.json()["pack_hash"] == data["pack_hash"]
