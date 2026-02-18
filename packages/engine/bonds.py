"""
Bond Analytics Module (v1.8)
Simple fixed-rate bond pricing and risk metrics.
"""

import math
from typing import Dict, Any


def bond_price_from_yield(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    yield_to_maturity: float,
    periods_per_year: int = 2
) -> float:
    """
    Calculate bond price from yield (present value of cash flows).
    
    Args:
        face_value: Face/par value of the bond
        coupon_rate: Annual coupon rate (e.g., 0.05 for 5%)
        years_to_maturity: Years until maturity
        yield_to_maturity: Annual yield to maturity (e.g., 0.06 for 6%)
        periods_per_year: Coupon payment frequency (2 = semi-annual)
    
    Returns:
        Bond price
    """
    if years_to_maturity <= 0:
        return face_value
    
    n_periods = int(years_to_maturity * periods_per_year)
    coupon_payment = face_value * coupon_rate / periods_per_year
    period_yield = yield_to_maturity / periods_per_year
    
    # Price = PV(coupons) + PV(face value)
    pv_coupons = 0.0
    for t in range(1, n_periods + 1):
        pv_coupons += coupon_payment / math.pow(1 + period_yield, t)
    
    pv_face = face_value / math.pow(1 + period_yield, n_periods)
    
    return pv_coupons + pv_face


def bond_yield_from_price(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    price: float,
    periods_per_year: int = 2,
    tolerance: float = 0.0001,
    max_iterations: int = 100
) -> float:
    """
    Calculate yield to maturity from price (numerical iteration).
    Uses Newton-Raphson method with fixed iterations for determinism.
    
    Args:
        face_value: Face/par value of the bond
        coupon_rate: Annual coupon rate
        years_to_maturity: Years until maturity
        price: Current market price
        periods_per_year: Coupon payment frequency
        tolerance: Convergence tolerance
        max_iterations: Maximum iterations (fixed for determinism)
    
    Returns:
        Yield to maturity
    """
    if years_to_maturity <= 0:
        return 0.0
    
    # Initial guess: coupon rate
    ytm = coupon_rate
    
    for _ in range(max_iterations):
        calculated_price = bond_price_from_yield(
            face_value, coupon_rate, years_to_maturity, ytm, periods_per_year
        )
        
        diff = calculated_price - price
        
        if abs(diff) < tolerance:
            break
        
        # Calculate derivative (duration approximation)
        ytm_up = ytm + 0.0001
        price_up = bond_price_from_yield(
            face_value, coupon_rate, years_to_maturity, ytm_up, periods_per_year
        )
        derivative = (price_up - calculated_price) / 0.0001
        
        # Newton-Raphson step
        if abs(derivative) > 1e-10:
            ytm = ytm - diff / derivative
        
        # Clamp to reasonable range
        ytm = max(0.0001, min(1.0, ytm))
    
    return ytm


def bond_duration(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    yield_to_maturity: float,
    periods_per_year: int = 2
) -> float:
    """
    Calculate Macaulay duration (weighted average time to cash flows).
    
    Returns:
        Duration in years
    """
    if years_to_maturity <= 0:
        return 0.0
    
    n_periods = int(years_to_maturity * periods_per_year)
    coupon_payment = face_value * coupon_rate / periods_per_year
    period_yield = yield_to_maturity / periods_per_year
    
    bond_price = bond_price_from_yield(
        face_value, coupon_rate, years_to_maturity, yield_to_maturity, periods_per_year
    )
    
    weighted_time = 0.0
    for t in range(1, n_periods + 1):
        cash_flow = coupon_payment if t < n_periods else coupon_payment + face_value
        pv_cf = cash_flow / math.pow(1 + period_yield, t)
        time_in_years = t / periods_per_year
        weighted_time += time_in_years * pv_cf
    
    return weighted_time / bond_price if bond_price > 0 else 0.0


def bond_convexity(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    yield_to_maturity: float,
    periods_per_year: int = 2
) -> float:
    """
    Calculate convexity (second derivative of price with respect to yield).
    
    Returns:
        Convexity
    """
    if years_to_maturity <= 0:
        return 0.0
    
    n_periods = int(years_to_maturity * periods_per_year)
    coupon_payment = face_value * coupon_rate / periods_per_year
    period_yield = yield_to_maturity / periods_per_year
    
    bond_price = bond_price_from_yield(
        face_value, coupon_rate, years_to_maturity, yield_to_maturity, periods_per_year
    )
    
    convexity_sum = 0.0
    for t in range(1, n_periods + 1):
        cash_flow = coupon_payment if t < n_periods else coupon_payment + face_value
        pv_cf = cash_flow / math.pow(1 + period_yield, t)
        convexity_sum += t * (t + 1) * pv_cf
    
    convexity = convexity_sum / (bond_price * math.pow(1 + period_yield, 2) * periods_per_year * periods_per_year)
    
    return convexity if bond_price > 0 else 0.0


def bond_risk_metrics(
    face_value: float,
    coupon_rate: float,
    years_to_maturity: float,
    yield_to_maturity: float,
    periods_per_year: int = 2
) -> Dict[str, Any]:
    """
    Calculate all bond risk metrics in one call.
    
    Returns:
        Dictionary with price, duration, modified_duration, convexity
    """
    price = bond_price_from_yield(
        face_value, coupon_rate, years_to_maturity, yield_to_maturity, periods_per_year
    )
    
    duration = bond_duration(
        face_value, coupon_rate, years_to_maturity, yield_to_maturity, periods_per_year
    )
    
    modified_duration = duration / (1 + yield_to_maturity / periods_per_year)
    
    convexity = bond_convexity(
        face_value, coupon_rate, years_to_maturity, yield_to_maturity, periods_per_year
    )
    
    return {
        "price": round(price, 4),
        "duration": round(duration, 4),
        "modified_duration": round(modified_duration, 4),
        "convexity": round(convexity, 4),
    }
