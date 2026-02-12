import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import black_scholes

# Test black_scholes directly
print("Testing Black-Scholes function directly:")

# Parameters from test case
S = 40.0  # current_price (stock price)
K = 35.0  # strike_price
T = 0.5   # time_to_maturity
r = 0.03  # risk_free_rate
sigma = 0.20  # volatility
option_type = 'call'

result = black_scholes(S, K, T, r, sigma, option_type)
print(f"Black-Scholes call price: {result}")

# Test if we're using the correct function
print("\nTesting if black_scholes_call function is used:")
try:
    from models.pricing import black_scholes_call
    result2 = black_scholes_call(S, K, T, r, sigma)
    print(f"black_scholes_call result: {result2}")
except Exception as e:
    print(f"Error: {e}")