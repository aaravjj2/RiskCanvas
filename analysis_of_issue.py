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

print("=== Manual Calculation of Correct Values ===")

# Calculate stock contribution
stock_current_value = 110.0 * 100.0  # 11000
stock_purchase_value = 100.0 * 100.0  # 10000
stock_pl = stock_current_value - stock_purchase_value  # 1000

print(f"Stock contribution:")
print(f"  Current value: {stock_current_value}")
print(f"  Purchase value: {stock_purchase_value}")
print(f"  PL: {stock_pl}")

# Calculate option contribution
# Option current value (Black-Scholes price)
option_current_price = black_scholes(40.0, 35.0, 0.5, 0.03, 0.20, 'call')  # 5.9177
option_current_value = option_current_price * 50.0  # 295.885
print(f"\nOption contribution:")
print(f"  Black-Scholes price: {option_current_price}")
print(f"  Current value: {option_current_value}")

# The issue is that the purchase_price is not provided for the option
# So the current function skips adding the option to purchase_value
# That's why we get: PL = 11295.884947241831 - 10000 = 1295.8849472418315

# But what should be the correct purchase value for the option?
# In a real scenario, the option would have been purchased at its Black-Scholes price
# So the correct approach is to calculate the Black-Scholes price and use that as purchase value

# If we use the Black-Scholes price as the purchase price for the option:
option_purchase_value = option_current_price * 50.0  # 295.885
print(f"  If we used Black-Scholes price as purchase value: {option_purchase_value}")

# Then the correct PL would be:
# Portfolio value: 11295.884947241831
# Purchase value: 10000 (stock) + 295.885 (option) = 10295.885
# PL = 11295.884947241831 - 10295.885 = 1000.0

print(f"\nIf we used Black-Scholes price as purchase value for option:")
print(f"  Total purchase value: 10000 + {option_purchase_value} = 10295.885")
print(f"  Correct PL: 11295.884947241831 - 10295.885 = 1000.0")

print("\n--- Problem Analysis ---")
print("The current function skips options with no purchase_price (purchase_price = 0)")
print("But in the real world, we should use the Black-Scholes price as the purchase price for options")
print("when no explicit purchase price is provided.")