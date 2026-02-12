import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

# Let's run the original test to see what's happening with the actual implementation
# I'll directly call the functions and check what happens

# Let me see what happens if I just run a very basic check
from models.pricing import portfolio_value, portfolio_pl

# Simple test case that should make it clear what's happening
positions = [
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

print("Positions:")
for i, pos in enumerate(positions):
    print(f"  {i}: {pos}")

# Calculate values
value = portfolio_value(positions)
print(f"\nPortfolio value: {value}")

pl = portfolio_pl(positions)
print(f"Portfolio PL: {pl}")

# Manual calculation for verification:
# Stock: 100 * 110 = 11000 (current)
#      : 100 * 100 = 10000 (purchase)
#      : PL = 1000
# Option: 50 * 5.9177 = 295.885 (current)
#       : 50 * 5.9177 = 295.885 (purchase) - This is what my fix should calculate
# Total PL = 1000 + (295.885 - 295.885) = 1000 (if no purchase price is given, should be same as stock)

# But wait, that's wrong logic. If the option had a purchase price of 0, we should have added 0 to purchase_value
# The current function skips it, so we get PL = 11295.88 - 10000 = 1295.88

# If we use Black-Scholes price as purchase value, we get:
# Purchase value = 10000 + 295.885 = 10295.885
# PL = 11295.884947241831 - 10295.885 = 1000.0

print("\nExpected results with correct fix:")
print("If we calculate Black-Scholes price as purchase price for option:")
print("  Stock: 10000 (purchase) + 295.885 (option purchase) = 10295.885")
print("  PL = 11295.884947241831 - 10295.885 = 1000.0")