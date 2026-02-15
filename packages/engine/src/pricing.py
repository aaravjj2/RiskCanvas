"""
Pricing module - Black-Scholes and basic asset pricing
"""

import math
from typing import Literal
from .config import round_to_precision


def _standard_normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _black_scholes_d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    """
    Calculate d1 and d2 for Black-Scholes formula.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
    
    Returns:
        Tuple of (d1, d2)
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def price_option(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call"
) -> float:
    """
    Price a European option using Black-Scholes model.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        Option price (rounded to configured precision)
    """
    # Handle edge cases
    if T <= 0:
        if option_type == "call":
            return round_to_precision(max(S - K, 0.0))
        else:
            return round_to_precision(max(K - S, 0.0))
    
    if sigma == 0:
        if option_type == "call":
            return round_to_precision(max(S - K * math.exp(-r * T), 0.0))
        else:
            return round_to_precision(max(K * math.exp(-r * T) - S, 0.0))
    
    d1, d2 = _black_scholes_d1_d2(S, K, T, r, sigma)
    
    if option_type == "call":
        price = S * _standard_normal_cdf(d1) - K * math.exp(-r * T) * _standard_normal_cdf(d2)
    elif option_type == "put":
        price = K * math.exp(-r * T) * _standard_normal_cdf(-d2) - S * _standard_normal_cdf(-d1)
    else:
        raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'")
    
    return round_to_precision(price)


def price_stock(current_price: float, quantity: float) -> float:
    """
    Calculate the current value of a stock position.
    
    Args:
        current_price: Current market price
        quantity: Number of shares
    
    Returns:
        Total value (rounded to configured precision)
    """
    return round_to_precision(current_price * quantity)
