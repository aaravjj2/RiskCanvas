"""
Demo script showing how to use the Black-Scholes Greeks functions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.pricing import (
    black_scholes_call,
    black_scholes_put,
    black_scholes_delta,
    black_scholes_gamma,
    black_scholes_vega,
    black_scholes_theta,
    black_scholes_rho
)

def main():
    # Example parameters
    S = 100.0  # Current stock price
    K = 100.0  # Strike price
    T = 0.5    # Time to maturity (6 months)
    r = 0.05   # Risk-free rate (5%)
    sigma = 0.20  # Volatility (20%)

    print("Black-Scholes Greeks Demo")
    print("=" * 30)

    # Calculate option prices
    call_price = black_scholes_call(S, K, T, r, sigma)
    put_price = black_scholes_put(S, K, T, r, sigma)

    print(f"Call option price: ${call_price:.4f}")
    print(f"Put option price: ${put_price:.4f}")
    print()

    # Calculate Greeks
    call_delta = black_scholes_delta(S, K, T, r, sigma, 'call')
    put_delta = black_scholes_delta(S, K, T, r, sigma, 'put')

    call_gamma = black_scholes_gamma(S, K, T, r, sigma)
    put_gamma = black_scholes_gamma(S, K, T, r, sigma)

    call_vega = black_scholes_vega(S, K, T, r, sigma)
    put_vega = black_scholes_vega(S, K, T, r, sigma)

    call_theta = black_scholes_theta(S, K, T, r, sigma, 'call')
    put_theta = black_scholes_theta(S, K, T, r, sigma, 'put')

    call_rho = black_scholes_rho(S, K, T, r, sigma, 'call')
    put_rho = black_scholes_rho(S, K, T, r, sigma, 'put')

    print("Greeks for Call Option:")
    print(f"  Delta: {call_delta:.4f}")
    print(f"  Gamma: {call_gamma:.4f}")
    print(f"  Vega:  {call_vega:.4f}")
    print(f"  Theta: {call_theta:.4f}")
    print(f"  Rho:   {call_rho:.4f}")
    print()

    print("Greeks for Put Option:")
    print(f"  Delta: {put_delta:.4f}")
    print(f"  Gamma: {put_gamma:.4f}")
    print(f"  Vega:  {put_vega:.4f}")
    print(f"  Theta: {put_theta:.4f}")
    print(f"  Rho:   {put_rho:.4f}")
    print()

    # Example with zero volatility
    print("Example with zero volatility:")
    call_delta_zero = black_scholes_delta(100.0, 100.0, 0.5, 0.05, 0.0, 'call')
    print(f"  Delta (ATM, zero volatility): {call_delta_zero:.4f}")

    put_delta_zero = black_scholes_delta(100.0, 100.0, 0.5, 0.05, 0.0, 'put')
    print(f"  Delta (ATM, zero volatility): {put_delta_zero:.4f}")

if __name__ == "__main__":
    main()