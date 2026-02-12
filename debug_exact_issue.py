import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value, black_scholes

# Reproduce the exact test case
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

print("=== Detailed Debug ===")
print("Positions:")
for i, pos in enumerate(positions):
    print(f"  Position {i}: {pos}")

# Calculate what Black-Scholes value would be for the option
option_price = black_scholes(40.0, 35.0, 0.5, 0.03, 0.20, 'call')
print(f"\nBlack-Scholes option price: {option_price}")

# Calculate portfolio value
value = portfolio_value(positions)
print(f"Portfolio value: {value}")

# Manual calculation of what should be the purchase value
# Stock purchase value: 100 * 100 = 10000
# Option purchase value: 0 (since no purchase_price provided)
# So PL = 11295.88 - 10000 = 1295.88

# What the current function returns
pl = portfolio_pl(positions)
print(f"Current function portfolio_pl result: {pl}")

# What should happen:
# If no purchase_price for option, we should calculate the Black-Scholes price as the purchase value
# But that's not how the current function works - it just skips the option in purchase value calculation
print("\n--- The Problem ---")
print("When no purchase_price is provided for options, the current function:")
print("1. Calculates correct current value (including option)")
print("2. Skips adding the option to purchase value (because purchase_price = 0)")
print("3. Returns PL = current_value - 10000 = 1295.88")

print("\n--- What It Should Do ---")
print("If no purchase_price is provided for options, it should still include the option in purchase value calculation.")
print("But there's no purchase_price to use, so the issue is: what to use?")
print("The correct approach would be to use the Black-Scholes price as the purchase price when no explicit one is provided.")
