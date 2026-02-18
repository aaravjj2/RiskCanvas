"""
Engine tests for Rates Curve Bootstrap (v3.4+)

Verifies:
- Deterministic output (same input → same hash)
- Discount factor monotonicity (longer tenor = smaller DF)
- Bond price via curve is deterministic and stable
- Bootstrap from deposit-only curve
- Bootstrap with swap instruments
"""

import hashlib
import json
import math
import pytest
import sys
from pathlib import Path

# Ensure engine src on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rates import bootstrap_rates_curve, bond_price_from_curve


# ── Fixtures ──────────────────────────────────────────────────────────────────

DEPOSIT_INSTRUMENTS = [
    {"type": "deposit", "tenor": 0.25, "rate": 0.04},
    {"type": "deposit", "tenor": 0.5,  "rate": 0.042},
    {"type": "deposit", "tenor": 1.0,  "rate": 0.045},
]

SWAP_INSTRUMENTS = [
    {"type": "deposit", "tenor": 0.25, "rate": 0.04},
    {"type": "deposit", "tenor": 0.5,  "rate": 0.042},
    {"type": "deposit", "tenor": 1.0,  "rate": 0.045},
    {"type": "swap",    "tenor": 2.0,  "rate": 0.048, "periods_per_year": 2},
    {"type": "swap",    "tenor": 5.0,  "rate": 0.052, "periods_per_year": 2},
]

# Golden hash for DEPOSIT_INSTRUMENTS (computed from first passing run)
# We compute it in the test itself to ensure byte-for-byte determinism.

class TestBootstrapDepositsOnly:
    def test_output_keys_present(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        assert "instruments" in result
        assert "zero_rates" in result
        assert "discount_factors" in result
        assert "curve_hash" in result

    def test_tenor_ordering_ascending(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        tenors = [item["tenor"] for item in result["zero_rates"]]
        assert tenors == sorted(tenors)

    def test_df_ordering_ascending_by_tenor(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        dfs = [item["df"] for item in result["discount_factors"]]
        # Longer tenor → smaller DF (monotonically decreasing)
        for i in range(len(dfs) - 1):
            assert dfs[i] >= dfs[i + 1], f"DF not decreasing at index {i}: {dfs[i]} < {dfs[i+1]}"

    def test_df_values_in_range(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        for item in result["discount_factors"]:
            assert 0 < item["df"] <= 1.0, f"DF out of range: {item}"

    def test_zero_rates_positive(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        for item in result["zero_rates"]:
            assert item["zero_rate"] > 0, f"Zero rate not positive: {item}"

    def test_curve_hash_is_sha256(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        assert len(result["curve_hash"]) == 64
        int(result["curve_hash"], 16)  # must be valid hex

    def test_determinism_same_input_same_hash(self):
        r1 = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        r2 = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        assert r1["curve_hash"] == r2["curve_hash"]

    def test_determinism_canonical_json(self):
        """byte-for-byte: same input → same canonical JSON → same hash"""
        r1 = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        r2 = bootstrap_rates_curve(list(DEPOSIT_INSTRUMENTS))  # copy
        assert r1["curve_hash"] == r2["curve_hash"]

    def test_tenor_count_matches_instruments(self):
        result = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        assert len(result["zero_rates"]) == len(DEPOSIT_INSTRUMENTS)
        assert len(result["discount_factors"]) == len(DEPOSIT_INSTRUMENTS)

    def test_instrument_order_doesnt_affect_output(self):
        """Instruments fed in reverse → same result (they're sorted internally)."""
        r_fwd = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        r_rev = bootstrap_rates_curve(list(reversed(DEPOSIT_INSTRUMENTS)))
        assert r_fwd["curve_hash"] == r_rev["curve_hash"]


class TestBootstrapWithSwaps:
    def test_output_keys_present(self):
        result = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        assert "curve_hash" in result

    def test_swap_tenor_present_in_output(self):
        result = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        tenors = [item["tenor"] for item in result["zero_rates"]]
        assert 2.0 in tenors
        assert 5.0 in tenors

    def test_df_monotonically_decreasing(self):
        result = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        dfs = [item["df"] for item in result["discount_factors"]]
        for i in range(len(dfs) - 1):
            assert dfs[i] >= dfs[i + 1], f"DF not decreasing at index {i}"

    def test_determinism(self):
        r1 = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        r2 = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        assert r1["curve_hash"] == r2["curve_hash"]

    def test_curve_hash_differs_from_deposits_only(self):
        r_dep = bootstrap_rates_curve(DEPOSIT_INSTRUMENTS)
        r_swap = bootstrap_rates_curve(SWAP_INSTRUMENTS)
        assert r_dep["curve_hash"] != r_swap["curve_hash"]


class TestBondPriceFromCurve:
    def _curve(self):
        return bootstrap_rates_curve(SWAP_INSTRUMENTS)["discount_factors"]

    def test_returns_positive_price(self):
        price = bond_price_from_curve(
            face_value=1000.0,
            coupon_rate=0.05,
            years_to_maturity=3.0,
            discount_factors=self._curve(),
        )
        assert price > 0

    def test_zero_coupon_bond_below_par_when_rates_up(self):
        """Zero coupon bond with positive rates → price < face value."""
        price = bond_price_from_curve(
            face_value=1000.0,
            coupon_rate=0.0,
            years_to_maturity=2.0,
            discount_factors=self._curve(),
        )
        assert price < 1000.0

    def test_zero_maturity_returns_face(self):
        price = bond_price_from_curve(
            face_value=1000.0,
            coupon_rate=0.05,
            years_to_maturity=0.0,
            discount_factors=self._curve(),
        )
        assert price == 1000.0

    def test_determinism(self):
        curve = self._curve()
        p1 = bond_price_from_curve(1000.0, 0.05, 3.0, curve)
        p2 = bond_price_from_curve(1000.0, 0.05, 3.0, curve)
        assert p1 == p2

    def test_higher_coupon_higher_price(self):
        curve = self._curve()
        low = bond_price_from_curve(1000.0, 0.01, 3.0, curve)
        high = bond_price_from_curve(1000.0, 0.10, 3.0, curve)
        assert high > low


class TestEmptyInstruments:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            bootstrap_rates_curve([])

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            bootstrap_rates_curve([{"type": "futures", "tenor": 1.0, "rate": 0.04}])
