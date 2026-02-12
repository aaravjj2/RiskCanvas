import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.pricing import (
    black_scholes, black_scholes_call, black_scholes_put, black_scholes_delta,
    black_scholes_gamma, black_scholes_vega, black_scholes_theta, black_scholes_rho,
    bond_pv, bond_duration, bond_convexity, bond_dv01,
    stock_pl, stock_delta_exposure, portfolio_pl, portfolio_delta_exposure,
    historical_var, parametric_var, portfolio_var, calculate_returns, calculate_log_returns
)

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

def test_bond_pv():
    """Test bond present value calculation."""
    # Test case: 5% coupon, 1000 face value, 2 years maturity, 4% yield
    pv = bond_pv(0.05, 1000.0, 2.0, 0.04, 1)
    assert pv > 0

    # Test case with zero coupon
    pv_zero_coupon = bond_pv(0.0, 1000.0, 2.0, 0.04, 1)
    assert pv_zero_coupon > 0
    assert pv_zero_coupon < 1000.0  # Should be less than face value

    # Test case with zero maturity
    pv_zero_maturity = bond_pv(0.05, 1000.0, 0.0, 0.04, 1)
    assert abs(pv_zero_maturity - 1000.0) < 0.0001  # Should equal face value

def test_bond_duration():
    """Test bond duration calculation."""
    # Test case: 5% coupon, 1000 face value, 2 years maturity, 4% yield
    duration = bond_duration(0.05, 1000.0, 2.0, 0.04, 1)
    assert duration > 0

    # Test case with zero maturity
    duration_zero = bond_duration(0.05, 1000.0, 0.0, 0.04, 1)
    assert abs(duration_zero) < 0.0001  # Should be zero

    # Test case with zero coupon
    duration_zero_coupon = bond_duration(0.0, 1000.0, 2.0, 0.04, 1)
    assert duration_zero_coupon > 0

def test_bond_convexity():
    """Test bond convexity calculation."""
    # Test case: 5% coupon, 1000 face value, 2 years maturity, 4% yield
    convexity = bond_convexity(0.05, 1000.0, 2.0, 0.04, 1)
    assert convexity > 0

    # Test case with zero maturity
    convexity_zero = bond_convexity(0.05, 1000.0, 0.0, 0.04, 1)
    assert abs(convexity_zero) < 0.0001  # Should be zero

    # Test case with zero coupon
    convexity_zero_coupon = bond_convexity(0.0, 1000.0, 2.0, 0.04, 1)
    assert convexity_zero_coupon > 0

def test_bond_dv01():
    """Test bond DV01 calculation."""
    # Test case: 5% coupon, 1000 face value, 2 years maturity, 4% yield
    dv01 = bond_dv01(0.05, 1000.0, 2.0, 0.04, 1)
    assert dv01 < 0  # DV01 should be negative


def test_stock_pl():
    """Test stock profit/loss calculation."""
    # Test long position
    pl = stock_pl(110.0, 100.0, 100.0)
    assert pl == 1000.0  # (110 - 100) * 100 = 1000

    # Test short position
    pl = stock_pl(90.0, 100.0, 100.0)
    assert pl == -1000.0  # (90 - 100) * 100 = -1000

    # Test zero profit
    pl = stock_pl(100.0, 100.0, 100.0)
    assert pl == 0.0  # (100 - 100) * 100 = 0


def test_stock_delta_exposure():
    """Test stock delta exposure calculation."""
    # Test long position
    delta = stock_delta_exposure(100.0, 100.0)
    assert delta == 100.0  # 1.0 * 100 = 100

    # Test short position
    delta = stock_delta_exposure(100.0, -100.0)
    assert delta == -100.0  # 1.0 * -100 = -100

    # Test zero quantity
    delta = stock_delta_exposure(100.0, 0.0)
    assert delta == 0.0  # 1.0 * 0 = 0


def test_portfolio_pl():
    """Test portfolio profit/loss calculation."""
    # Test empty portfolio
    pl = portfolio_pl([])
    assert pl == 0.0

    # Test single stock position
    positions = [
        {
            'type': 'stock',
            'current_price': 110.0,
            'purchase_price': 100.0,
            'quantity': 100.0
        }
    ]
    pl = portfolio_pl(positions)
    assert pl == 1000.0

    # Test multiple positions
    positions = [
        {
            'type': 'stock',
            'current_price': 110.0,
            'purchase_price': 100.0,
            'quantity': 100.0
        },
        {
            'type': 'stock',
            'current_price': 90.0,
            'purchase_price': 100.0,
            'quantity': 100.0
        }
    ]
    pl = portfolio_pl(positions)
    assert pl == 0.0  # 1000 - 1000 = 0


def test_portfolio_delta_exposure():
    """Test portfolio delta exposure calculation."""
    # Test empty portfolio
    delta = portfolio_delta_exposure([])
    assert delta == 0.0

    # Test single stock position
    positions = [
        {
            'type': 'stock',
            'current_price': 100.0,
            'quantity': 100.0
        }
    ]
    delta = portfolio_delta_exposure(positions)
    assert delta == 100.0

    # Test multiple stock positions
    positions = [
        {
            'type': 'stock',
            'current_price': 100.0,
            'quantity': 100.0
        },
        {
            'type': 'stock',
            'current_price': 100.0,
            'quantity': -50.0
        }
    ]
    delta = portfolio_delta_exposure(positions)
    assert delta == 50.0  # 100 + (-50) = 50

    # Test with option positions (no delta provided)
    positions = [
        {
            'type': 'stock',
            'current_price': 100.0,
            'quantity': 100.0
        },
        {
            'type': 'option',
            'current_price': 10.0,
            'quantity': 50.0
        }
    ]
    delta = portfolio_delta_exposure(positions)
    assert delta == 100.0  # Only stock positions contribute to delta

    # Test case with zero maturity
    dv01_zero = bond_dv01(0.05, 1000.0, 0.0, 0.04, 1)
    assert abs(dv01_zero) < 0.0001  # Should be zero

    # Test case with zero coupon
    dv01_zero_coupon = bond_dv01(0.0, 1000.0, 2.0, 0.04, 1)
    assert dv01_zero_coupon < 0  # Should still be negative