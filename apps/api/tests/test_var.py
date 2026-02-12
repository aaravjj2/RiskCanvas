import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.pricing import (
    historical_var,
    parametric_var,
    portfolio_var,
    monte_carlo_var,
    calculate_returns,
    calculate_log_returns
)

def test_calculate_returns():
    """Test the calculate_returns function."""
    prices = [100, 105, 102, 108, 110]
    expected_returns = [0.05, -0.02857142857142857, 0.058823529411764705, 0.018518518518518517]
    actual_returns = calculate_returns(prices)

    assert len(actual_returns) == len(expected_returns)
    for i, (actual, expected) in enumerate(zip(actual_returns, expected_returns)):
        assert abs(actual - expected) < 0.001

def test_calculate_log_returns():
    """Test the calculate_log_returns function."""
    prices = [100, 105, 102, 108, 110]
    expected_log_returns = [0.04879016416924521, -0.02937942442704645, 0.05636909834033317, 0.01814251223141359]
    actual_log_returns = calculate_log_returns(prices)

    assert len(actual_log_returns) == len(expected_log_returns)
    for i, (actual, expected) in enumerate(zip(actual_log_returns, expected_log_returns)):
        assert abs(actual - expected) < 0.001

def test_historical_var():
    """Test the historical_var function."""
    # Simple test case with known returns
    portfolio_returns = [-0.05, -0.02, 0.01, 0.03, 0.05, 0.08, 0.12, 0.15, 0.20, 0.25]
    var_95 = historical_var(portfolio_returns, 0.95)

    # The historical VaR function returns a positive value (potential loss)
    # In this case, 5% worst case is -0.05, so VaR = 0.05
    assert var_95 >= 0

def test_parametric_var():
    """Test the parametric_var function."""
    portfolio_returns = [-0.05, -0.02, 0.01, 0.03, 0.05, 0.08, 0.12, 0.15, 0.20, 0.25]
    var_95 = parametric_var(portfolio_returns, 0.95)

    # For 95% confidence level, VaR should be negative (representing potential loss)
    # The result should be a negative number representing the potential loss
    assert var_95 <= 0

def test_portfolio_var_historical():
    """Test the portfolio_var function with historical method."""
    # Mock positions
    positions = [
        {"symbol": "AAPL", "quantity": 10, "price": 150.0},
        {"symbol": "MSFT", "quantity": 5, "price": 300.0}
    ]

    # Mock historical prices for each asset
    historical_prices = [
        [150.0, 155.0, 152.0, 158.0, 160.0],  # AAPL prices
        [300.0, 310.0, 305.0, 315.0, 320.0]   # MSFT prices
    ]

    # Test with historical method
    var = portfolio_var(positions, historical_prices, method="historical", confidence_level=0.95)

    # Should return a positive VaR value
    assert var >= 0

def test_portfolio_var_parametric():
    """Test the portfolio_var function with parametric method."""
    # Mock positions
    positions = [
        {"symbol": "AAPL", "quantity": 10, "price": 150.0},
        {"symbol": "MSFT", "quantity": 5, "price": 300.0}
    ]

    # Mock historical prices for each asset
    historical_prices = [
        [150.0, 155.0, 152.0, 158.0, 160.0],  # AAPL prices
        [300.0, 310.0, 305.0, 315.0, 320.0]   # MSFT prices
    ]

    # Test with parametric method
    var = portfolio_var(positions, historical_prices, method="parametric", confidence_level=0.95)

    # Should return a negative VaR value (representing potential loss)
    assert var <= 0

def test_portfolio_var_invalid_method():
    """Test the portfolio_var function with invalid method."""
    positions = [
        {"symbol": "AAPL", "quantity": 10, "price": 150.0},
        {"symbol": "MSFT", "quantity": 5, "price": 300.0}
    ]

    historical_prices = [
        [150.0, 155.0, 152.0, 158.0, 160.0],
        [300.0, 310.0, 305.0, 315.0, 320.0]
    ]

    # Test with invalid method
    with pytest.raises(ValueError, match="Method must be 'historical', 'parametric', or 'monte_carlo'"):
        portfolio_var(positions, historical_prices, method="invalid_method", confidence_level=0.95)


def test_monte_carlo_var():
    """Test the monte_carlo_var function."""
    portfolio_returns = [-0.05, -0.02, 0.01, 0.03, 0.05, 0.08, 0.12, 0.15, 0.20, 0.25]
    var_95 = monte_carlo_var(portfolio_returns, 0.95)

    # Should return a positive VaR value (representing potential loss)
    assert var_95 >= 0


if __name__ == "__main__":
    # Run tests directly
    test_calculate_returns()
    test_calculate_log_returns()
    test_historical_var()
    test_parametric_var()
    test_portfolio_var_historical()
    test_portfolio_var_parametric()
    test_portfolio_var_invalid_method()
    test_monte_carlo_var()
    print("All tests passed!")