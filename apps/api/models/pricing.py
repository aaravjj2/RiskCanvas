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

def black_scholes_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """
    Calculate the delta of a European option using Black-Scholes formula.

    Delta measures the rate of change of option price with respect to stock price.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)
        option_type: 'call' or 'put'

    Returns:
        Option delta
    """
    if sigma == 0 or T == 0:
        # For zero volatility or time, delta is either 0 or 1 depending on option type
        # When sigma = 0, the option is either at-the-money or in/out-of-the-money
        # For at-the-money (S = K), delta is 0.5 for calls and -0.5 for puts (this is a convention)
        # For in/out-of-the-money, delta is 0 or 1 (as in standard Black-Scholes)
        if option_type.lower() == 'call':
            if S > K:
                return 1.0
            elif S < K:
                return 0.0
            else:  # S == K (at-the-money)
                return 0.5  # Standard convention for at-the-money options
        else:  # put
            if S > K:
                return 0.0
            elif S < K:
                return 1.0
            else:  # S == K (at-the-money)
                return 0.5  # Standard convention for at-the-money options

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    # Standard normal CDF using erf
    def N(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    if option_type.lower() == 'call':
        return N(d1)
    else:  # put
        return N(d1) - 1.0

def black_scholes_gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate the gamma of a European option using Black-Scholes formula.

    Gamma measures the rate of change of delta with respect to stock price.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)

    Returns:
        Option gamma
    """
    if sigma == 0 or T == 0:
        return 0.0

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    # Standard normal probability density function
    def n(x: float) -> float:
        return math.exp(-0.5 * x ** 2) / math.sqrt(2.0 * math.pi)

    gamma = n(d1) / (S * sigma * math.sqrt(T))
    return gamma

def black_scholes_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Calculate the vega of a European option using Black-Scholes formula.

    Vega measures the rate of change of option price with respect to volatility.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)

    Returns:
        Option vega
    """
    if sigma == 0 or T == 0:
        return 0.0

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

    # Standard normal probability density function
    def n(x: float) -> float:
        return math.exp(-0.5 * x ** 2) / math.sqrt(2.0 * math.pi)

    vega = S * n(d1) * math.sqrt(T)
    return vega

def black_scholes_theta(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """
    Calculate the theta of a European option using Black-Scholes formula.

    Theta measures the rate of change of option price with respect to time.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)
        option_type: 'call' or 'put'

    Returns:
        Option theta (per year)
    """
    if sigma == 0 or T == 0:
        return 0.0

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    # Standard normal probability density function
    def n(x: float) -> float:
        return math.exp(-0.5 * x ** 2) / math.sqrt(2.0 * math.pi)

    # Standard normal CDF using erf
    def N(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    if option_type.lower() == 'call':
        theta = -(S * n(d1) * sigma) / (2.0 * math.sqrt(T)) - r * K * math.exp(-r * T) * N(d2)
    else:  # put
        theta = -(S * n(d1) * sigma) / (2.0 * math.sqrt(T)) + r * K * math.exp(-r * T) * N(-d2)

    return theta

def black_scholes_rho(S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """
    Calculate the rho of a European option using Black-Scholes formula.

    Rho measures the rate of change of option price with respect to interest rate.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        sigma: Volatility (annual standard deviation)
        option_type: 'call' or 'put'

    Returns:
        Option rho
    """
    if sigma == 0 or T == 0:
        return 0.0

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    # Standard normal CDF using erf
    def N(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    if option_type.lower() == 'call':
        rho = K * T * math.exp(-r * T) * N(d2)
    else:  # put
        rho = -K * T * math.exp(-r * T) * N(-d2)

    return rho

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