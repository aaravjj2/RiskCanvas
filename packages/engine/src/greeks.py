"""
Greeks calculation for options
"""

import math
from typing import Literal
from .config import round_to_precision
from .pricing import _standard_normal_cdf, _black_scholes_d1_d2


def _standard_normal_pdf(x: float) -> float:
    """Standard normal probability density function"""
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


def delta(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["call", "put"] = "call") -> float:
    """
    Calculate option delta.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        Delta (rounded to configured precision)
    """
    if T <= 0 or sigma == 0:
        # At expiration or zero vol, delta is binary
        if option_type == "call":
            return round_to_precision(1.0 if S > K else 0.0)
        else:
            return round_to_precision(-1.0 if S < K else 0.0)
    
    d1, _ = _black_scholes_d1_d2(S, K, T, r, sigma)
    
    if option_type == "call":
        return round_to_precision(_standard_normal_cdf(d1))
    elif option_type == "put":
        return round_to_precision(_standard_normal_cdf(d1) - 1.0)
    else:
        raise ValueError(f"Invalid option_type: {option_type}")


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate option gamma (same for calls and puts).
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
    
    Returns:
        Gamma (rounded to configured precision)
    """
    if T <= 0 or sigma == 0:
        return round_to_precision(0.0)
    
    d1, _ = _black_scholes_d1_d2(S, K, T, r, sigma)
    gamma_val = _standard_normal_pdf(d1) / (S * sigma * math.sqrt(T))
    return round_to_precision(gamma_val)


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate option vega (same for calls and puts).
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
    
    Returns:
        Vega (rounded to configured precision, per 1% change in volatility)
    """
    if T <= 0 or sigma == 0:
        return round_to_precision(0.0)
    
    d1, _ = _black_scholes_d1_d2(S, K, T, r, sigma)
    vega_val = S * _standard_normal_pdf(d1) * math.sqrt(T) / 100.0  # Per 1% change
    return round_to_precision(vega_val)


def theta(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["call", "put"] = "call") -> float:
    """
    Calculate option theta (time decay per day).
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        Theta (rounded to configured precision, per day)
    """
    if T <= 0:
        return round_to_precision(0.0)
    
    if sigma == 0:
        return round_to_precision(0.0)
    
    d1, d2 = _black_scholes_d1_d2(S, K, T, r, sigma)
    
    term1 = -(S * _standard_normal_pdf(d1) * sigma) / (2 * math.sqrt(T))
    
    if option_type == "call":
        term2 = -r * K * math.exp(-r * T) * _standard_normal_cdf(d2)
        theta_val = (term1 + term2) / 365.0  # Per day
    elif option_type == "put":
        term2 = r * K * math.exp(-r * T) * _standard_normal_cdf(-d2)
        theta_val = (term1 + term2) / 365.0  # Per day
    else:
        raise ValueError(f"Invalid option_type: {option_type}")
    
    return round_to_precision(theta_val)


def rho(S: float, K: float, T: float, r: float, sigma: float, option_type: Literal["call", "put"] = "call") -> float:
    """
    Calculate option rho (interest rate sensitivity per 1% change).
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        Rho (rounded to configured precision, per 1% change in rate)
    """
    if T <= 0:
        return round_to_precision(0.0)
    
    if sigma == 0:
        if option_type == "call":
            return round_to_precision(K * T * math.exp(-r * T) / 100.0 if S > K else 0.0)
        else:
            return round_to_precision(-K * T * math.exp(-r * T) / 100.0 if S < K else 0.0)
    
    _, d2 = _black_scholes_d1_d2(S, K, T, r, sigma)
    
    if option_type == "call":
        rho_val = K * T * math.exp(-r * T) * _standard_normal_cdf(d2) / 100.0  # Per 1% change
    elif option_type == "put":
        rho_val = -K * T * math.exp(-r * T) * _standard_normal_cdf(-d2) / 100.0  # Per 1% change
    else:
        raise ValueError(f"Invalid option_type: {option_type}")
    
    return round_to_precision(rho_val)


def calculate_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: Literal["call", "put"] = "call"
) -> dict:
    """
    Calculate all Greeks for an option.
    
    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (years)
        r: Risk-free rate (annual)
        sigma: Volatility (annual)
        option_type: "call" or "put"
    
    Returns:
        Dictionary with all Greeks
    """
    return {
        "delta": delta(S, K, T, r, sigma, option_type),
        "gamma": gamma(S, K, T, r, sigma),
        "vega": vega(S, K, T, r, sigma),
        "theta": theta(S, K, T, r, sigma, option_type),
        "rho": rho(S, K, T, r, sigma, option_type),
    }
