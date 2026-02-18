"""
RiskCanvas Engine - Deterministic Risk Computation Core
"""

from .pricing import price_option, price_stock
from .greeks import calculate_greeks, delta, gamma, vega, theta, rho
from .portfolio import portfolio_pnl, portfolio_greeks
from .var import var_parametric, var_historical
from .scenario import scenario_run
from .config import NUMERIC_PRECISION, round_to_precision
from .bonds import (
    bond_price_from_yield,
    bond_yield_from_price,
    bond_duration,
    bond_convexity,
    bond_risk_metrics,
)
from .rates import (
    bootstrap_rates_curve,
    bond_price_from_curve,
)
from .stress import (
    list_presets as stress_list_presets,
    get_preset as stress_get_preset,
    apply_preset as stress_apply_preset,
)

__version__ = "0.1.0"

__all__ = [
    "price_option",
    "price_stock",
    "calculate_greeks",
    "delta",
    "gamma",
    "vega",
    "theta",
    "rho",
    "portfolio_pnl",
    "portfolio_greeks",
    "var_parametric",
    "var_historical",
    "scenario_run",
    "NUMERIC_PRECISION",
    "round_to_precision",
    "bond_price_from_yield",
    "bond_yield_from_price",
    "bond_duration",
    "bond_convexity",
    "bond_risk_metrics",
    # v3.4+ rates curve
    "bootstrap_rates_curve",
    "bond_price_from_curve",
    # v3.5+ stress library
    "stress_list_presets",
    "stress_get_preset",
    "stress_apply_preset",
]
