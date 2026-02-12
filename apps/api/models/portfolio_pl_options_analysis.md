# Analysis of Portfolio Profit/Loss Calculation for Options

## Issue Summary

The `portfolio_pl` function in `apps/api/models/pricing.py` has an incomplete implementation for calculating portfolio profit/loss when the portfolio contains options.

## Current Implementation Problems

1. **Incorrect Purchase Price Handling**: The function uses a hardcoded `purchase_price = 0.5` instead of properly handling the case where purchase price data is available or calculating it correctly.

2. **Inappropriate Calculation Logic**: The current implementation doesn't correctly calculate profit/loss for options, as it compares the current Black-Scholes value against an arbitrary fixed purchase price.

3. **Incomplete Portfolio PL Calculation**: While the function attempts to process options, it doesn't properly include their contribution to the total portfolio profit/loss, leading to incomplete reporting.

## Analysis of the Problem

Looking at lines 662-748 in pricing.py:

```python
def portfolio_pl(positions: list) -> float:
    # ... function definition ...
    for position in positions:
        # ... stock handling ...
        elif position_type == 'option':
            # Extract option parameters
            current_price = position.get('current_price', 0.0)
            strike_price = position.get('strike_price', 0.0)
            time_to_maturity = position.get('time_to_maturity', 0.0)
            risk_free_rate = position.get('risk_free_rate', 0.0)
            volatility = position.get('volatility', 0.0)
            option_type = position.get('option_type', 'call')
            quantity = position.get('quantity', 0.0)

            # Only calculate if we have the necessary data
            if (current_price > 0 and strike_price > 0 and time_to_maturity > 0 and
                risk_free_rate > 0 and volatility > 0 and quantity > 0):

                # Calculate the Black-Scholes price for the current option
                option_price = black_scholes(current_price, strike_price, time_to_maturity,
                                           risk_free_rate, volatility, option_type)

                # ... problematic hardcoded purchase price ...
                purchase_price = 0.5  # This is wrong!

                # Calculate profit/loss for the option position
                pl = (current_option_value - purchase_price) * quantity
                total_pl += pl
```

The issue is specifically on line 742 where `purchase_price = 0.5` is hardcoded. This approach is fundamentally flawed because:

1. It doesn't use actual purchase price data from the position
2. It assumes all options were purchased at $0.5, which is incorrect
3. It doesn't properly handle the case where purchase price data is not available

## Expected Behavior

A complete implementation should:
1. Properly calculate the current value of options using Black-Scholes or similar
2. Either use actual purchase price data when available, or use a method that correctly accounts for the option's value at purchase
3. Include all portfolio positions (stocks and options) in the final profit/loss calculation

## Impact

This issue results in incomplete portfolio profit/loss reporting, where:
- Options in a portfolio are not properly valued for profit/loss calculation
- The final portfolio PL is misleading because option contributions are ignored or incorrectly calculated
- Users get inaccurate risk assessments and performance metrics

## Recommendation

The function needs to be extended to properly handle option positions by:
1. Using actual purchase price data when available in the position dictionary
2. Implementing a more robust approach for handling missing purchase price data
3. Ensuring that option profit/loss is calculated correctly and contributes to the total portfolio PL