"""
Black-Scholes pricing model for European options.
"""

import math
from typing import Union

def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate the Black-Scholes price for a European call option.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)

    Returns:
        Call option price
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    call_price = S * math.erf(d1 / math.sqrt(2)) - K * math.exp(-r * T) * math.erf(d2 / math.sqrt(2))
    return call_price

def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate the Black-Scholes price for a European put option.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)

    Returns:
        Put option price
    """
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    put_price = K * math.exp(-r * T) * math.erf(-d2 / math.sqrt(2)) - S * math.erf(-d1 / math.sqrt(2))
    return put_price

def black_scholes(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """
    Calculate the Black-Scholes price for a European option.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)
        option_type: 'call' or 'put'

    Returns:
        Option price
    """
    if option_type.lower() == 'call':
        return black_scholes_call(S, K, T, r, sigma)
    elif option_type.lower() == 'put':
        return black_scholes_put(S, K, T, r, sigma)
    else:
        raise ValueError("option_type must be 'call' or 'put'")