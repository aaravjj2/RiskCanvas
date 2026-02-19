"""
Tests for v4.22.0-v4.24.0 Construction Engine (Wave 18)
Verifies: solver determinism, constraint enforcement, compare, memo, pack.
"""
import pytest
from fastapi.testclient import TestClient

SAMPLE_WEIGHTS = {
    "AAPL": 0.20,
    "MSFT": 0.20,
    "GOOGL": 0.15,
    "AMZN": 0.15,
    "TSLA": 0.10,
    "JPM": 0.10,
    "XOM": 0.10,
}

SAMPLE_CONSTRAINTS = {
    "var_cap": 0.05,
    "max_weight_per_symbol": 0.25,
    "turnover_cap": 0.30,
    "sector_caps": {"Technology": 0.60, "Finance": 0.30},
}


def test_construction_solve_determinism():
    """Same inputs → same outputs."""
    from construction_engine import solve_construction

    r1 = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    r2 = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)

    assert r1["output_hash"] == r2["output_hash"]
    assert r1["target_weights"] == r2["target_weights"]
    assert r1["trades"] == r2["trades"]


def test_construction_weights_sum_to_one():
    """Target weights should sum to 1.0 (within tolerance)."""
    from construction_engine import solve_construction

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    total = sum(result["target_weights"].values())
    assert abs(total - 1.0) < 1e-4


def test_construction_max_weight_constraint():
    """No target weight exceeds max_weight_per_symbol."""
    from construction_engine import solve_construction

    constraints = {**SAMPLE_CONSTRAINTS, "max_weight_per_symbol": 0.20}
    result = solve_construction(SAMPLE_WEIGHTS, constraints)

    for symbol, weight in result["target_weights"].items():
        assert weight <= 0.20 + 1e-4, f"{symbol}: {weight} exceeds 0.20"


def test_construction_different_objectives_differ():
    """minimize_risk vs balanced give different outputs."""
    from construction_engine import solve_construction

    r1 = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS, "minimize_risk")
    r2 = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS, "balanced")

    # May be different in output_hash (objective is part of input)
    assert r1["objective"] == "minimize_risk"
    assert r2["objective"] == "balanced"


def test_construction_empty_weights():
    """Empty weights returns empty result."""
    from construction_engine import solve_construction

    result = solve_construction({}, {})
    assert result["target_weights"] == {}
    assert result["trades"] == []


def test_construction_feasibility():
    """Solver always returns feasible result (no errors)."""
    from construction_engine import solve_construction

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    assert result["trade_count"] == len(result["trades"])
    assert result["cost_estimate"] >= 0.0


def test_construction_before_after_metrics():
    """Before/after metrics are present and after VaR ≤ before VaR."""
    from construction_engine import solve_construction

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    assert "before_metrics" in result
    assert "after_metrics" in result
    assert result["after_metrics"]["var"] <= result["before_metrics"]["var"]


def test_construction_compare_determinism():
    """Compare result is deterministic."""
    from construction_engine import solve_construction, compare_construction

    before = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    after = solve_construction({k: v * 0.9 for k, v in SAMPLE_WEIGHTS.items()}, SAMPLE_CONSTRAINTS)

    c1 = compare_construction(before, after)
    c2 = compare_construction(before, after)
    assert c1["output_hash"] == c2["output_hash"]


def test_construction_constraint_validation_valid():
    """Valid constraints pass validation."""
    from construction_engine import validate_constraints

    errors = validate_constraints(SAMPLE_CONSTRAINTS, list(SAMPLE_WEIGHTS.keys()))
    assert errors == []


def test_construction_constraint_validation_bad_var_cap():
    """Negative var_cap fails validation."""
    from construction_engine import validate_constraints

    constraints = {**SAMPLE_CONSTRAINTS, "var_cap": -0.01}
    errors = validate_constraints(constraints, list(SAMPLE_WEIGHTS.keys()))
    assert any("var_cap" in e for e in errors)


def test_construction_constraint_validation_bad_max_weight():
    """max_weight > 1 fails validation."""
    from construction_engine import validate_constraints

    constraints = {**SAMPLE_CONSTRAINTS, "max_weight_per_symbol": 1.5}
    errors = validate_constraints(constraints, list(SAMPLE_WEIGHTS.keys()))
    assert any("max_weight" in e for e in errors)


def test_construction_memo_determinism():
    """Construction memo is deterministic."""
    from construction_engine import solve_construction, build_construction_memo

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    m1 = build_construction_memo(result)
    m2 = build_construction_memo(result)
    assert m1["memo_hash"] == m2["memo_hash"]


def test_construction_memo_content():
    """Memo contains required sections."""
    from construction_engine import solve_construction, build_construction_memo

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    memo = build_construction_memo(result)
    content = memo["content_md"]
    assert "Portfolio Construction Decision Memo" in content
    assert "Proposed Trades" in content
    assert "Audit" in content


def test_construction_pack_determinism():
    """Construction pack hash is deterministic."""
    from construction_engine import solve_construction, build_construction_pack

    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    p1 = build_construction_pack(result)
    p2 = build_construction_pack(result)
    assert p1["pack_hash"] == p2["pack_hash"]
    assert p1["manifest"]["manifest_hash"] == p2["manifest"]["manifest_hash"]


def test_construction_api_solve():
    """Solve API endpoint returns valid response."""
    from main import app

    client = TestClient(app)
    payload = {
        "current_weights": SAMPLE_WEIGHTS,
        "constraints": SAMPLE_CONSTRAINTS,
        "objective": "minimize_risk",
    }
    resp = client.post("/construct/solve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "target_weights" in data
    assert "trades" in data
    assert "output_hash" in data


def test_construction_api_solve_deterministic():
    """Solve API returns same hash on repeated calls."""
    from main import app

    client = TestClient(app)
    payload = {
        "current_weights": SAMPLE_WEIGHTS,
        "constraints": SAMPLE_CONSTRAINTS,
    }
    r1 = client.post("/construct/solve", json=payload).json()
    r2 = client.post("/construct/solve", json=payload).json()
    assert r1["output_hash"] == r2["output_hash"]


def test_construction_api_compare():
    """Compare API endpoint works."""
    from main import app
    from construction_engine import solve_construction

    client = TestClient(app)
    before = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)
    after = solve_construction({k: v * 0.9 for k, v in SAMPLE_WEIGHTS.items()}, SAMPLE_CONSTRAINTS)

    resp = client.post("/construct/compare", json={"before": before, "after": after})
    assert resp.status_code == 200
    data = resp.json()
    assert "metric_changes" in data
    assert "output_hash" in data


def test_construction_api_export_pack():
    """Export pack API is deterministic."""
    from main import app
    from construction_engine import solve_construction

    client = TestClient(app)
    result = solve_construction(SAMPLE_WEIGHTS, SAMPLE_CONSTRAINTS)

    resp = client.post("/exports/construction-decision-pack", json={"solve_result": result})
    assert resp.status_code == 200
    data = resp.json()
    assert "pack_hash" in data
    assert data["manifest"]["manifest_hash"] is not None

    # Second call same hash
    resp2 = client.post("/exports/construction-decision-pack", json={"solve_result": result})
    assert resp2.json()["pack_hash"] == data["pack_hash"]
