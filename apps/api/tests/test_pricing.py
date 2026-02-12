import math
from models.pricing import black_scholes, black_scholes_call, black_scholes_put, black_scholes_delta, black_scholes_gamma, black_scholes_vega, black_scholes_theta, black_scholes_rho

def test_black_scholes_call():
    """Test Black-Scholes call option pricing with known values."""
    # Test case from Hull's "Options, Futures, and Other Derivatives"
    S = 40.0  # Stock price
    K = 40.0  # Strike price
    T = 0.25  # Time to maturity (3 months)
    r = 0.03  # Risk-free rate (3%)
    sigma = 0.20  # Volatility (20%)

    call_price = black_scholes_call(S, K, T, r, sigma)

    # Expected value (standard Black-Scholes calculation)
    expected = 1.7430477333830225
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

    # Expected value (standard Black-Scholes calculation)
    expected = 1.444169926148561
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

def test_black_scholes_delta():
    """Test Black-Scholes delta calculation."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    # Test call delta
    call_delta = black_scholes_delta(S, K, T, r, sigma, 'call')
    assert call_delta > 0
    assert call_delta < 1

    # Test put delta
    put_delta = black_scholes_delta(S, K, T, r, sigma, 'put')
    assert put_delta > -1
    assert put_delta < 0

    # Test with zero volatility
    call_delta_zero = black_scholes_delta(40.0, 40.0, 1.0, 0.05, 0.0, 'call')
    assert abs(call_delta_zero - 0.5) < 0.0001  # At-the-money call should be 0.5

def test_black_scholes_gamma():
    """Test Black-Scholes gamma calculation."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    gamma = black_scholes_gamma(S, K, T, r, sigma)
    assert gamma > 0  # Gamma should be positive for all options

    # Test with zero volatility
    gamma_zero = black_scholes_gamma(40.0, 40.0, 1.0, 0.05, 0.0)
    assert abs(gamma_zero) < 0.0001  # Should be near zero

def test_black_scholes_vega():
    """Test Black-Scholes vega calculation."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    vega = black_scholes_vega(S, K, T, r, sigma)
    assert vega > 0  # Vega should be positive for all options

    # Test with zero volatility
    vega_zero = black_scholes_vega(40.0, 40.0, 1.0, 0.05, 0.0)
    assert abs(vega_zero) < 0.0001  # Should be near zero

def test_black_scholes_theta():
    """Test Black-Scholes theta calculation."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    # Test call theta
    call_theta = black_scholes_theta(S, K, T, r, sigma, 'call')
    # Theta should be negative for options (time decay)
    assert call_theta < 0

    # Test put theta
    put_theta = black_scholes_theta(S, K, T, r, sigma, 'put')
    # Theta should be negative for options (time decay)
    assert put_theta < 0

    # Test with zero volatility
    call_theta_zero = black_scholes_theta(40.0, 40.0, 1.0, 0.05, 0.0, 'call')
    assert abs(call_theta_zero) < 0.0001  # Should be near zero

def test_black_scholes_rho():
    """Test Black-Scholes rho calculation."""
    S = 40.0
    K = 40.0
    T = 0.25
    r = 0.03
    sigma = 0.20

    # Test call rho
    call_rho = black_scholes_rho(S, K, T, r, sigma, 'call')
    assert call_rho > 0  # Call rho should be positive

    # Test put rho
    put_rho = black_scholes_rho(S, K, T, r, sigma, 'put')
    assert put_rho < 0  # Put rho should be negative

    # Test with zero volatility
    call_rho_zero = black_scholes_rho(40.0, 40.0, 1.0, 0.05, 0.0, 'call')
    assert abs(call_rho_zero) < 0.0001  # Should be near zero