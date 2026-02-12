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

    # Standard normal CDF using erf
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


def portfolio_delta_exposure(positions: list) -> float:
    """
    Calculate the total delta exposure for a portfolio of positions.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'quantity': Number of shares/contracts held
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'delta': Delta value (for options, if already calculated)

    Returns:
        Total delta exposure for the portfolio
    """
    total_delta = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')  # Default to stock if not specified

        if position_type == 'stock':
            current_price = position.get('current_price', position.get('price', 0.0))
            quantity = position.get('quantity', 0.0)

            # Only calculate if we have the necessary data
            if current_price > 0:
                delta_exposure = stock_delta_exposure(current_price, quantity)
                total_delta += delta_exposure

        elif position_type == 'option':
            # For options, use the provided delta if available
            if 'delta' in position:
                quantity = position.get('quantity', 0.0)
                if quantity > 0:
                    delta_exposure = position['delta'] * quantity
                    total_delta += delta_exposure
            else:
                # If no delta provided, we could calculate it, but that would require
                # more complex logic with current market parameters
                # For now, we'll skip this case
                pass

    return total_delta


def portfolio_net_delta_exposure(positions: list) -> float:
    """
    Calculate the net delta exposure for a portfolio of positions.
    Net delta exposure is total delta exposure minus short positions.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'quantity': Number of shares/contracts held
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'delta': Delta value (for options, if already calculated)

    Returns:
        Net delta exposure for the portfolio
    """
    total_delta = 0.0
    short_positions = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')  # Default to stock if not specified
        quantity = position.get('quantity', 0.0)

        if position_type == 'stock':
            current_price = position.get('current_price', position.get('price', 0.0))

            # Only calculate if we have the necessary data
            if current_price > 0:
                delta_exposure = stock_delta_exposure(current_price, quantity)
                if quantity > 0:
                    total_delta += delta_exposure
                else:
                    short_positions += abs(delta_exposure)
        elif position_type == 'option':
            # For options, use the provided delta if available
            if 'delta' in position:
                if quantity > 0:
                    delta_exposure = position['delta'] * quantity
                    total_delta += delta_exposure
                else:
                    # For short options, add to short positions
                    short_positions += abs(position['delta'] * quantity)
            else:
                # If no delta provided, we could calculate it, but that would require
                # more complex logic with current market parameters
                # For now, we'll skip this case
                pass

    # Net delta exposure = total delta exposure - short positions
    return total_delta - short_positions


def portfolio_gross_exposure(positions: list) -> float:
    """
    Calculate the gross exposure for a portfolio of positions.
    Gross exposure is the sum of absolute values of all delta exposures.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'quantity': Number of shares/contracts held
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'delta': Delta value (for options, if already calculated)

    Returns:
        Gross exposure for the portfolio
    """
    total_gross_exposure = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')  # Default to stock if not specified

        if position_type == 'stock':
            current_price = position.get('current_price', position.get('price', 0.0))
            quantity = position.get('quantity', 0.0)

            # Only calculate if we have the necessary data
            if current_price > 0:
                delta_exposure = stock_delta_exposure(current_price, quantity)
                total_gross_exposure += abs(delta_exposure)

        elif position_type == 'option':
            # For options, use the provided delta if available
            if 'delta' in position:
                quantity = position.get('quantity', 0.0)
                delta_exposure = position['delta'] * quantity
                total_gross_exposure += abs(delta_exposure)
            else:
                # If no delta provided, we could calculate it, but that would require
                # more complex logic with current market parameters
                # For now, we'll skip this case
                pass

    return total_gross_exposure


def portfolio_sector_aggregation(positions: list) -> dict:
    """
    Aggregate portfolio positions by sector and calculate metrics per sector.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'quantity': Number of shares/contracts held
            - 'sector': Sector classification (for stocks)
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'delta': Delta value (for options, if already calculated)

    Returns:
        Dictionary with sector aggregation data
    """
    sector_data = {}

    for position in positions:
        position_type = position.get('type', 'stock')  # Default to stock if not specified

        # For now, we'll assume sector is provided for stocks
        # If sector is not provided, we'll use a default 'Unknown' sector
        sector = position.get('sector', 'Unknown')

        if sector not in sector_data:
            sector_data[sector] = {
                'total_value': 0.0,
                'total_delta_exposure': 0.0,
                'position_count': 0,
                'assets': []
            }

        # Calculate value and delta exposure
        quantity = position.get('quantity', 0.0)
        current_price = position.get('current_price', position.get('price', 0.0))

        if position_type == 'stock' and current_price > 0:
            value = current_price * quantity
            delta_exposure = stock_delta_exposure(current_price, quantity)

            sector_data[sector]['total_value'] += value
            sector_data[sector]['total_delta_exposure'] += delta_exposure
            sector_data[sector]['position_count'] += 1
            sector_data[sector]['assets'].append(position)
        elif position_type == 'option':
            # For options, we'll add to the sector if delta is provided
            if 'delta' in position:
                value = position.get('quantity', 0.0) * position.get('delta', 0.0)  # Simplified
                delta_exposure = position['delta'] * position.get('quantity', 0.0)

                sector_data[sector]['total_value'] += value
                sector_data[sector]['total_delta_exposure'] += delta_exposure
                sector_data[sector]['position_count'] += 1
                sector_data[sector]['assets'].append(position)

    return sector_data

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


def portfolio_pl(positions: list) -> float:
    """
    Calculate the total profit/loss for a portfolio of positions.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'purchase_price': Original purchase price (for stocks)
            - 'quantity': Number of shares/contracts held
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'time_to_maturity': Time to maturity (in years) (for options)
            - 'risk_free_rate': Risk-free interest rate (annual) (for options)
            - 'volatility': Volatility (annual standard deviation) (for options)

    Returns:
        Total profit/loss for the portfolio
    """
    # Calculate portfolio value using existing portfolio_value function
    current_value = portfolio_value(positions)

    # Calculate purchase value manually by summing up purchase costs
    total_purchase_value = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')

        if position_type == 'stock':
            purchase_price = position.get('purchase_price', 0.0)
            quantity = position.get('quantity', 0.0)

            if purchase_price > 0 and quantity > 0:
                total_purchase_value += purchase_price * quantity

        elif position_type == 'option':
            # For options, we use the purchase_price if available
            purchase_price = position.get('purchase_price', 0.0)
            quantity = position.get('quantity', 0.0)

            # For options without explicit purchase_price, we need to calculate the Black-Scholes value
            # as the purchase price, since that represents what the option was actually purchased for
            if quantity > 0:
                if purchase_price > 0:
                    # Use the provided purchase price
                    total_purchase_value += purchase_price * quantity
                else:
                    # No explicit purchase price - calculate Black-Scholes price as purchase price
                    # Get option parameters needed for Black-Scholes
                    current_price = position.get('current_price', 0.0)
                    strike_price = position.get('strike_price', 0.0)
                    time_to_maturity = position.get('time_to_maturity', 0.0)
                    risk_free_rate = position.get('risk_free_rate', 0.0)
                    volatility = position.get('volatility', 0.0)
                    option_type = position.get('option_type', 'call')

                    # Only calculate if we have the necessary data
                    if (current_price > 0 and strike_price > 0 and time_to_maturity > 0 and
                        risk_free_rate > 0 and volatility > 0):

                        # Calculate the Black-Scholes price for the option at current market conditions
                        option_price = black_scholes(current_price, strike_price, time_to_maturity,
                                                   risk_free_rate, volatility, option_type)

                        total_purchase_value += option_price * quantity

    # Return profit/loss as portfolio_value - purchase_value
    return current_value - total_purchase_value


def portfolio_value(positions: list) -> float:
    """
    Calculate the total value of a portfolio of positions.

    Args:
        positions: List of position dictionaries with keys:
            - 'type': 'stock' or 'option'
            - 'current_price': Current market price
            - 'quantity': Number of shares/contracts held
            - 'strike_price': Strike price (for options)
            - 'option_type': 'call' or 'put' (for options)
            - 'time_to_maturity': Time to maturity (in years) (for options)
            - 'risk_free_rate': Risk-free interest rate (annual) (for options)
            - 'volatility': Volatility (annual standard deviation) (for options)

    Returns:
        Total value of the portfolio
    """
    total_value = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')  # Default to stock if not specified

        if position_type == 'stock':
            current_price = position.get('current_price', position.get('price', 0.0))
            quantity = position.get('quantity', 0.0)

            # Only calculate if we have the necessary data
            if current_price > 0 and quantity > 0:
                value = current_price * quantity
                total_value += value

        elif position_type == 'option':
            # For options, calculate the current market value using Black-Scholes model
            current_price = position.get('current_price', 0.0)
            strike_price = position.get('strike_price', 0.0)
            time_to_maturity = position.get('time_to_maturity', 0.0)
            risk_free_rate = position.get('risk_free_rate', 0.0)
            volatility = position.get('volatility', 0.0)
            option_type = position.get('option_type', 'call')
            quantity = position.get('quantity', 0.0)

            # Only calculate if we have the necessary data
            if (current_price > 0 and strike_price > 0 and time_to_maturity > 0 and
                risk_free_rate > 0 and volatility > 0 and quantity > 0):

                # Calculate the Black-Scholes price for the current option
                option_price = black_scholes(current_price, strike_price, time_to_maturity,
                                           risk_free_rate, volatility, option_type)

                # Calculate the total value for this option position
                value = option_price * quantity
                total_value += value

    return total_value

def implied_volatility_call(market_price: float, S: float, K: float, T: float, r: float,
                          max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate the implied volatility for a European call option using the bisection method.

    Args:
        market_price: Observed market price of the call option
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        max_iterations: Maximum number of iterations for the solver
        tolerance: Tolerance for convergence

    Returns:
        Implied volatility (annual standard deviation)

    Raises:
        ValueError: If the market price is too low or too high to be consistent with Black-Scholes
    """
    # Check for valid inputs
    if S <= 0 or K <= 0 or T <= 0 or r < 0:
        raise ValueError("Invalid parameters: S, K, T, and r must be positive")

    if market_price < 0:
        raise ValueError("Market price cannot be negative")

    # The Black-Scholes call price is always at least max(0, S - K * exp(-r * T))
    # If market_price is below this, there's no valid volatility
    intrinsic_value = max(0, S - K * math.exp(-r * T))
    if market_price < intrinsic_value:
        raise ValueError("Market price is too low to be consistent with Black-Scholes model")

    # The Black-Scholes call price is bounded above by S (when volatility approaches infinity)
    # If market_price is above S, there's no valid volatility (this should not happen in practice)
    if market_price > S:
        raise ValueError("Market price is too high to be consistent with Black-Scholes model")

    # Bisection method
    # Set reasonable bounds for volatility
    vol_min = 0.0001  # 0.01% - minimum reasonable volatility
    vol_max = 10.0    # 1000% - maximum reasonable volatility

    # Ensure bounds are correct
    if vol_min >= vol_max:
        raise ValueError("Invalid volatility bounds")

    # Check if the bounds are reasonable
    bs_price_min = black_scholes_call(S, K, T, r, vol_min)
    bs_price_max = black_scholes_call(S, K, T, r, vol_max)

    # If the minimum bound already gives a higher price than the market price,
    # we need to adjust the upper bound
    if bs_price_min > market_price:
        vol_max = vol_min * 100  # Increase upper bound
        bs_price_max = black_scholes_call(S, K, T, r, vol_max)

        # If even this doesn't work, the price is too high
        if bs_price_max < market_price:
            raise ValueError("Market price is too high to be consistent with Black-Scholes model")

    # Check if the maximum bound already gives a lower price than the market price,
    # which would indicate the price is too low
    if bs_price_max < market_price:
        vol_min = vol_max / 100  # Decrease lower bound
        bs_price_min = black_scholes_call(S, K, T, r, vol_min)

        # If even this doesn't work, the price is too low
        if bs_price_min > market_price:
            raise ValueError("Market price is too low to be consistent with Black-Scholes model")

    # Bisection method
    for _ in range(max_iterations):
        vol_mid = (vol_min + vol_max) / 2.0
        bs_price = black_scholes_call(S, K, T, r, vol_mid)

        if abs(bs_price - market_price) < tolerance:
            return vol_mid

        if bs_price < market_price:
            vol_min = vol_mid
        else:
            vol_max = vol_mid

    # Return the best approximation if we didn't converge to the exact tolerance
    return (vol_min + vol_max) / 2.0

def implied_volatility_put(market_price: float, S: float, K: float, T: float, r: float,
                         max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate the implied volatility for a European put option using the bisection method.

    Args:
        market_price: Observed market price of the put option
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        max_iterations: Maximum number of iterations for the solver
        tolerance: Tolerance for convergence

    Returns:
        Implied volatility (annual standard deviation)

    Raises:
        ValueError: If the market price is too low or too high to be consistent with Black-Scholes
    """
    # Check for valid inputs
    if S <= 0 or K <= 0 or T <= 0 or r < 0:
        raise ValueError("Invalid parameters: S, K, T, and r must be positive")

    if market_price < 0:
        raise ValueError("Market price cannot be negative")

    # The Black-Scholes put price is always at least max(0, K * exp(-r * T) - S)
    # If market_price is below this, there's no valid volatility
    intrinsic_value = max(0, K * math.exp(-r * T) - S)
    if market_price < intrinsic_value:
        raise ValueError("Market price is too low to be consistent with Black-Scholes model")

    # The Black-Scholes put price is bounded above by K * exp(-r * T) (when volatility approaches infinity)
    # If market_price is above K * exp(-r * T), there's no valid volatility (this should not happen in practice)
    if market_price > K * math.exp(-r * T):
        raise ValueError("Market price is too high to be consistent with Black-Scholes model")

    # Bisection method
    # Set reasonable bounds for volatility
    vol_min = 0.0001  # 0.01% - minimum reasonable volatility
    vol_max = 10.0    # 1000% - maximum reasonable volatility

    # Ensure bounds are correct
    if vol_min >= vol_max:
        raise ValueError("Invalid volatility bounds")

    # Check if the bounds are reasonable
    bs_price_min = black_scholes_put(S, K, T, r, vol_min)
    bs_price_max = black_scholes_put(S, K, T, r, vol_max)

    # If the minimum bound already gives a higher price than the market price,
    # we need to adjust the upper bound
    if bs_price_min > market_price:
        vol_max = vol_min * 100  # Increase upper bound
        bs_price_max = black_scholes_put(S, K, T, r, vol_max)

        # If even this doesn't work, the price is too high
        if bs_price_max < market_price:
            raise ValueError("Market price is too high to be consistent with Black-Scholes model")

    # Check if the maximum bound already gives a lower price than the market price,
    # which would indicate the price is too low
    if bs_price_max < market_price:
        vol_min = vol_max / 100  # Decrease lower bound
        bs_price_min = black_scholes_put(S, K, T, r, vol_min)

        # If even this doesn't work, the price is too low
        if bs_price_min > market_price:
            raise ValueError("Market price is too low to be consistent with Black-Scholes model")

    # Bisection method
    for _ in range(max_iterations):
        vol_mid = (vol_min + vol_max) / 2.0
        bs_price = black_scholes_put(S, K, T, r, vol_mid)

        if abs(bs_price - market_price) < tolerance:
            return vol_mid

        if bs_price < market_price:
            vol_min = vol_mid
        else:
            vol_max = vol_mid

    # Return the best approximation if we didn't converge to the exact tolerance
    return (vol_min + vol_max) / 2.0

def implied_volatility(S: float, K: float, T: float, r: float, market_price: float,
                      option_type: str = 'call', max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate the implied volatility for a European option using the bisection method.

    Args:
        S: Current stock price
        K: Strike price
        T: Time to maturity (in years)
        r: Risk-free interest rate (annual)
        market_price: Observed market price of the option
        option_type: 'call' or 'put'
        max_iterations: Maximum number of iterations for the solver
        tolerance: Tolerance for convergence

    Returns:
        Implied volatility (annual standard deviation)

    Raises:
        ValueError: If the market price is too low or too high to be consistent with Black-Scholes
    """
    if option_type.lower() == 'call':
        return implied_volatility_call(market_price, S, K, T, r, max_iterations, tolerance)
    elif option_type.lower() == 'put':
        return implied_volatility_put(market_price, S, K, T, r, max_iterations, tolerance)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

def bond_price_approximation(coupon_rate: float, face_value: float, time_to_maturity: float,
                           yield_to_maturity: float, payments_per_year: int = 1,
                           yield_change: float = 0.0001) -> float:
    """
    Approximate the change in bond price using duration and convexity.

    This function estimates the percentage change in bond price for a given change in yield
    using the duration and convexity approximation formula:
    ΔP/P ≈ -Duration * Δy + 0.5 * Convexity * (Δy)^2

    Args:
        coupon_rate: Annual coupon rate (as decimal, e.g., 0.05 for 5%)
        face_value: Face value of the bond
        time_to_maturity: Time to maturity in years
        yield_to_maturity: Annual yield to maturity (as decimal, e.g., 0.04 for 4%)
        payments_per_year: Number of coupon payments per year (default is 1)
        yield_change: Change in yield (as decimal, e.g., 0.0001 for 0.01% or 1 basis point)

    Returns:
        Approximated percentage change in bond price
    """
    # Calculate duration and convexity
    duration = bond_duration(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)
    convexity = bond_convexity(coupon_rate, face_value, time_to_maturity, yield_to_maturity, payments_per_year)

    # Calculate the percentage change in price using the duration and convexity approximation
    price_change_percentage = -duration * yield_change + 0.5 * convexity * (yield_change ** 2)

    return price_change_percentage