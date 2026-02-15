"""
Hedge Studio Engine for v1.3 - Deterministic hedge suggestions

Provides deterministic hedge recommendations to reduce portfolio VaR
with minimal cost. Uses grid search over candidate hedges.

DETERMINISM GUARANTEES:
- Fixed seed for any random operations (though we prefer enumeration)
- Sorted results for stable ordering
- Canonical JSON representations
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Import engine
engine_path = str(Path(__file__).parent.parent.parent / "packages" / "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

from src import (
    price_option,
    calculate_greeks,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    round_to_precision,
)


def canonicalize_json(obj: any) -> str:
    """Convert object to canonical JSON"""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True, default=str)


def calculate_portfolio_var(positions: List[Dict[str, Any]], volatility: float = 0.15) -> float:
    """Calculate portfolio VaR"""
    total_value = 0.0
    for pos in positions:
        current_price = pos.get("current_price", pos.get("price", 0))
        quantity = pos.get("quantity", 0)
        total_value += current_price * quantity
    
    if total_value <= 0:
        return 0.0
    
    return var_parametric(
        portfolio_value=total_value,
        volatility=volatility,
        confidence_level=0.95,
        time_horizon_days=1
    )


def generate_hedge_candidates(
    portfolio: Dict[str, Any],
    target_reduction_pct: float,
    max_cost: Optional[float] = None,
    allowed_instruments: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate deterministic list of hedge candidates.
    
    Strategies:
    1. Buy protective puts on underlying stocks
    2. Reduce exposure (sell portion of holdings)
    3. Add offsetting positions
    
    Returns sorted list of candidates by cost-effectiveness.
    """
    positions = portfolio.get("assets", [])
    if not positions:
        return []
    
    # Default allowed instruments
    if allowed_instruments is None:
        allowed_instruments = ["protective_put", "reduce_exposure"]
    
    candidates = []
    
    # Get stock positions (we can hedge these)
    stock_positions = [p for p in positions if p.get("type") == "stock"]
    
    # Strategy 1: Protective puts
    if "protective_put" in allowed_instruments:
        for stock in stock_positions:
            symbol = stock.get("symbol")
            quantity = stock.get("quantity", 0)
            current_price = stock.get("current_price", stock.get("price", 0))
            
            # Generate put option candidates at various strikes
            for strike_pct in [0.95, 0.90, 0.85]:  # 5%, 10%, 15% OTM
                strike = current_price * strike_pct
                
                # Price the put
                put_price = price_option(
                    S=current_price,
                    K=strike,
                    T=0.25,  # 3 months
                    r=0.05,
                    sigma=0.25,
                    option_type="put"
                )
                
                # Cost to buy protection for full position
                cost = put_price * quantity * 100  # Options are per 100 shares
                
                # Skip if over max cost
                if max_cost and cost > max_cost:
                    continue
                
                # Create hedged portfolio
                hedged_positions = positions.copy()
                hedged_positions.append({
                    "symbol": f"{symbol}_PUT",
                    "type": "option",
                    "option_type": "put",
                    "quantity": quantity / 100,  # 1 contract per 100 shares
                    "S": current_price,
                    "K": strike,
                    "T": 0.25,
                    "r": 0.05,
                    "sigma": 0.25,
                    "current_price": put_price,
                    "purchase_price": put_price
                })
                
                # Calculate new VaR
                hedged_portfolio = {"assets": hedged_positions}
                new_var = calculate_portfolio_var(hedged_positions)
                
                candidates.append({
                    "strategy": "protective_put",
                    "description": f"Buy {strike_pct*100:.0f}% OTM put on {symbol}",
                    "instrument": {
                        "type": "option",
                        "option_type": "put",
                        "underlying": symbol,
                        "strike": strike,
                        "quantity": quantity / 100,
                        "expiry_months": 3
                    },
                    "cost": round_to_precision(cost),
                    "estimated_new_var": new_var,
                    "hedged_positions": hedged_positions
                })
    
    # Strategy 2: Reduce exposure
    if "reduce_exposure" in allowed_instruments:
        for stock in stock_positions:
            symbol = stock.get("symbol")
            quantity = stock.get("quantity", 0)
            current_price = stock.get("current_price", stock.get("price", 0))
            
            # Try reducing by 25%, 50%
            for reduction_pct in [0.25, 0.50]:
                reduction_qty = quantity * reduction_pct
                cost = 0  # No cost to sell (ignoring commissions/slippage)
                
                # Create reduced portfolio
                hedged_positions = []
                for pos in positions:
                    if pos.get("symbol") == symbol:
                        new_pos = pos.copy()
                        new_pos["quantity"] = quantity * (1 - reduction_pct)
                        hedged_positions.append(new_pos)
                    else:
                        hedged_positions.append(pos)
                
                new_var = calculate_portfolio_var(hedged_positions)
                
                candidates.append({
                    "strategy": "reduce_exposure",
                    "description": f"Reduce {symbol} position by {reduction_pct*100:.0f}%",
                    "instrument": {
                        "type": "sell",
                        "symbol": symbol,
                        "quantity": reduction_qty
                    },
                    "cost": cost,
                    "estimated_new_var": new_var,
                    "hedged_positions": hedged_positions
                })
    
    # Calculate current VaR
    current_var = calculate_portfolio_var(positions)
    
    # Filter and score candidates
    scored_candidates = []
    for candidate in candidates:
        new_var = candidate["estimated_new_var"]
        cost = candidate["cost"]
        
        # Calculate VaR reduction
        var_reduction = current_var - new_var
        var_reduction_pct = (var_reduction / abs(current_var)) * 100 if current_var != 0 else 0
        
        # Skip if doesn't meet target
        if var_reduction_pct < target_reduction_pct:
            continue
        
        # Calculate cost-effectiveness score (var reduction per dollar)
        cost_effectiveness = var_reduction / max(cost, 1)  # Avoid division by zero
        
        candidate["current_var"] = current_var
        candidate["var_reduction"] = round_to_precision(var_reduction)
        candidate["var_reduction_pct"] = round_to_precision(var_reduction_pct)
        candidate["cost_effectiveness"] = round_to_precision(cost_effectiveness)
        
        scored_candidates.append(candidate)
    
    # Sort by cost-effectiveness (descending), then by cost (ascending)
    scored_candidates.sort(key=lambda x: (-x["cost_effectiveness"], x["cost"]))
    
    return scored_candidates


def evaluate_hedge(
    portfolio: Dict[str, Any],
    hedge_candidate: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a hedge candidate against stress scenarios.
    Returns before/after metrics.
    """
    original_positions = portfolio.get("assets", [])
    hedged_positions = hedge_candidate.get("hedged_positions", [])
    
    # Calculate metrics
    original_var = calculate_portfolio_var(original_positions)
    hedged_var = calculate_portfolio_var(hedged_positions)
    
    # Calculate portfolio values
    original_value = sum(
        pos.get("current_price", pos.get("price", 0)) * pos.get("quantity", 0)
        for pos in original_positions
    )
    hedged_value = sum(
        pos.get("current_price", pos.get("price", 0)) * pos.get("quantity", 0)
        for pos in hedged_positions
    )
    
    # Scenario analysis (simple price shocks)
    scenarios = []
    for shock_pct in [-0.20, -0.10, 0.00, 0.10]:
        original_scenario_value = original_value * (1 + shock_pct)
        hedged_scenario_value = hedged_value * (1 + shock_pct)
        
        # For puts, add intrinsic value if in the money
        if hedge_candidate.get("strategy") == "protective_put":
            instrument = hedge_candidate.get("instrument", {})
            strike = instrument.get("strike", 0)
            quantity = instrument.get("quantity", 0)
            
            # Current underlying price after shock
            underlying_price = instrument.get("strike", 100) / 0.95 * (1 + shock_pct)  # Approximate
            
            if underlying_price < strike:
                # Put is ITM
                intrinsic = max(0, strike - underlying_price) * quantity * 100
                hedged_scenario_value += intrinsic
        
        scenarios.append({
            "shock_pct": shock_pct,
            "original_value": round_to_precision(original_scenario_value),
            "hedged_value": round_to_precision(hedged_scenario_value),
            "protection": round_to_precision(hedged_scenario_value - original_scenario_value)
        })
    
    return {
        "original": {
            "var_95": original_var,
            "portfolio_value": round_to_precision(original_value)
        },
        "hedged": {
            "var_95": hedged_var,
            "portfolio_value": round_to_precision(hedged_value)
        },
        "improvement": {
            "var_reduction": round_to_precision(original_var - hedged_var),
            "var_reduction_pct": round_to_precision((original_var - hedged_var) / abs(original_var) * 100) if original_var != 0 else 0
        },
        "scenarios": scenarios,
        "cost": hedge_candidate.get("cost", 0)
    }
