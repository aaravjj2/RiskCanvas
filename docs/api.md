# RiskCanvas API Reference

**Version**: 1.0.0  
**Base URL**: `http://localhost:8090`

---

## Health & Info

### GET /health

Returns service health status.

**Response** `200 OK`
```json
{
  "status": "healthy",
  "engine_version": "0.1.0",
  "api_version": "1.0.0",
  "demo_mode": true
}
```

### GET /version

Returns version info.

**Response** `200 OK`
```json
{
  "api_version": "1.0.0",
  "engine_version": "0.1.0"
}
```

---

## Pricing

### POST /price/option

Price a European option using Black-Scholes.

**Request Body**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| S | float | yes | Current stock price |
| K | float | yes | Strike price |
| T | float | yes | Time to maturity (years) |
| r | float | yes | Risk-free rate |
| sigma | float | yes | Volatility |
| option_type | string | no | `"call"` (default) or `"put"` |

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "price": 3.12345678,
  "greeks": {
    "delta": 0.45,
    "gamma": 0.02,
    "vega": 0.15,
    "theta": -0.04,
    "rho": 0.08
  }
}
```

---

## Portfolio Analysis

### POST /analyze/portfolio

Analyze a portfolio of assets.

**Request Body**
```json
{
  "portfolio": {
    "assets": [
      {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0}
    ]
  }
}
```

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "total_value": 1500.0,
  "total_pnl": 0.0,
  "asset_count": 1,
  "metrics": { "delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0 }
}
```

---

## Risk

### POST /risk/var

Calculate Value at Risk.

**Request Body**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| portfolio_value | float | yes | Current portfolio value |
| volatility | float | yes | Annual volatility |
| confidence_level | float | no | Default 0.95 |
| time_horizon_days | int | no | Default 1 |
| method | string | no | `"parametric"` (default) or `"historical"` |
| historical_returns | float[] | no | Required if method=historical |

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "var_value": 15534.12,
  "confidence_level": 0.95,
  "time_horizon_days": 1,
  "method": "parametric"
}
```

---

## Scenarios

### POST /scenario/run

Run stress scenarios against positions.

**Request Body**
```json
{
  "positions": [
    {"type": "stock", "quantity": 10, "current_price": 100, "symbol": "AAPL"}
  ],
  "scenarios": [
    {"name": "Market Crash", "shock_type": "price", "parameters": {"price_change_pct": -20}}
  ]
}
```

**Shock types**: `price`, `volatility`, `rate`, `combined`

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "results": [
    {
      "name": "Market Crash",
      "shock_type": "price",
      "base_value": 1000.0,
      "scenario_value": 800.0,
      "change": -200.0,
      "change_pct": -20.0
    }
  ]
}
```

---

## Reports

### POST /report/generate

Generate an HTML risk report.

**Request Body**
```json
{
  "portfolio": {
    "assets": [{"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150}]
  },
  "include_greeks": true,
  "include_var": true,
  "include_scenarios": true
}
```

**Response** `200 OK` — returns `{ "request_id": "...", "html": "..." }`

---

## Agent

### POST /agent/execute

Execute an agentic workflow.

**Request Body**
```json
{
  "goal": "Analyze portfolio risk",
  "portfolio": {
    "assets": [{"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150}]
  }
}
```

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "plan": ["step1", "step2"],
  "result": "...",
  "html": "...",
  "audit_log": ["..."]
}
```

---

## Determinism

### POST /determinism/check

Run determinism verification across all key computations.

**Response** `200 OK`
```json
{
  "request_id": "uuid",
  "passed": true,
  "checks": [
    {"name": "option_pricing", "value": 3.12, "hash": "sha256...", "match": true}
  ],
  "overall_hash": "sha256..."
}
```

---

## Legacy Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Root greeting |
| GET | /portfolio/report | Portfolio report from fixture |
| GET | /export | Export portfolio as JSON |
| GET | /portfolio/aggregation/sector | Sector aggregation |
| GET | /portfolio/aggregation/summary | Portfolio summary |

---

## Error Responses

All errors follow this structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description of the error",
    "request_id": "uuid"
  }
}
```

Error codes: `VALIDATION_ERROR`, `COMPUTATION_ERROR`, `NOT_FOUND`, `TIMEOUT`, `INTERNAL`, `AUTH_ERROR`, `RATE_LIMIT`
