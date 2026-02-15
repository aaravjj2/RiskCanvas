# Hedge Studio (v1.3+)

## Overview

RiskCanvas v1.3 introduces the Hedge Studio: a deterministic hedge suggestion engine that recommends strategies to reduce portfolio VaR with minimal cost.

## Core Concept

**Problem**: "How do I reduce my portfolio VaR by X% with minimal cost?"

**Solution**: Generate ranked hedge candidates via grid search over:
1. **Protective puts** — Buy out-of-the-money puts on underlying stocks
2. **Exposure reduction** — Sell portion of high-risk positions
3. *(Future)* Collars, spreads, futures, etc.

## Determinism Guarantees

### No Randomness
- **Grid search** over fixed candidate set (not Monte Carlo)
- **Enumerated strikes**: [95%, 90%, 85%] of current price
- **Fixed expiries**: 3 months (0.25 years)
- **Sorted output**: By cost-effectiveness, then by cost

### Stable IDs
- Hedge candidates have no ID (stateless suggestions)
- Evaluation results include all inputs for reproducibility

## API Endpoints

### Suggest Hedges

```http
POST /hedge/suggest
Body: {
  portfolio_id?: string,
  portfolio?: object,
  target_reduction_pct: number,  // e.g., 20.0 for 20% VaR reduction
  max_cost?: number,
  allowed_instruments?: string[]
}
Response: {
  portfolio_id,
  target_reduction_pct,
  max_cost,
  candidates: [ ...hedgeCandidate ],
  total_candidates
}
```

**Candidate Fields**:
```json
{
  "strategy": "protective_put" | "reduce_exposure",
  "description": "Buy 95% OTM put on AAPL",
  "instrument": {
    "type": "option",
    "option_type": "put",
    "underlying": "AAPL",
    "strike": 142.5,
    "quantity": 0.1,
    "expiry_months": 3
  },
  "cost": 250.50,
  "current_var": -50000.00,
  "estimated_new_var": -40000.00,
  "var_reduction": 10000.00,
  "var_reduction_pct": 20.0,
  "cost_effectiveness": 39.92,
  "hedged_positions": [ ...assets ]
}
```

**Parameters**:
- `target_reduction_pct` — Minimum VaR reduction required (filters candidates)
- `max_cost` — Maximum allowable hedge cost (optional)
- `allowed_instruments` — `["protective_put", "reduce_exposure"]` (default: both)

**Returns**: Top 10 candidates sorted by cost-effectiveness

### Evaluate Hedge

```http
POST /hedge/evaluate
Body: {
  portfolio: object,
  hedge_candidate: object
}
Response: {
  original: { var_95, portfolio_value },
  hedged: { var_95, portfolio_value },
  improvement: { var_reduction, var_reduction_pct },
  scenarios: [
    { shock_pct, original_value, hedged_value, protection }
  ],
  cost
}
```

**Scenario Analysis**:
- Tests hedge under price shocks: -20%, -10%, 0%, +10%
- Computes "protection" = hedged_value - original_value
- For protective puts, adds intrinsic value when ITM

## Hedge Strategies

### 1. Protective Puts

**Mechanism**: Buy OTM put options on underlying stocks to limit downside.

**Candidates Generated**:
- For each stock position:
  - 95% OTM (5% below current price)
  - 90% OTM (10% below current price)
  - 85% OTM (15% below current price)
- Expiry: 3 months
- Volatility: 25% (fixed for determinism)
- Risk-free rate: 5% (fixed)

**Cost Calculation**:
```python
put_price = black_scholes(S, K, T=0.25, r=0.05, sigma=0.25, type="put")
cost = put_price * quantity * 100  # Options per 100 shares
```

**VaR Impact**:
- Adds put position to portfolio
- Recalculates VaR with hedged portfolio
- Captures reduced downside tail risk

### 2. Exposure Reduction

**Mechanism**: Sell portion of high-risk positions.

**Candidates Generated**:
- For each stock position:
  - Reduce by 25%
  - Reduce by 50%
- No transaction cost assumed (simplification)

**VaR Impact**:
- Reduces position size in portfolio
- Recalculates VaR with smaller exposure
- Linear reduction not accurate for non-linear risk (options), but good approximation for stocks

## Scoring & Ranking

**Cost-Effectiveness Score**:
```
cost_effectiveness = var_reduction / max(cost, 1)
```

**Sort Order**:
1. Cost-effectiveness (descending) — maximize VaR reduction per dollar
2. Cost (ascending) — prefer cheaper hedges when effectiveness is equal

**Filtering**:
- Exclude candidates that don't meet `target_reduction_pct`
- Exclude candidates above `max_cost`

## Use Cases

### Risk Manager
- Portfolio VaR exceeds limit
- Generate hedges to bring VaR below threshold
- Compare cost of different strategies
- Apply hedge → create new portfolio → compare runs

### Portfolio Construction
- Analyst builds aggressive portfolio
- Studio suggests protective hedges
- Evaluate trade-off: potential return vs. hedge cost

### What-If Analysis
- "What if I buy 10% OTM puts on all tech stocks?"
- Evaluate specific hedge via `/hedge/evaluate`
- See scenario-by-scenario protection

## Implementation Details

### VaR Calculation

Uses parametric VaR (same as portfolio analysis):
```python
var = var_parametric(
    portfolio_value=total_value,
    volatility=0.15,
    confidence_level=0.95,
    time_horizon_days=1
)
```

**Simplification**: Portfolio volatility fixed at 15%
- **Future**: Use historical returns or covariance matrix for accurate portfolio vol

### Option Pricing

Black-Scholes with fixed parameters:
- `r = 0.05` (risk-free rate)
- `sigma = 0.25` (implied volatility)
- `T = 0.25` (3 months to expiry)

**Simplification**: Same IV for all underlyings
- **Future**: Fetch live IV from options chain API

### Greeks Impact

Hedge suggestions **do not yet** account for Greeks (delta, gamma, vega) changes.
- **Future**: Add delta-neutral hedging, gamma scalping strategies

## Agent Integration

**HedgeAgent** (planned):
- Accepts natural language goal: "Reduce my VaR by 20% for less than $5,000"
- Calls `/hedge/suggest` with parsed parameters
- Generates structured plan with ranked hedges
- Returns explanation referencing computed fields only (no invented numbers)
- Audit log includes all hashes for determinism verification

## Frontend Integration

**Hedge Studio Page** (planned):
- **Inputs**:
  - Target reduction slider (0-100%)
  - Max cost input field
  - Expiry selector (1m, 3m, 6m, 1y)
  - Instrument checkboxes (puts, collars, reduce exposure)
- **Outputs**:
  - Ranked hedge cards with cost, VaR reduction, effectiveness score
  - Before/After VaR comparison chart
  - Scenario table (price shocks vs. protection)
- **Actions**:
  - "Apply Hedge" → creates new portfolio with hedge applied
  - "Save Scenario" → stores hedged portfolio for comparison

## Known Limitations

- **Simplistic VaR**: Fixed 15% volatility for all portfolios (should use historical data)
- **Fixed IV**: 25% volatility for all options (should query live IV)
- **No Greeks optimization**: Doesn't target delta-neutral or gamma-neutral portfolios
- **No transaction costs**: Ignores commissions, slippage, bid-ask spreads
- **No dynamic hedging**: Doesn't model hedge rebalancing over time
- **Limited instruments**: Only puts and position reduction (no futures, swaps, etc.)

## Future Enhancements

1. **Delta-neutral hedging** — Match delta exposure exactly
2. **Tail-risk hedging** — Far OTM puts for black swan protection
3. **Collar strategies** — Buy put + sell call to finance hedge
4. **Futures hedging** — Use futures for cheapest VaR reduction
5. **Multi-leg strategies** — Spreads, straddles, butterflies
6. **Live market data** — Fetch real option prices and IVs
7. **hedge rebalancing** — Model dynamic hedge adjustments over time
8. **Machine learning** — Train model to predict best hedge for portfolio characteristics
