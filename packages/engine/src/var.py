"""
Value at Risk (VaR) calculations
"""

import math
from typing import Any
from .config import round_to_precision, FIXED_SEED


def var_parametric(
    portfolio_value: float,
    volatility: float,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> float:
    """
    Calculate parametric VaR (assumes normal distribution).
    
    Args:
        portfolio_value: Current portfolio value
        volatility: Annual volatility (standard deviation)
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        time_horizon_days: Time horizon in days
    
    Returns:
        VaR amount (positive number representing potential loss)
    """
    # Z-scores for common confidence levels
    z_scores = {
        0.90: 1.28,
        0.95: 1.645,
        0.99: 2.326,
    }
    
    z_score = z_scores.get(confidence_level, 1.645)
    
    # Scale volatility to time horizon
    vol_scaled = volatility * math.sqrt(time_horizon_days / 252.0)
    
    var_value = portfolio_value * vol_scaled * z_score
    
    return round_to_precision(var_value)


def var_historical(
    current_value: float,
    historical_returns: list[float],
    confidence_level: float = 0.95
) -> float:
    """
    Calculate historical VaR based on historical returns.
    
    Args:
        current_value: Current portfolio value
        historical_returns: List of historical returns (as decimals, e.g., 0.02 for 2%)
        confidence_level: Confidence level (e.g., 0.95 for 95%)
    
    Returns:
        VaR amount (positive number representing potential loss)
    """
    if not historical_returns:
        return round_to_precision(0.0)
    
    # Sort returns (ascending, so worst losses are first)
    sorted_returns = sorted(historical_returns)
    
    # Find the percentile corresponding to (1 - confidence_level)
    percentile_index = int(len(sorted_returns) * (1 - confidence_level))
    percentile_index = max(0, min(percentile_index, len(sorted_returns) - 1))
    
    var_return = sorted_returns[percentile_index]
    
    # Convert return to dollar loss (negative return = loss)
    var_value = -current_value * var_return if var_return < 0 else 0.0
    
    return round_to_precision(var_value)
