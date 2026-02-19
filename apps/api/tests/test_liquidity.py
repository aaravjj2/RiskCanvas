"""Tests for Wave 21: Liquidity + Transaction Cost Models (v4.34–v4.36)"""
import pytest
from liquidity import (
    compute_haircut, compute_tcost, compute_tradeoff,
    _LIQ_TIERS, _TIER_LABELS,
)


DEMO_PORTFOLIO = [
    {"symbol": "AAPL",   "notional": 500000},
    {"symbol": "TSLA",   "notional": 200000},
    {"symbol": "CORP_A", "notional": 300000},
    {"symbol": "CORP_C", "notional": 100000},
]

DEMO_TRADES = [
    {"symbol": "AAPL",   "notional": 500000, "side": "sell"},
    {"symbol": "TSLA",   "notional": 200000, "side": "buy"},
    {"symbol": "CORP_A", "notional": 300000, "side": "sell"},
]


# ─────────────────── Haircut ───────────────────────────────────────────────────


def test_haircut_basic():
    r = compute_haircut(DEMO_PORTFOLIO)
    assert len(r["portfolio_rows"]) == 4
    assert r["total_notional"] == 1100000.0
    assert r["total_haircut"] > 0
    assert r["total_net_after_haircut"] < r["total_notional"]
    assert "output_hash" in r
    assert "audit_chain_head_hash" in r


def test_haircut_determinism():
    r1 = compute_haircut(DEMO_PORTFOLIO)
    r2 = compute_haircut(DEMO_PORTFOLIO)
    assert r1["output_hash"] == r2["output_hash"]


def test_haircut_stable_ordering():
    shuffled = list(reversed(DEMO_PORTFOLIO))
    r1 = compute_haircut(DEMO_PORTFOLIO)
    r2 = compute_haircut(shuffled)
    assert r1["output_hash"] == r2["output_hash"]


def test_haircut_tier1_lower_than_tier4():
    tier1 = [{"symbol": "AAPL", "notional": 1000000}]
    tier4 = [{"symbol": "CORP_C", "notional": 1000000}]
    r1 = compute_haircut(tier1)
    r4 = compute_haircut(tier4)
    assert r4["total_haircut"] > r1["total_haircut"]


def test_haircut_net_value_positive():
    r = compute_haircut(DEMO_PORTFOLIO)
    for row in r["portfolio_rows"]:
        assert row["net_value"] >= 0
        assert row["net_value"] < row["notional"]


def test_haircut_tier_labels_present():
    r = compute_haircut(DEMO_PORTFOLIO)
    for row in r["portfolio_rows"]:
        assert row["tier_label"] in _TIER_LABELS.values()


# ─────────────────── TCost ─────────────────────────────────────────────────────


def test_tcost_basic():
    r = compute_tcost(DEMO_TRADES)
    assert len(r["trades"]) == 3
    assert r["total_estimated_cost_usd"] > 0
    assert "output_hash" in r
    assert "audit_chain_head_hash" in r


def test_tcost_determinism():
    r1 = compute_tcost(DEMO_TRADES)
    r2 = compute_tcost(DEMO_TRADES)
    assert r1["output_hash"] == r2["output_hash"]


def test_tcost_stable_ordering():
    shuffled = list(reversed(DEMO_TRADES))
    r1 = compute_tcost(DEMO_TRADES)
    r2 = compute_tcost(shuffled)
    assert r1["output_hash"] == r2["output_hash"]


def test_tcost_illiquid_higher_cost():
    """Illiquid symbol should have higher cost bps than liquid."""
    liquid = [{"symbol": "AAPL", "notional": 1000000, "side": "sell"}]
    illiquid = [{"symbol": "CORP_C", "notional": 1000000, "side": "sell"}]
    r_liq = compute_tcost(liquid)
    r_illiq = compute_tcost(illiquid)
    assert r_illiq["total_estimated_cost_usd"] > r_liq["total_estimated_cost_usd"]


def test_tcost_positive_costs():
    r = compute_tcost(DEMO_TRADES)
    for t in r["trades"]:
        assert t["estimated_cost_usd"] > 0
        assert t["total_cost_bps"] > 0


def test_tcost_components_sum():
    r = compute_tcost(DEMO_TRADES)
    for t in r["trades"]:
        component_sum = t["spread_component_bps"] + t["impact_component_bps"]
        assert abs(component_sum - t["total_cost_bps"]) < 0.001


# ─────────────────── Tradeoff ─────────────────────────────────────────────────


def test_tradeoff_basic():
    r = compute_tradeoff(DEMO_TRADES, 450000.0)
    assert r["total_risk_reduction_usd"] == 450000.0
    assert r["total_cost_usd"] > 0
    assert r["risk_reduction_to_cost_ratio"] > 0
    assert r["recommendation"] in ("EXECUTE — risk reduction > 10x cost",
                                    "REVIEW — risk reduction > 3x cost",
                                    "CAUTION — cost is high relative to risk reduction")
    assert "output_hash" in r
    assert "audit_chain_head_hash" in r


def test_tradeoff_determinism():
    r1 = compute_tradeoff(DEMO_TRADES, 450000.0)
    r2 = compute_tradeoff(DEMO_TRADES, 450000.0)
    assert r1["output_hash"] == r2["output_hash"]


def test_tradeoff_high_ratio_executes():
    """If risk reduction >> cost, recommendation should be EXECUTE."""
    r = compute_tradeoff(DEMO_TRADES, 50000000.0)
    assert "EXECUTE" in r["recommendation"]


def test_tradeoff_low_ratio_cautions():
    """If cost > risk reduction, recommendation should be CAUTION."""
    r = compute_tradeoff(DEMO_TRADES, 10.0)
    assert "CAUTION" in r["recommendation"]
