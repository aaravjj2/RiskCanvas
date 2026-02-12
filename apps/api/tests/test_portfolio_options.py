import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.pricing import portfolio_pl, portfolio_value

def test_portfolio_pl_with_options():
    """Test portfolio profit/loss calculation with options."""

    # Test case with both stocks and options
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
            'quantity': 50.0,
            'purchase_price': 2.0  # Add purchase price for proper calculation
        }
    ]

    # Calculate portfolio profit/loss
    pl = portfolio_pl(positions)
    print(f"Portfolio PL with options: {pl}")

    # Calculate portfolio value
    value = portfolio_value(positions)
    print(f"Portfolio value with options: {value}")

    # Test with only options
    options_only = [
        {
            'type': 'option',
            'current_price': 40.0,  # Stock price
            'strike_price': 35.0,
            'time_to_maturity': 0.5,
            'risk_free_rate': 0.03,
            'volatility': 0.20,
            'option_type': 'call',
            'quantity': 50.0,
            'purchase_price': 2.0  # Add purchase price for proper calculation
        }
    ]

    pl_options = portfolio_pl(options_only)
    print(f"Options-only PL: {pl_options}")

    value_options = portfolio_value(options_only)
    print(f"Options-only value: {value_options}")

if __name__ == "__main__":
    test_portfolio_pl_with_options()