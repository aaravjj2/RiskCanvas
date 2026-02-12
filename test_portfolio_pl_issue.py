import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value

def demonstrate_current_issue():
    """Demonstrate the current issue with portfolio_pl and options."""

    print("=== Demonstrating Portfolio PL Issue with Options ===\n")

    # Test case: Portfolio with both stocks and options
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

    # Calculate portfolio profit/loss
    pl = portfolio_pl(positions)
    print(f"Portfolio PL with options: {pl}")

    # Calculate portfolio value
    value = portfolio_value(positions)
    print(f"Portfolio value with options: {value}")

    # Show what each component contributes
    stock_pl = 100.0 * (110.0 - 100.0)  # 1000.0
    print(f"Stock contribution to PL: {stock_pl}")

    # The option portion is calculated incorrectly due to hardcoded purchase_price = 0.5
    # So we have 50 * (option_price - 0.5) where option_price is Black-Scholes value
    print("\n--- Analysis ---")
    print("The function uses a hardcoded purchase_price = 0.5 in line 742")
    print("This means option PL = quantity * (Black-Scholes_price - 0.5)")
    print("Instead of using the actual purchase price data")
    print("This results in incorrect profit/loss calculation for options")

if __name__ == "__main__":
    demonstrate_current_issue()