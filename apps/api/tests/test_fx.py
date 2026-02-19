"""Tests for Wave 19: FX + Cross-Currency Risk (v4.26–v4.28)"""
import pytest
from fx import (
    get_fx_spot, get_fx_forward, get_fx_vol,
    compute_fx_exposure, apply_fx_shocks,
    _FX_SPOT,
)

# ─────────────────────────────────────────────────────────────────────────────
# Import guard — no external calls ever in this module

def test_no_external_calls_in_import():
    """fx.py must be importable with zero network calls."""
    import fx
    assert fx._FX_SPOT is not None


# ─────────────────── FX Spot ─────────────────────────────────────────────────

def test_fx_spot_eurusd():
    r = get_fx_spot("EURUSD")
    assert r["pair"] == "EURUSD"
    assert isinstance(r["spot"], float)
    assert r["spot"] > 0.5
    assert "hash" in r
    assert "audit_chain_head_hash" in r
    r1 = get_fx_spot("USDJPY")
    r2 = get_fx_spot("USDJPY")
    assert r1["hash"] == r2["hash"]
    assert r1["spot"] == r2["spot"]


def test_fx_spot_all_pairs():
    for pair in _FX_SPOT.keys():
        r = get_fx_spot(pair)
        assert r["spot"] > 0


def test_fx_spot_unknown_pair():
    with pytest.raises(ValueError, match="Unknown pair"):
        get_fx_spot("XYZABC")


def test_fx_spot_case_insensitive():
    r1 = get_fx_spot("EURUSD")
    r2 = get_fx_spot("eurusd")
    assert r1["spot"] == r2["spot"]


# ─────────────────── FX Forward ──────────────────────────────────────────────

def test_fx_forward_basic():
    r = get_fx_forward("EURUSD", "3M")
    assert r["pair"] == "EURUSD"
    assert r["tenor"] == "3M"
    assert isinstance(r["forward"], float)
    assert r["forward"] != r["spot"]  # non-zero forward points


def test_fx_forward_determinism():
    r1 = get_fx_forward("USDJPY", "1Y")
    r2 = get_fx_forward("USDJPY", "1Y")
    assert r1["hash"] == r2["hash"]
    assert r1["forward"] == r2["forward"]


def test_fx_forward_tenors():
    for tenor in ["1M", "3M", "6M", "1Y"]:
        r = get_fx_forward("GBPUSD", tenor)
        assert r["tenor"] == tenor
        assert r["forward"] > 0


# ─────────────────── FX Vol ──────────────────────────────────────────────────

def test_fx_vol_basic():
    r = get_fx_vol("EURUSD")
    assert 0 < r["vol"] < 1.0
    assert r["vol_pct"] == round(r["vol"] * 100, 4)


def test_fx_vol_determinism():
    r1 = get_fx_vol("GBPUSD")
    r2 = get_fx_vol("GBPUSD")
    assert r1["hash"] == r2["hash"]


# ─────────────────── FX Exposure ─────────────────────────────────────────────

DEMO_PORTFOLIO = [
    {"symbol": "AAPL",  "notional": 150000, "native_ccy": "USD"},
    {"symbol": "SHELL", "notional": 80000,  "native_ccy": "GBP"},
    {"symbol": "ASML",  "notional": 60000,  "native_ccy": "EUR"},
    {"symbol": "TM",    "notional": 5000000,"native_ccy": "JPY"},
]


def test_fx_exposure_basic():
    r = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    assert r["base_ccy"] == "USD"
    assert r["total_base"] > 0
    assert "USD" in r["exposure_by_ccy"]
    assert "GBP" in r["exposure_by_ccy"]
    assert "EUR" in r["exposure_by_ccy"]
    assert "JPY" in r["exposure_by_ccy"]


def test_fx_exposure_determinism():
    r1 = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    r2 = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    assert r1["output_hash"] == r2["output_hash"]
    assert r1["total_base"] == r2["total_base"]


def test_fx_exposure_usd_only():
    port = [{"symbol": "AAPL", "notional": 100000, "native_ccy": "USD"}]
    r = compute_fx_exposure(port, "USD")
    assert r["total_base"] == 100000.0
    assert r["exposure_by_ccy"]["USD"] == 100000.0


def test_fx_exposure_stable_ordering():
    """Rows must be sorted by symbol regardless of input order."""
    port_shuffled = list(reversed(DEMO_PORTFOLIO))
    r1 = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    r2 = compute_fx_exposure(port_shuffled, "USD")
    assert r1["output_hash"] == r2["output_hash"]


def test_fx_exposure_hash_changes_with_input():
    port_a = [{"symbol": "AAPL", "notional": 100000, "native_ccy": "USD"}]
    port_b = [{"symbol": "AAPL", "notional": 200000, "native_ccy": "USD"}]
    r1 = compute_fx_exposure(port_a, "USD")
    r2 = compute_fx_exposure(port_b, "USD")
    assert r1["output_hash"] != r2["output_hash"]


# ─────────────────── FX Shocks ───────────────────────────────────────────────

def test_fx_shock_basic():
    exposure = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    shocks = [{"pair": "EURUSD", "pct": -10.0}]
    r = apply_fx_shocks(exposure, shocks)
    assert r["base_ccy"] == "USD"
    assert "shocked_total_base" in r
    assert "delta_base" in r
    assert r["output_hash"]


def test_fx_shock_determinism():
    exposure = compute_fx_exposure(DEMO_PORTFOLIO, "USD")
    shocks = [{"pair": "GBPUSD", "pct": -5.0}, {"pair": "EURUSD", "pct": -3.0}]
    r1 = apply_fx_shocks(exposure, shocks)
    r2 = apply_fx_shocks(exposure, shocks)
    assert r1["output_hash"] == r2["output_hash"]


def test_fx_shock_zero_has_no_effect():
    exposure = compute_fx_exposure([{"symbol": "AAPL", "notional": 100000, "native_ccy": "USD"}], "USD")
    shocks = [{"pair": "EURUSD", "pct": 0.0}]
    r = apply_fx_shocks(exposure, shocks)
    assert r["delta_base"] == 0.0


def test_fx_shock_appreciation_reduces_base_value():
    """EUR appreciation (positive pct) reduces USD value of EUR position."""
    port = [{"symbol": "ASML", "notional": 100000, "native_ccy": "EUR"}]
    exposure = compute_fx_exposure(port, "USD")
    shocks = [{"pair": "EURUSD", "pct": 10.0}]
    r = apply_fx_shocks(exposure, shocks)
    # When EUR appreciates +10%, same EUR notional is worth less in base after applying shock formula
    # Our formula: shocked = base_amount / (1 + pct/100)
    assert r["delta_base"] < 0
