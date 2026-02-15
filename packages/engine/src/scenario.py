"""
Scenario analysis and stress testing
"""

from typing import Any
from .config import round_to_precision
from .pricing import price_option, price_stock


def scenario_run(
    positions: list[dict[str, Any]],
    scenarios: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Run stress scenarios on a portfolio.
    
    Args:
        positions: List of position dictionaries
        scenarios: List of scenario dictionaries, each with:
            - name: Scenario name
            - shock_type: "price", "volatility", "rate", or "combined"
            - parameters: Dict with shock parameters
    
    Returns:
        List of scenario results with portfolio values and changes
    """
    results = []
    
    # Calculate base portfolio value
    base_value = _calculate_portfolio_value(positions)
    
    for scenario in scenarios:
        name = scenario.get("name", "Unnamed Scenario")
        shock_type = scenario.get("shock_type", "price")
        parameters = scenario.get("parameters", {})
        
        # Apply scenario shocks
        shocked_positions = _apply_shocks(positions, shock_type, parameters)
        
        # Calculate new portfolio value
        new_value = _calculate_portfolio_value(shocked_positions)
        change = new_value - base_value
        change_pct = (change / base_value * 100.0) if base_value != 0 else 0.0
        
        results.append({
            "name": name,
            "shock_type": shock_type,
            "base_value": round_to_precision(base_value),
            "scenario_value": round_to_precision(new_value),
            "change": round_to_precision(change),
            "change_pct": round_to_precision(change_pct),
        })
    
    return results


def _calculate_portfolio_value(positions: list[dict[str, Any]]) -> float:
    """Calculate total portfolio value"""
    total = 0.0
    
    for position in positions:
        position_type = position.get("type", "stock").lower()
        quantity = position.get("quantity", 0)
        
        if position_type == "stock":
            current_price = position.get("current_price", position.get("price", 0))
            total += current_price * quantity
        elif position_type == "option":
            # For options, use current_price if available, else price using BS
            if "current_price" in position:
                total += position["current_price"] * quantity
            elif all(k in position for k in ["S", "K", "T", "r", "sigma"]):
                option_price = price_option(
                    S=position["S"],
                    K=position["K"],
                    T=position["T"],
                    r=position["r"],
                    sigma=position["sigma"],
                    option_type=position.get("option_type", "call")
                )
                total += option_price * quantity
    
    return total


def _apply_shocks(
    positions: list[dict[str, Any]],
    shock_type: str,
    parameters: dict[str, Any]
) -> list[dict[str, Any]]:
    """Apply scenario shocks to positions"""
    shocked_positions = []
    
    for position in positions:
        shocked = position.copy()
        
        if shock_type == "price":
            price_shock = parameters.get("price_change_pct", 0.0) / 100.0
            if "current_price" in shocked:
                shocked["current_price"] = shocked["current_price"] * (1 + price_shock)
            elif "price" in shocked:
                shocked["price"] = shocked["price"] * (1 + price_shock)
            if "S" in shocked:
                shocked["S"] = shocked["S"] * (1 + price_shock)
        
        elif shock_type == "volatility":
            vol_shock = parameters.get("volatility_change_pct", 0.0) / 100.0
            if "sigma" in shocked:
                shocked["sigma"] = shocked["sigma"] * (1 + vol_shock)
        
        elif shock_type == "rate":
            rate_shock = parameters.get("rate_change_bps", 0.0) / 10000.0
            if "r" in shocked:
                shocked["r"] = shocked["r"] + rate_shock
        
        elif shock_type == "combined":
            # Apply multiple shocks
            if "price_change_pct" in parameters:
                price_shock = parameters["price_change_pct"] / 100.0
                if "current_price" in shocked:
                    shocked["current_price"] = shocked["current_price"] * (1 + price_shock)
                elif "price" in shocked:
                    shocked["price"] = shocked["price"] * (1 + price_shock)
                if "S" in shocked:
                    shocked["S"] = shocked["S"] * (1 + price_shock)
            
            if "volatility_change_pct" in parameters:
                vol_shock = parameters["volatility_change_pct"] / 100.0
                if "sigma" in shocked:
                    shocked["sigma"] = shocked["sigma"] * (1 + vol_shock)
            
            if "rate_change_bps" in parameters:
                rate_shock = parameters["rate_change_bps"] / 10000.0
                if "r" in shocked:
                    shocked["r"] = shocked["r"] + rate_shock
        
        shocked_positions.append(shocked)
    
    return shocked_positions
