"""
Portfolio-level calculations
"""

from typing import Any
from .config import round_to_precision
from .pricing import price_option, price_stock
from .greeks import calculate_greeks


def portfolio_pnl(positions: list[dict[str, Any]]) -> float:
    """
    Calculate total P&L for a portfolio.
    
    Args:
        positions: List of position dictionaries with required keys:
            - type: "stock" or "option"
            - For stocks: quantity, current_price, purchase_price
            - For options: quantity, current_price, purchase_price
    
    Returns:
        Total P&L (rounded to configured precision)
    """
    total_pl = 0.0
    
    for position in positions:
        position_type = position.get("type", "stock").lower()
        quantity = position.get("quantity", 0)
        current_price = position.get("current_price", position.get("price", 0))
        purchase_price = position.get("purchase_price", current_price)
        
        pl = (current_price - purchase_price) * quantity
        total_pl += pl
    
    return round_to_precision(total_pl)


def portfolio_greeks(positions: list[dict[str, Any]]) -> dict:
    """
    Calculate aggregate Greeks for a portfolio of options.
    
    Args:
        positions: List of position dictionaries with required keys for options:
            - type: "option"
            - quantity: number of contracts
            - S: current stock price
            - K: strike price
            - T: time to maturity (years)
            - r: risk-free rate
            - sigma: volatility
            - option_type: "call" or "put"
    
    Returns:
        Dictionary with aggregated Greeks
    """
    total_delta = 0.0
    total_gamma = 0.0
    total_vega = 0.0
    total_theta = 0.0
    total_rho = 0.0
    
    for position in positions:
        if position.get("type", "").lower() != "option":
            continue
        
        quantity = position.get("quantity", 0)
        S = position.get("S", 0)
        K = position.get("K", 0)
        T = position.get("T", 0)
        r = position.get("r", 0.05)
        sigma = position.get("sigma", 0.2)
        option_type = position.get("option_type", "call")
        
        if S > 0 and K > 0 and T > 0:
            greeks = calculate_greeks(S, K, T, r, sigma, option_type)
            total_delta += greeks["delta"] * quantity
            total_gamma += greeks["gamma"] * quantity
            total_vega += greeks["vega"] * quantity
            total_theta += greeks["theta"] * quantity
            total_rho += greeks["rho"] * quantity
    
    return {
        "delta": round_to_precision(total_delta),
        "gamma": round_to_precision(total_gamma),
        "vega": round_to_precision(total_vega),
        "theta": round_to_precision(total_theta),
        "rho": round_to_precision(total_rho),
    }
