#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from models.pricing import portfolio_pl, portfolio_value

def debug_portfolio_pl():
    """Debug what's happening with portfolio_pl."""

    print("=== Debugging Portfolio PL ===\n")

    # Test case from test_portfolio_pl_issue.py
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

    print("Positions data:")
    for i, pos in enumerate(positions):
        print(f"  Position {i}: {pos}")

    # Calculate portfolio value
    value = portfolio_value(positions)
    print(f"\nPortfolio value: {value}")

    # Calculate portfolio pl - let's trace through what portfolio_pl does
    print("\nTracing portfolio_pl calculation:")

    # First calculate current value
    current_value = portfolio_value(positions)
    print(f"Current value: {current_value}")

    # Then calculate purchase value manually
    total_purchase_value = 0.0

    for position in positions:
        position_type = position.get('type', 'stock')
        print(f"\nProcessing position of type: {position_type}")

        if position_type == 'stock':
            purchase_price = position.get('purchase_price', 0.0)
            quantity = position.get('quantity', 0.0)
            print(f"  Stock: purchase_price={purchase_price}, quantity={quantity}")
            if purchase_price > 0 and quantity > 0:
                total_purchase_value += purchase_price * quantity
                print(f"  Adding to purchase value: {purchase_price * quantity}")

        elif position_type == 'option':
            # For options, we use the purchase_price if available
            purchase_price = position.get('purchase_price', 0.0)
            quantity = position.get('quantity', 0.0)
            print(f"  Option: purchase_price={purchase_price}, quantity={quantity}")
            if purchase_price > 0 and quantity > 0:
                total_purchase_value += purchase_price * quantity
                print(f"  Adding to purchase value: {purchase_price * quantity}")

    print(f"\nTotal purchase value: {total_purchase_value}")
    pl = current_value - total_purchase_value
    print(f"Portfolio PL: {pl}")

if __name__ == "__main__":
    debug_portfolio_pl()