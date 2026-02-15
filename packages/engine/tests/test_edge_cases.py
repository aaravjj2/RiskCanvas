"""
Edge-case tests for the RiskCanvas engine (v0.9 judge-proof reliability).

Covers:
  - Near-expiry options (T → 0)
  - Near-zero volatility (sigma → 0)
  - Deep in-the-money / out-of-the-money
  - Negative / zero interest rates
  - Empty and single-item portfolios
  - Boundary VaR inputs
  - Scenario-run edge inputs
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    price_option,
    price_stock,
    calculate_greeks,
    delta,
    gamma,
    vega,
    theta,
    rho,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    var_historical,
    scenario_run,
    round_to_precision,
    NUMERIC_PRECISION,
)


# ── Pricing edge cases ──────────────────────────────────────────────

class TestPricingEdgeCases:
    """Edge cases for price_option and price_stock."""

    # --- Near-expiry (T → 0) -------------------------------------------

    def test_call_at_expiry_itm(self):
        """At expiry, ITM call = max(S - K, 0)."""
        assert price_option(110, 100, 0.0, 0.05, 0.2, "call") == round_to_precision(10.0)

    def test_call_at_expiry_otm(self):
        """At expiry, OTM call = 0."""
        assert price_option(90, 100, 0.0, 0.05, 0.2, "call") == 0.0

    def test_put_at_expiry_itm(self):
        """At expiry, ITM put = max(K - S, 0)."""
        assert price_option(90, 100, 0.0, 0.05, 0.2, "put") == round_to_precision(10.0)

    def test_put_at_expiry_otm(self):
        """At expiry, OTM put = 0."""
        assert price_option(110, 100, 0.0, 0.05, 0.2, "put") == 0.0

    def test_call_at_expiry_atm(self):
        """ATM call at expiry = 0 (no intrinsic value)."""
        assert price_option(100, 100, 0.0, 0.05, 0.2, "call") == 0.0

    def test_near_expiry_call(self):
        """Very small T should be finite and >= max(S-K, 0)."""
        price = price_option(105, 100, 1e-6, 0.05, 0.2, "call")
        assert price >= round_to_precision(max(105 - 100, 0.0))
        assert math.isfinite(price)

    # --- Near-zero volatility (sigma → 0) -------------------------------

    def test_zero_vol_call_itm(self):
        """Zero vol, ITM call = max(S - K*exp(-rT), 0)."""
        expected = max(110 - 100 * math.exp(-0.05 * 0.25), 0.0)
        assert price_option(110, 100, 0.25, 0.05, 0.0, "call") == round_to_precision(expected)

    def test_zero_vol_call_otm(self):
        """Zero vol, OTM call = 0."""
        assert price_option(90, 100, 0.25, 0.05, 0.0, "call") == 0.0

    def test_zero_vol_put_itm(self):
        """Zero vol, ITM put = max(K*exp(-rT) - S, 0)."""
        expected = max(100 * math.exp(-0.05 * 0.25) - 90, 0.0)
        assert price_option(90, 100, 0.25, 0.05, 0.0, "put") == round_to_precision(expected)

    def test_zero_vol_put_otm(self):
        """Zero vol, OTM put = 0."""
        assert price_option(110, 100, 0.25, 0.05, 0.0, "put") == 0.0

    # --- Deep ITM / OTM -----------------------------------------------

    def test_deep_itm_call(self):
        """Deep ITM call approaches S - K*exp(-rT)."""
        price = price_option(500, 100, 1.0, 0.05, 0.2, "call")
        intrinsic = 500 - 100 * math.exp(-0.05 * 1.0)
        assert price >= round_to_precision(intrinsic * 0.99)

    def test_deep_otm_call(self):
        """Deep OTM call approaches 0."""
        price = price_option(10, 100, 0.25, 0.05, 0.2, "call")
        assert price < 0.01

    def test_deep_itm_put(self):
        """Deep ITM put has large value."""
        price = price_option(10, 100, 1.0, 0.05, 0.2, "put")
        intrinsic = 100 * math.exp(-0.05 * 1.0) - 10
        assert price >= round_to_precision(intrinsic * 0.99)

    def test_deep_otm_put(self):
        """Deep OTM put approaches 0."""
        price = price_option(500, 100, 0.25, 0.05, 0.2, "put")
        assert price < 0.01

    # --- Negative / zero interest rates ---------------------------------

    def test_negative_rate_call(self):
        """Negative risk-free rate still produces finite price."""
        price = price_option(100, 100, 0.5, -0.02, 0.25, "call")
        assert math.isfinite(price) and price > 0

    def test_zero_rate_call(self):
        """Zero rate call is valid."""
        price = price_option(100, 100, 0.5, 0.0, 0.25, "call")
        assert math.isfinite(price) and price > 0

    # --- price_stock ----------------------------------------------------

    def test_stock_zero_quantity(self):
        assert price_stock(150.0, 0) == 0.0

    def test_stock_negative_quantity_short(self):
        assert price_stock(150.0, -10) == round_to_precision(-1500.0)


# ── Greeks edge cases ────────────────────────────────────────────────

class TestGreeksEdgeCases:
    """Edge cases for Greeks."""

    def test_delta_at_expiry_itm_call(self):
        assert delta(110, 100, 0.0, 0.05, 0.2, "call") == round_to_precision(1.0)

    def test_delta_at_expiry_otm_call(self):
        assert delta(90, 100, 0.0, 0.05, 0.2, "call") == 0.0

    def test_delta_at_expiry_itm_put(self):
        assert delta(90, 100, 0.0, 0.05, 0.2, "put") == round_to_precision(-1.0)

    def test_delta_at_expiry_otm_put(self):
        assert delta(110, 100, 0.0, 0.05, 0.2, "put") == 0.0

    def test_gamma_at_expiry_zero(self):
        assert gamma(100, 100, 0.0, 0.05, 0.2) == 0.0

    def test_vega_at_expiry_zero(self):
        assert vega(100, 100, 0.0, 0.05, 0.2) == 0.0

    def test_greeks_zero_vol(self):
        """With zero vol, gamma/vega are zero; delta is binary."""
        g = gamma(110, 100, 0.5, 0.05, 0.0)
        v = vega(110, 100, 0.5, 0.05, 0.0)
        d = delta(110, 100, 0.5, 0.05, 0.0, "call")
        assert g == 0.0
        assert v == 0.0
        assert d == round_to_precision(1.0)

    def test_calculate_greeks_returns_all_keys(self):
        """calculate_greeks always returns all five greek keys."""
        result = calculate_greeks(100, 100, 0.5, 0.05, 0.2, "call")
        for key in ("delta", "gamma", "vega", "theta", "rho"):
            assert key in result
            assert math.isfinite(result[key])


# ── Portfolio edge cases ─────────────────────────────────────────────

class TestPortfolioEdgeCases:
    """Edge cases for portfolio_pnl and portfolio_greeks."""

    def test_empty_portfolio_pnl(self):
        """Empty portfolio → P&L = 0."""
        assert portfolio_pnl([]) == 0.0

    def test_empty_portfolio_greeks(self):
        """Empty portfolio → all greeks 0."""
        result = portfolio_greeks([])
        for key in ("delta", "gamma", "vega", "theta", "rho"):
            assert result[key] == 0.0

    def test_single_stock_pnl(self):
        """Single stock position P&L."""
        positions = [
            {"type": "stock", "quantity": 10, "current_price": 105, "purchase_price": 100}
        ]
        assert portfolio_pnl(positions) == round_to_precision(50.0)

    def test_mixed_positions_pnl(self):
        """Mix of stock and option positions."""
        positions = [
            {"type": "stock", "quantity": 5, "current_price": 110, "purchase_price": 100},
            {"type": "option", "quantity": 2, "current_price": 8.0, "purchase_price": 5.0},
        ]
        pnl = portfolio_pnl(positions)
        expected = (110 - 100) * 5 + (8.0 - 5.0) * 2  # 50 + 6 = 56
        assert pnl == round_to_precision(expected)

    def test_portfolio_greeks_stocks_only(self):
        """Stocks contribute no greeks."""
        positions = [{"type": "stock", "quantity": 100, "current_price": 50}]
        result = portfolio_greeks(positions)
        for key in ("delta", "gamma", "vega", "theta", "rho"):
            assert result[key] == 0.0

    def test_portfolio_greeks_with_options(self):
        """Options contribute non-zero delta."""
        positions = [
            {
                "type": "option",
                "quantity": 10,
                "S": 100,
                "K": 100,
                "T": 0.5,
                "r": 0.05,
                "sigma": 0.2,
                "option_type": "call",
            }
        ]
        result = portfolio_greeks(positions)
        assert result["delta"] > 0


# ── VaR edge cases ───────────────────────────────────────────────────

class TestVaREdgeCases:
    """Edge cases for VaR calculations."""

    def test_parametric_var_zero_vol(self):
        """Zero vol → VaR = 0."""
        assert var_parametric(1_000_000, 0.0, 0.95, 1) == 0.0

    def test_parametric_var_zero_value(self):
        """Zero portfolio value → VaR = 0."""
        assert var_parametric(0.0, 0.2, 0.95, 1) == 0.0

    def test_parametric_var_known_value(self):
        """Spot-check parametric VaR formula."""
        value = 1_000_000
        vol = 0.15
        z = 1.645  # 95%
        expected = value * vol * math.sqrt(1 / 252.0) * z
        result = var_parametric(value, vol, 0.95, 1)
        assert result == round_to_precision(expected)

    def test_historical_var_empty_returns(self):
        """Empty returns → VaR = 0."""
        assert var_historical(1_000_000, [], 0.95) == 0.0

    def test_historical_var_single_return(self):
        """Single return, still computes."""
        result = var_historical(1_000_000, [-0.05], 0.95)
        assert math.isfinite(result) and result >= 0

    def test_historical_var_all_positive(self):
        """All positive returns → VaR = 0 (no loss)."""
        returns = [0.01, 0.02, 0.005, 0.03]
        result = var_historical(1_000_000, returns, 0.95)
        assert result == 0.0


# ── Scenario edge cases ─────────────────────────────────────────────

class TestScenarioEdgeCases:
    """Edge cases for scenario_run."""

    def test_no_scenarios(self):
        """No scenarios → empty results."""
        positions = [{"type": "stock", "quantity": 10, "current_price": 100}]
        result = scenario_run(positions, [])
        assert result == []

    def test_empty_positions(self):
        """Empty positions → scenario change is 0."""
        scenarios = [{"name": "crash", "shock_type": "price", "parameters": {"factor": 0.9}}]
        result = scenario_run([], scenarios)
        assert len(result) == 1
        assert result[0]["change"] == 0.0

    def test_price_shock_basic(self):
        """Simple price shock changes portfolio value."""
        positions = [{"type": "stock", "quantity": 10, "current_price": 100}]
        scenarios = [{"name": "10pct_drop", "shock_type": "price", "parameters": {"price_change_pct": -10.0}}]
        results = scenario_run(positions, scenarios)
        assert len(results) == 1
        assert results[0]["change"] < 0  # price dropped → negative change

    def test_multiple_scenarios(self):
        """Multiple scenarios all execute."""
        positions = [{"type": "stock", "quantity": 5, "current_price": 200}]
        scenarios = [
            {"name": "up10", "shock_type": "price", "parameters": {"price_change_pct": 10.0}},
            {"name": "down10", "shock_type": "price", "parameters": {"price_change_pct": -10.0}},
        ]
        results = scenario_run(positions, scenarios)
        assert len(results) == 2
        assert results[0]["change"] > 0
        assert results[1]["change"] < 0
