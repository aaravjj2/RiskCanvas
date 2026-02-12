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
    # Handle edge cases where volatility or time is zero
    # When volatility is zero the option's value is its intrinsic value
    if sigma == 0 or T == 0:
        return max(S - K, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    # Standard normal CDF using erf
    def N(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    call_price = S * N(d1) - K * math.exp(-r * T) * N(d2)
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
    # Handle edge cases where volatility or time is zero
    # When volatility is zero the option's value is its intrinsic value
    if sigma == 0 or T == 0:
        return max(K - S, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    def N(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    put_price = K * math.exp(-r * T) * N(-d2) - S * N(-d1)
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

def stock_pl(current_price: float, purchase_price: float, quantity: float) -> float:
    """
    Calculate the profit/loss for a stock position.

    Args:
        current_price: Current market price of the stock
        purchase_price: Original purchase price of the stock
        quantity: Number of shares held

    Returns:
        Profit/Loss amount
    """
    return (current_price - purchase_price) * quantity

def stock_delta_exposure(current_price: float, quantity: float) -> float:
    """
    Calculate the delta exposure for a stock position.

    For a stock, delta is 1.0 (i.e., the price changes at the same rate as the stock).

    Args:
        current_price: Current market price of the stock
        quantity: Number of shares held

    Returns:
        Delta exposure
    """
    return 1.0 * quantity