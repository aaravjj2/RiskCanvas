# Analysis of Portfolio Profit/Loss Calculation for Options

## Issue Summary

The `portfolio_pl` function in `apps/api/models/pricing.py` has an incomplete implementation for calculating portfolio profit/loss when the portfolio contains options.

## Current Implementation Problems

1. **Incorrect Purchase Price Handling**: The function previously used a hardcoded `purchase_price = 0.5` instead of properly handling the case where purchase price data is available or calculating it correctly.

2. **Inappropriate Calculation Logic**: The previous implementation didn't correctly calculate profit/loss for options, as it compared against an arbitrary fixed purchase price.

3. **Incomplete Portfolio PL Calculation**: While the function attempted to process options, it didn't properly include their contribution to the total portfolio profit/loss, leading to incomplete reporting.

## Updated Analysis

The current implementation now:
1. Retrieves `purchase_price` from the position data using `position.get('purchase_price', 0.0)`
2. If `purchase_price` is provided, calculates option PL = quantity * (Black-Scholes_price - purchase_price)
3. If `purchase_price` is not provided (0.0), returns 0 to indicate that meaningful profit/loss calculation cannot be performed

This approach is more realistic and correct than the previous hardcoded value.

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