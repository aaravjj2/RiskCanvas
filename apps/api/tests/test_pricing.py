import math
from models.pricing import black_scholes, black_scholes_call, black_scholes_put

def test_black_scholes_call():
    """Test Black-Scholes call option pricing with known values."""
    # Test case from Hull's "Options, Futures, and Other Derivatives"
    S = 40.0  # Stock price
    K = 40.0  # Strike price
    T = 0.25  # Time to maturity (3 months)
    r = 0.03  # Risk-free rate (3%)
    sigma = 0.20  # Volatility (20%)

    call_price = black_scholes_call(S, K, T, r, sigma)

    # Expected value from Hull's book: ~2.07
    expected = 2.07
    assert abs(call_price - expected) < 0.01

def test_black_scholes_put():
    """Test Black-Scholes put option pricing with known values."""
    # Test case from Hull's "Options, Futures, and Other Derivatives"
    S = 40.0  # Stock price
    K = 40.0  # Strike price
    T = 0.25  # Time to maturity (3 months)
    r = 0.03  # Risk-free rate (3%)
    sigma = 0.20  # Volatility (20%)

    put_price = black_scholes_put(S, K, T, r, sigma)

    # Expected value from Hull's book: ~1.97
    expected = 1.97
    assert abs(put_price - expected) < 0.01

def test_black_scholes_function():
    """Test the unified black_scholes function."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    call_price = black_scholes(S, K, T, r, sigma, 'call')
    put_price = black_scholes(S, K, T, r, sigma, 'put')

    # Verify that the call and put prices match the individual functions
    assert abs(call_price - black_scholes_call(S, K, T, r, sigma)) < 0.0001
    assert abs(put_price - black_scholes_put(S, K, T, r, sigma)) < 0.0001

def test_edge_cases():
    """Test edge cases for Black-Scholes pricing."""
    # In-the-money call
    call_price = black_scholes_call(50.0, 40.0, 1.0, 0.05, 0.20)
    assert call_price > 0

    # Out-of-the-money call
    call_price = black_scholes_call(30.0, 40.0, 1.0, 0.05, 0.20)
    assert call_price > 0

    # At-the-money call
    call_price = black_scholes_call(40.0, 40.0, 1.0, 0.05, 0.20)
    assert call_price > 0

    # Test with zero volatility
    call_price = black_scholes_call(40.0, 40.0, 1.0, 0.05, 0.0)
    # When volatility is 0, the option should be worth the intrinsic value
    expected = max(0, 40.0 - 40.0)  # Intrinsic value
    assert abs(call_price - expected) < 0.0001

def test_put_call_parity():
    """Test that put-call parity holds."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    call_price = black_scholes_call(S, K, T, r, sigma)
    put_price = black_scholes_put(S, K, T, r, sigma)

    # Put-call parity: C - P = S - K * e^(-rT)
    left_side = call_price - put_price
    right_side = S - K * math.exp(-r * T)

    assert abs(left_side - right_side) < 0.0001