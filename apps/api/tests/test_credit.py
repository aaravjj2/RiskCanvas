"""Tests for Wave 20: Credit + Spread Risk Lite (v4.30–v4.32)"""
import pytest
from credit import (
    get_curve, list_curves, compute_credit_risk,
    _interpolate_spread, _SPREAD_CURVES,
)


def test_list_curves():
    r = list_curves()
    assert "curves" in r
    assert len(r["curves"]) >= 4
    ids = [c["curve_id"] for c in r["curves"]]
    assert "usd_ig" in ids
    assert "usd_hy" in ids
    assert "eur_ig" in ids
    assert "em_hy" in ids


def test_list_curves_determinism():
    r1 = list_curves()
    r2 = list_curves()
    assert r1["curves"] == r2["curves"]


def test_get_curve_usd_ig():
    r = get_curve("usd_ig")
    assert r["curve_id"] == "usd_ig"
    assert r["currency"] == "USD"
    assert len(r["nodes"]) >= 5
    assert "hash" in r
    assert "audit_chain_head_hash" in r


def test_get_curve_hash_stable():
    r1 = get_curve("usd_hy")
    r2 = get_curve("usd_hy")
    assert r1["hash"] == r2["hash"]


def test_get_curve_nodes_sorted():
    r = get_curve("eur_ig")
    tenors = [n["tenor_years"] for n in r["nodes"]]
    assert tenors == sorted(tenors)


def test_get_curve_unknown():
    with pytest.raises(ValueError, match="Unknown curve_id"):
        get_curve("xyz_unknown")


def test_interpolate_spread_at_node():
    nodes = {1: 32.5, 5: 78.3, 10: 108.4}
    assert _interpolate_spread(nodes, 5) == 78.3


def test_interpolate_spread_between_nodes():
    nodes = {1: 32.5, 5: 78.3}
    result = _interpolate_spread(nodes, 3.0)
    # linear interp: 32.5 + (3-1)/(5-1) * (78.3-32.5)
    expected = 32.5 + 0.5 * (78.3 - 32.5)
    assert abs(result - expected) < 0.01


def test_interpolate_spread_below_min():
    nodes = {2: 45.0, 10: 110.0}
    assert _interpolate_spread(nodes, 0.5) == 45.0


def test_interpolate_spread_above_max():
    nodes = {2: 45.0, 10: 110.0}
    assert _interpolate_spread(nodes, 15.0) == 110.0


DEMO_POSITIONS = [
    {"symbol": "CORP_A", "notional": 1000000, "tenor_years": 5},
    {"symbol": "CORP_B", "notional": 500000,  "tenor_years": 3},
    {"symbol": "CORP_C", "notional": 750000,  "tenor_years": 7},
]


def test_credit_risk_basic():
    r = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    assert r["curve_id"] == "usd_ig"
    assert len(r["positions"]) == 3
    assert r["total_spread_dv01"] > 0
    assert r["total_shock_25bps_usd"] > 0
    assert r["total_shock_100bps_usd"] > 0
    assert "output_hash" in r
    assert "audit_chain_head_hash" in r


def test_credit_risk_determinism():
    r1 = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    r2 = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    assert r1["output_hash"] == r2["output_hash"]
    assert r1["total_spread_dv01"] == r2["total_spread_dv01"]


def test_credit_risk_stable_ordering():
    pos_shuffled = list(reversed(DEMO_POSITIONS))
    r1 = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    r2 = compute_credit_risk(pos_shuffled, "usd_ig")
    assert r1["output_hash"] == r2["output_hash"]


def test_credit_risk_hy_higher_dv01():
    """HY has higher spreads, so same positions give different hash."""
    r_ig = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    r_hy = compute_credit_risk(DEMO_POSITIONS, "usd_hy")
    assert r_ig["output_hash"] != r_hy["output_hash"]
    # HY spread is much higher => different spreads in rows
    assert r_hy["positions"][0]["spread_bps"] > r_ig["positions"][0]["spread_bps"]


def test_credit_risk_unknown_curve():
    with pytest.raises(ValueError):
        compute_credit_risk(DEMO_POSITIONS, "nonexistent")


def test_credit_risk_shock_scaling():
    r = compute_credit_risk(DEMO_POSITIONS, "usd_ig")
    # 100bps shock should be 4x the 25bps shock (approximately)
    ratio = r["total_shock_100bps_usd"] / r["total_shock_25bps_usd"]
    assert abs(ratio - 4.0) < 0.01


def test_credit_risk_all_curves():
    for curve_id in _SPREAD_CURVES.keys():
        r = compute_credit_risk(DEMO_POSITIONS[:1], curve_id)
        assert r["total_spread_dv01"] > 0
