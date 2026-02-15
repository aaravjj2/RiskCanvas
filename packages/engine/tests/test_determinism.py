"""
Test determinism and numeric stability of engine calculations
"""

import json
import hashlib
from pathlib import Path
import sys

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pricing import price_option, price_stock
from src.greeks import calculate_greeks, delta, gamma, vega, theta, rho
from src.portfolio import portfolio_pnl, portfolio_greeks
from src.var import var_parametric, var_historical
from src.scenario import scenario_run
from src.config import round_to_precision


def test_determinism_option_pricing():
    """Test that option pricing produces identical results on repeated runs"""
    params = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    # Run 10 times
    results = [price_option(**params) for _ in range(10)]
    
    # All results should be identical
    assert len(set(results)) == 1, f"Non-deterministic results: {results}"
    print(f"✓ Option pricing deterministic: {results[0]}")


def test_determinism_greeks():
    """Test that Greeks calculation produces identical results"""
    params = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    # Run 10 times
    results = [calculate_greeks(**params) for _ in range(10)]
    
    # Convert to JSON strings for comparison
    json_results = [json.dumps(r, sort_keys=True) for r in results]
    
    # All should be identical
    assert len(set(json_results)) == 1, f"Non-deterministic Greeks"
    print(f"✓ Greeks calculation deterministic: {results[0]}")


def test_determinism_portfolio_with_fixtures():
    """Test portfolio calculations with fixture data produce identical hashes"""
    fixture_path = Path(__file__).parent.parent.parent.parent / "fixtures" / "portfolio_1.json"
    
    if not fixture_path.exists():
        print(f"⚠ Fixture not found: {fixture_path}")
        return
    
    with open(fixture_path) as f:
        portfolio = json.load(f)
    
    positions = portfolio.get("assets", [])
    
    # Add required fields for P&L calc
    for pos in positions:
        pos["current_price"] = pos.get("price", 0)
        pos["purchase_price"] = pos.get("price", 0) * 0.95  # Mock 5% gain
    
    # Calculate P&L 10 times
    results = [portfolio_pnl(positions) for _ in range(10)]
    
    # All should be identical
    assert len(set(results)) == 1, f"Non-deterministic portfolio P&L: {results}"
    print(f"✓ Portfolio P&L deterministic: {results[0]}")


def test_determinism_var():
    """Test VaR calculations are deterministic"""
    # Parametric VaR
    var_results = [
        var_parametric(
            portfolio_value=1000000.0,
            volatility=0.15,
            confidence_level=0.95,
            time_horizon_days=1
        )
        for _ in range(10)
    ]
    
    assert len(set(var_results)) == 1, "Non-deterministic parametric VaR"
    print(f"✓ Parametric VaR deterministic: {var_results[0]}")
    
    # Historical VaR
    historical_returns = [-0.05, -0.02, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05]
    hist_var_results = [
        var_historical(
            current_value=1000000.0,
            historical_returns=historical_returns,
            confidence_level=0.95
        )
        for _ in range(10)
    ]
    
    assert len(set(hist_var_results)) == 1, "Non-deterministic historical VaR"
    print(f"✓ Historical VaR deterministic: {hist_var_results[0]}")


def test_determinism_scenario():
    """Test scenario analysis is deterministic"""
    positions = [
        {
            "type": "stock",
            "symbol": "AAPL",
            "quantity": 100,
            "current_price": 150.0,
            "purchase_price": 140.0
        }
    ]
    
    scenarios = [
        {
            "name": "Market Crash",
            "shock_type": "price",
            "parameters": {"price_change_pct": -20.0}
        }
    ]
    
    # Run 10 times
    results = [scenario_run(positions, scenarios) for _ in range(10)]
    
    # Convert to JSON for comparison
    json_results = [json.dumps(r, sort_keys=True) for r in results]
    
    assert len(set(json_results)) == 1, "Non-deterministic scenario analysis"
    print(f"✓ Scenario analysis deterministic")


def test_numeric_stability():
    """Test that rounding is consistent"""
    # Test various precision levels
    test_value = 1.123456789012345
    
    rounded = round_to_precision(test_value)
    
    # Should be rounded to 8 decimal places
    expected = round(test_value, 8)
    
    assert rounded == expected, f"Unexpected rounding: {rounded} vs {expected}"
    print(f"✓ Numeric rounding consistent: {rounded}")


def test_output_hash_consistency():
    """Test that identical inputs produce identical output hashes"""
    params = {
        "S": 100.0,
        "K": 105.0,
        "T": 0.25,
        "r": 0.05,
        "sigma": 0.2,
        "option_type": "call"
    }
    
    def calculate_and_hash():
        price = price_option(**params)
        greeks = calculate_greeks(**params)
        
        output = {
            "price": price,
            "greeks": greeks
        }
        
        # Create deterministic hash
        output_json = json.dumps(output, sort_keys=True)
        return hashlib.sha256(output_json.encode()).hexdigest()
    
    # Generate hashes 10 times
    hashes = [calculate_and_hash() for _ in range(10)]
    
    # All hashes should be identical
    assert len(set(hashes)) == 1, f"Non-deterministic output hashes"
    print(f"✓ Output hash consistent: {hashes[0][:16]}...")


if __name__ == "__main__":
    print("Running determinism and stability tests...\n")
    
    test_determinism_option_pricing()
    test_determinism_greeks()
    test_determinism_portfolio_with_fixtures()
    test_determinism_var()
    test_determinism_scenario()
    test_numeric_stability()
    test_output_hash_consistency()
    
    print("\n✅ All determinism tests passed!")
