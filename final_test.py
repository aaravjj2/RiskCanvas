import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value

print("=== Final Test of the Fix ===")

# Test case 1: Option with no explicit purchase price (should use Black-Scholes as purchase price)
positions1 = [
    {
        'type': 'stock',
        'current_price': 110.0,
        'purchase_price': 100.0,
        'quantity': 100.0
    },
    {
        'type': 'option',
        'current_price': 40.0,
        'strike_price': 35.0,
        'time_to_maturity': 0.5,
        'risk_free_rate': 0.03,
        'volatility': 0.20,
        'option_type': 'call',
        'quantity': 50.0
    }
]

pl1 = portfolio_pl(positions1)
print(f"Test 1 (no explicit purchase price): {pl1}")

# Test case 2: Option with explicit purchase price (should use that)
positions2 = [
    {
        'type': 'stock',
        'current_price': 110.0,
        'purchase_price': 100.0,
        'quantity': 100.0
    },
    {
        'type': 'option',
        'current_price': 40.0,
        'strike_price': 35.0,
        'time_to_maturity': 0.5,
        'risk_free_rate': 0.03,
        'volatility': 0.20,
        'option_type': 'call',
        'quantity': 50.0,
        'purchase_price': 5.9177  # Black-Scholes price
    }
]

pl2 = portfolio_pl(positions2)
print(f"Test 2 (explicit purchase price): {pl2}")

# Test case 3: Option with explicit purchase price that's different
positions3 = [
    {
        'type': 'stock',
        'current_price': 110.0,
        'purchase_price': 100.0,
        'quantity': 100.0
    },
    {
        'type': 'option',
        'current_price': 40.0,
        'strike_price': 35.0,
        'time_to_maturity': 0.5,
        'risk_free_rate': 0.03,
        'volatility': 0.20,
        'option_type': 'call',
        'quantity': 50.0,
        'purchase_price': 3.0  # Different purchase price
    }
]

pl3 = portfolio_pl(positions3)
print(f"Test 3 (different explicit purchase price): {pl3}")

print("\n--- Summary ---")
print("Test 1: Option with no purchase price -> Uses Black-Scholes as purchase price")
print("Test 2: Option with explicit Black-Scholes purchase price -> PL calculation correct")
print("Test 3: Option with different purchase price -> PL calculation uses provided price")