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

def bond_pv(coupon_rate: float, face_value: float, time_to_maturity: float, yield_to_maturity: float, payments_per_year: int = 1) -> float:
    """
    Calculate the present value (price) of a fixed-coupon bond.

    Args:
        coupon_rate: Annual coupon rate (as decimal, e.g., 0.05 for 5%)
        face_value: Face value of the bond
        time_to_maturity: Time to maturity in years
        yield_to_maturity: Annual yield to maturity (as decimal, e.g., 0.04 for 4%)
        payments_per_year: Number of coupon payments per year (default is 1)

    Returns:
        Bond price (present value)
    """
    # Calculate coupon payment per period
    coupon_payment = face_value * coupon_rate / payments_per_year

    # Calculate total number of periods
    total_periods = time_to_maturity * payments_per_year

    # Handle case where there are no periods
    if total_periods == 0:
        return face_value

    # Calculate present value of coupon payments and face value
    pv = 0.0

    # Present value of coupon payments
    for t in range(1, int(total_periods) + 1):
        pv += coupon_payment / (1 + yield_to_maturity / payments_per_year) ** t

    # Present value of face value (principal)
    pv += face_value / (1 + yield_to_maturity / payments_per_year) ** total_periods

    return pv

def bond_duration(coupon_rate: float, face_value: float, time_to_maturity: float, yield_to_maturity: float, payments_per_year: int = 1) -> float:
    """
    Calculate the Macaulay duration of a fixed-coupon bond.

    Args:
        coupon_rate: Annual coupon rate (as decimal, e.g., 0.05 for 5%)
        face_value: Face value of the bond
        time_to_maturity: Time to maturity in years
        yield_to_maturity: Annual yield to maturity (as decimal, e.g., 0.04 for 4%)
        payments_per_year: Number of coupon payments per year (default is 1)

    Returns:
        Macaulay duration in years
    """
    # Calculate coupon payment per period
    coupon_payment = face_value * coupon_rate / payments_per_year

    # Calculate total number of periods
    total_periods = time_to_maturity * payments_per_year

    # Handle case where there are no periods
    if total_periods == 0:
        return 0.0

    # Calculate present value of the bond
    pv = bond_pv(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    # Handle case where present value is zero (unlikely but for safety)
    if pv == 0:
        return 0.0

    # Calculate weighted average time of cash flows
    weighted_time = 0.0

    # Present value of coupon payments
    for t in range(1, int(total_periods) + 1):
        pv_coupon = coupon_payment / (1 + yield_to_maturity / payments_per_year) ** t
        weighted_time += t * pv_coupon

    # Present value of face value (principal)
    pv_face = face_value / (1 + yield_to_maturity / payments_per_year) ** total_periods
    weighted_time += total_periods * pv_face

    duration = weighted_time / pv

    # Convert to years (since t is in periods, we need to convert back)
    duration_years = duration / payments_per_year

    return duration_years

def bond_convexity(coupon_rate: float, face_value: float, time_to_maturity: float, yield_to_maturity: float, payments_per_year: int = 1) -> float:
    """
    Calculate the convexity of a fixed-coupon bond.

    Args:
        coupon_rate: Annual coupon rate (as decimal, e.g., 0.05 for 5%)
        face_value: Face value of the bond
        time_to_maturity: Time to maturity in years
        yield_to_maturity: Annual yield to maturity (as decimal, e.g., 0.04 for 4%)
        payments_per_year: Number of coupon payments per year (default is 1)

    Returns:
        Bond convexity
    """
    # Calculate coupon payment per period
    coupon_payment = face_value * coupon_rate / payments_per_year

    # Calculate total number of periods
    total_periods = time_to_maturity * payments_per_year

    # Handle case where there are no periods
    if total_periods == 0:
        return 0.0

    # Calculate present value of the bond
    pv = bond_pv(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    # Handle case where present value is zero (unlikely but for safety)
    if pv == 0:
        return 0.0

    # Calculate convexity
    convexity = 0.0

    # Present value of coupon payments
    for t in range(1, int(total_periods) + 1):
        pv_coupon = coupon_payment / (1 + yield_to_maturity / payments_per_year) ** t
        convexity += t * (t + 1) * pv_coupon / (payments_per_year ** 2)

    # Present value of face value (principal)
    pv_face = face_value / (1 + yield_to_maturity / payments_per_year) ** total_periods
    convexity += total_periods * (total_periods + 1) * pv_face / (payments_per_year ** 2)

    # Normalize by present value
    convexity = convexity / (pv * (1 + yield_to_maturity / payments_per_year) ** 2)

    return convexity

def bond_dv01(coupon_rate: float, face_value: float, time_to_maturity: float, yield_to_maturity: float, payments_per_year: int = 1) -> float:
    """
    Calculate the DV01 (dollar value of a 0.01% change in yield) of a fixed-coupon bond.

    Args:
        coupon_rate: Annual coupon rate (as decimal, e.g., 0.05 for 5%)
        face_value: Face value of the bond
        time_to_maturity: Time to maturity in years
        yield_to_maturity: Annual yield to maturity (as decimal, e.g., 0.04 for 4%)
        payments_per_year: Number of coupon payments per year (default is 1)

    Returns:
        DV01 in dollars
    """
    # Calculate duration and convexity
    duration = bond_duration(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    convexity = bond_convexity(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    # Calculate PV
    pv = bond_pv(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    # Calculate DV01 using the approximation formula:
    # DV01 ≈ -Duration * PV * 0.0001 + 0.5 * Convexity * PV * (0.0001)^2
    # For small changes, the convexity term is usually negligible, so we use:
    # DV01 ≈ -Duration * PV * 0.0001
    dv01 = -duration * pv * 0.0001

    return dv01