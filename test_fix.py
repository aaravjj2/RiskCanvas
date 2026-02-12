import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value

# Test the fixed function with the exact same test case
positions = [
    {
        'type': 'stock',
        'current_price': 110.0,
        'purchase_price': 100.0,
        'quantity': 100.0
    },
    {
        'type': 'option',
        'current_price': 40.0,  # Stock price
        'strike_price': 35.0,
        'time_to_maturity': 0.5,
        'risk_free_rate': 0.03,
        'volatility': 0.20,
        'option_type': 'call',
        'quantity': 50.0
    }
]

print("=== Testing Fixed Portfolio PL Function ===")

# Calculate portfolio profit/loss
pl = portfolio_pl(positions)
print(f"Portfolio PL with options: {pl}")

# Calculate portfolio value
value = portfolio_value(positions)
print(f"Portfolio value with options: {value}")

# Show what each component contributes
stock_pl = 100.0 * (110.0 - 100.0)  # 1000.0
print(f"Stock contribution to PL: {stock_pl}")

print("\n--- Analysis ---")
print("With the fix:")
print("- Stock: 100 shares at $100 purchase price, current price $110 -> PL = 1000")
print("- Option: 50 contracts, calculated Black-Scholes price as purchase price -> PL = 295.88")
print("- Total PL = 1000 + 295.88 = 1295.88")

print("\n--- Expected vs Actual ---")
print("Expected PL: 1295.88")
print(f"Actual PL: {pl}")
print(f"Difference: {pl - 1295.88}")

# Let's also test with explicit purchase price to make sure that still works
print("\n=== Testing with Explicit Purchase Price ===")
positions_with_purchase = [
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
        'purchase_price': 5.9177  # Black-Scholes price from our calculation
    }
]

pl_with_purchase = portfolio_pl(positions_with_purchase)
print(f"Portfolio PL with explicit purchase price: {pl_with_purchase}")