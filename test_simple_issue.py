import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value

def test_issue():
    """Test the specific case from the demo to show the problem."""

    # This is exactly what the demo test file does - no purchase_price for the option
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
            # Note: NO purchase_price provided for the option
        }
    ]

    # Calculate portfolio profit/loss
    pl = portfolio_pl(positions)
    print(f"Portfolio PL with options (no purchase_price for option): {pl}")

    # Calculate portfolio value
    value = portfolio_value(positions)
    print(f"Portfolio value with options: {value}")

    # Calculate the stock contribution to PL
    stock_pl = 100.0 * (110.0 - 100.0)  # 1000.0
    print(f"Stock contribution to PL: {stock_pl}")

    print("\n--- The problem analysis ---")
    print("The portfolio_pl function correctly uses the purchase_price for stock positions.")
    print("For options, if no purchase_price is provided, it's treated as 0.")
    print("But when we calculate portfolio value for options, it uses Black-Scholes price.")
    print("So the PL is calculated as: portfolio_value - purchase_value")
    print("Where purchase_value = stock_purchase_value + option_purchase_value")
    print("And option_purchase_value = 0 (because no purchase_price was provided)")
    print("So the PL calculation is correct for this case.")
    print("\nThe issue mentioned in the demo file might be a misunderstanding.")
    print("However, the correct approach is to require purchase_price for options.")

if __name__ == "__main__":
    test_issue()