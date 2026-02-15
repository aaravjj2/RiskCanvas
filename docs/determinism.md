# Determinism and Numeric Stability

## Overview

RiskCanvas engine is designed for **deterministic** calculations - identical inputs always produce identical outputs, down to the byte level.

## Numeric Precision

- All numeric outputs are rounded to **8 decimal places** by default
- Configured via `NUMERIC_PRECISION` in `config.py`
- Tolerance for numeric comparisons: `1e-10`

## Rounding Policy

All public API functions (pricing, Greeks, VaR, etc.) apply `round_to_precision()` to their outputs to ensure:
- Consistent behavior across platforms
- Reproducible results for testing
- Deterministic output hashes

## Determinism Guarantees

### What is Deterministic

- **Option pricing**: Same Black-Scholes parameters → same price
- **Greeks**: Same inputs → same Greeks
- **Portfolio calculations**: Same positions → same aggregates
- **VaR**: Same parameters/historical data → same VaR
- **Scenario analysis**: Same positions and shocks → same results

### What is NOT Included (by design)

- **Timestamps**: Calculations do not include `datetime.now()` in outputs
- **Random seeds**: No randomness in core calculations
- **Network calls**: No external data fetching in engine

## Testing Determinism

Run the determinism test suite:

```bash
cd packages/engine
python tests/test_determinism.py
```

Tests verify:
1. Repeated calculations produce identical results
2. Output JSON hashes match across runs
3. Fixture-based calculations are reproducible

## Numeric Stability

### Edge Cases Handled

1. **Zero volatility** (`sigma = 0`): Returns intrinsic value
2. **Zero time** (`T = 0`): Returns payoff at expiration
3. **Division by zero**: Protected with guards
4. **Very small numbers**: Rounded to configured precision

### Tolerance

Comparisons use `NUMERIC_TOLERANCE = 1e-10` to handle floating-point arithmetic limitations.

## Example

```python
from engine import price_option, calculate_greeks
import json
import hashlib

# Run calculation twice
params = {"S": 100, "K": 105, "T": 0.25, "r": 0.05, "sigma": 0.2}

result1 = price_option(**params, option_type="call")
result2 = price_option(**params, option_type="call")

assert result1 == result2  # Always True

# Hash consistency
def hash_output(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()

hash1 = hash_output(calculate_greeks(**params))
hash2 = hash_output(calculate_greeks(**params))

assert hash1 == hash2  # Always True
```

## Production Considerations

- **Timestamps**: Add separately in API layer if needed (not in engine)
- **Audit trails**: Log inputs and output hashes for reproducibility
- **Version tracking**: Engine version included in API responses
