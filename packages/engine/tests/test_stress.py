"""
Engine tests for Stress Library (v3.5+)

Verifies:
- All preset definitions are deterministic (stable hash)
- apply_preset produces correct shocked values
- apply_preset is deterministic (same input → same output hash)
- Edge cases: empty portfolio, unknown preset
"""

import hashlib
import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stress import list_presets, get_preset, apply_preset


# ── Fixtures ──────────────────────────────────────────────────────────────────

EQUITY_PORTFOLIO = {
    "assets": [
        {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0, "current_price": 150.0},
        {"symbol": "MSFT", "type": "stock", "quantity": 5, "price": 300.0, "current_price": 300.0},
    ]
}

OPTION_PORTFOLIO = {
    "assets": [
        {
            "symbol": "AAPL_CALL",
            "type": "option",
            "option_type": "call",
            "quantity": 1,
            "strike": 155.0,
            "price": 150.0,
            "current_price": 150.0,
            "volatility": 0.20,
            "risk_free_rate": 0.05,
            "time_to_expiry": 0.25,
        }
    ]
}

BOND_PORTFOLIO = {
    "assets": [
        {
            "symbol": "BOND1",
            "type": "bond",
            "quantity": 1,
            "face_value": 1000.0,
            "coupon_rate": 0.05,
            "years_to_maturity": 10.0,
            "yield_to_maturity": 0.054,
        }
    ]
}


EXPECTED_PRESET_IDS = {
    "rates_up_200bp", "rates_down_200bp", "vol_up_25pct", "equity_down_10pct", "credit_spread_up_100bp"
}


class TestPresetDefinitions:
    def test_list_presets_count(self):
        presets = list_presets()
        assert len(presets) == 5

    def test_list_presets_ids(self):
        preset_ids = {p["preset_id"] for p in list_presets()}
        assert preset_ids == EXPECTED_PRESET_IDS

    def test_each_preset_has_hash(self):
        for p in list_presets():
            assert "preset_hash" in p
            assert len(p["preset_hash"]) == 64

    def test_preset_hashes_stable(self):
        """Same presets → same hashes (byte-for-byte determinism)."""
        h1 = {p["preset_id"]: p["preset_hash"] for p in list_presets()}
        h2 = {p["preset_id"]: p["preset_hash"] for p in list_presets()}
        assert h1 == h2

    def test_presets_sorted_by_id(self):
        preset_ids = [p["preset_id"] for p in list_presets()]
        assert preset_ids == sorted(preset_ids)

    def test_get_preset_returns_correct(self):
        p = get_preset("rates_up_200bp")
        assert p is not None
        assert p["preset_id"] == "rates_up_200bp"

    def test_get_preset_unknown_returns_none(self):
        assert get_preset("nonexistent_preset") is None

    def test_preset_shocks_schema(self):
        for p in list_presets():
            shocks = p["shocks"]
            assert "interest_rate_shift_bp" in shocks
            assert "equity_shift_pct" in shocks
            assert "volatility_shift_pct" in shocks
            assert "credit_spread_shift_bp" in shocks

    def test_rates_up_shock_value(self):
        p = get_preset("rates_up_200bp")
        assert p["shocks"]["interest_rate_shift_bp"] == 200

    def test_rates_down_shock_value(self):
        p = get_preset("rates_down_200bp")
        assert p["shocks"]["interest_rate_shift_bp"] == -200

    def test_vol_up_shock_value(self):
        p = get_preset("vol_up_25pct")
        assert p["shocks"]["volatility_shift_pct"] == 0.25

    def test_equity_down_shock_value(self):
        p = get_preset("equity_down_10pct")
        assert p["shocks"]["equity_shift_pct"] == -0.10

    def test_credit_spread_up_shock_value(self):
        p = get_preset("credit_spread_up_100bp")
        assert p["shocks"]["credit_spread_shift_bp"] == 100


class TestApplyPreset:
    def test_equity_down_reduces_price(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        stressed = result["stressed_portfolio"]["assets"]
        for orig, stressed_asset in zip(EQUITY_PORTFOLIO["assets"], stressed):
            assert stressed_asset["current_price"] < orig["current_price"]

    def test_equity_down_10pct_exact_value(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        aapl = result["stressed_portfolio"]["assets"][0]
        assert abs(aapl["current_price"] - 150.0 * 0.90) < 1e-4

    def test_rates_up_increases_bond_ytm(self):
        result = apply_preset("rates_up_200bp", BOND_PORTFOLIO)
        bond = result["stressed_portfolio"]["assets"][0]
        original_ytm = BOND_PORTFOLIO["assets"][0]["yield_to_maturity"]
        assert bond["yield_to_maturity"] > original_ytm

    def test_rates_up_200bp_exact_ytm(self):
        result = apply_preset("rates_up_200bp", BOND_PORTFOLIO)
        bond = result["stressed_portfolio"]["assets"][0]
        expected = BOND_PORTFOLIO["assets"][0]["yield_to_maturity"] + 0.02
        assert abs(bond["yield_to_maturity"] - expected) < 1e-8

    def test_vol_up_increases_option_vol(self):
        result = apply_preset("vol_up_25pct", OPTION_PORTFOLIO)
        opt = result["stressed_portfolio"]["assets"][0]
        assert opt["volatility"] > OPTION_PORTFOLIO["assets"][0]["volatility"]

    def test_vol_up_25pct_exact_vol(self):
        result = apply_preset("vol_up_25pct", OPTION_PORTFOLIO)
        opt = result["stressed_portfolio"]["assets"][0]
        expected_vol = 0.20 * 1.25
        assert abs(opt["volatility"] - expected_vol) < 1e-8

    def test_stress_preset_id_set_in_output(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        assert result["stressed_portfolio"]["stress_preset_id"] == "equity_down_10pct"

    def test_input_hash_present(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        assert "input_hash" in result
        assert len(result["input_hash"]) == 64

    def test_stressed_input_hash_differs_from_input_hash(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        assert result["input_hash"] != result["stressed_input_hash"]

    def test_determinism_same_inputs_same_hashes(self):
        r1 = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        r2 = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        assert r1["input_hash"] == r2["input_hash"]
        assert r1["stressed_input_hash"] == r2["stressed_input_hash"]

    def test_result_contains_shocks_applied(self):
        result = apply_preset("equity_down_10pct", EQUITY_PORTFOLIO)
        assert "shocks_applied" in result
        assert result["shocks_applied"]["equity_shift_pct"] == -0.10

    def test_unknown_preset_raises(self):
        with pytest.raises(ValueError):
            apply_preset("nonexistent", EQUITY_PORTFOLIO)

    def test_rates_down_decreases_bond_ytm(self):
        result = apply_preset("rates_down_200bp", BOND_PORTFOLIO)
        bond = result["stressed_portfolio"]["assets"][0]
        original_ytm = BOND_PORTFOLIO["assets"][0]["yield_to_maturity"]
        assert bond["yield_to_maturity"] < original_ytm

    def test_no_shock_when_zero(self):
        """credit_spread shock doesn't change equity price."""
        result = apply_preset("credit_spread_up_100bp", EQUITY_PORTFOLIO)
        orig_price = EQUITY_PORTFOLIO["assets"][0]["current_price"]
        stressed_price = result["stressed_portfolio"]["assets"][0]["current_price"]
        assert orig_price == stressed_price
