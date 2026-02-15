# Persistence Architecture (v1.1+)

## Overview

RiskCanvas v1.1 introduces deterministic persistence for portfolios and analysis runs. All stored data uses content-based IDs (hashes) to ensure reproducibility and enable efficient deduplication.

## Database

**Storage**: SQLite (default) with SQLModel ORM
- **Production**: File-based at `apps/api/data/riskcanvas.db`
- **Tests**: In-memory (`sqlite:///:memory:`) when running under pytest
- **Configurable**: Set `DATABASE_URL` environment variable to override

## Database Schema

### portfolios table

| Column | Type | Description |
|--------|------|-------------|
| `portfolio_id` | TEXT PRIMARY KEY | Deterministic hash of canonical portfolio JSON (32 chars) |
| `name` | TEXT | User-friendly name |
| `tags` | TEXT | JSON array of tags (as string) |
| `canonical_data` | TEXT | Canonical JSON representation of portfolio |
| `created_at` | TEXT | ISO 8601 timestamp |
| `updated_at` | TEXT | ISO 8601 timestamp |

### runs table

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT PRIMARY KEY | Deterministic hash (32 chars) |
| `portfolio_id` | TEXT FOREIGN KEY | References `portfolios.portfolio_id` |
| `run_params` | TEXT | Canonical JSON of analysis parameters |
| `engine_version` | TEXT | Engine version (e.g., "0.1.0") |
| `pricing_output` | TEXT | JSON of pricing results |
| `greeks_output` | TEXT | JSON of Greeks results |
| `var_output` | TEXT | JSON of VaR results |
| `scenarios_output` | TEXT | JSON of scenario results |
| `output_hash` | TEXT | SHA256 hash of all outputs (64 chars) |
| `report_bundle_id` | TEXT | Associated report bundle ID (nullable) |
| `created_at` | TEXT | ISO 8601 timestamp |

## Deterministic ID Generation

### portfolio_id

```
portfolio_id = SHA256(canonical_json(portfolio))[:32]
```

**Canonical JSON rules**:
- Sorted keys (recursive)
- No whitespace (separators: `,` and `:`)
- ASCII encoding
- Consistent defaults for missing fields

**Example**:
```python
portfolio = {
    "id": "test-portfolio-1",
    "name": "Test Portfolio",
    "assets": [
        {"symbol": "AAPL", "type": "stock", "quantity": 10, "price": 150.0}
    ]
}
canonical = '{"assets":[{"price":150.0,"quantity":10,"symbol":"AAPL","type":"stock"}],"id":"test-portfolio-1","name":"Test Portfolio"}'
portfolio_id = "a1b2c3d4..."  # First 32 chars of SHA256
```

### run_id

```
run_id = SHA256(portfolio_id + ":" + canonical_json(params) + ":" + engine_version)[:32]
```

**Properties**:
- Same portfolio + params + engine version → same run_id
- Enables deduplication: running the same analysis twice stores only one run
- Hash includes engine version to invalidate cache on engine upgrades

### output_hash

```
output_hash = SHA256(canonical_json(all_outputs))
```

Used for determinism verification and change detection.

## API Endpoints

### Portfolio CRUD

**List portfolios**
```http
GET /portfolios
Response: [ { portfolio_id, name, tags, created_at, updated_at, portfolio } ]
```

**Create/update portfolio**
```http
POST /portfolios
Body: { portfolio, name?, tags? }
Response: { portfolio_id, name, tags, created_at, updated_at, portfolio }
```
- If portfolio with same content exists, updates metadata (name/tags) and bumps `updated_at`
- Otherwise creates new portfolio

**Get portfolio**
```http
GET /portfolios/{portfolio_id}
Response: { portfolio_id, name, tags, created_at, updated_at, portfolio }
```

**Delete portfolio**
```http
DELETE /portfolios/{portfolio_id}
Response: { deleted: true, portfolio_id }
```
- Cascades: deletes all associated runs

### Run Execution & History

**Execute analysis run**
```http
POST /runs/execute
Body: { portfolio_id?, portfolio?, params? }
Response: { run_id, portfolio_id, output_hash, outputs, created_at }
```
- Accepts either `portfolio_id` (existing) or `portfolio` (creates on-the-fly)
- Computes deterministic `run_id`
- If run already exists (same run_id), returns existing run
- Otherwise creates new run

**List runs**
```http
GET /runs?portfolio_id={id}
Response: [ { run_id, portfolio_id, engine_version, var_95, var_99, portfolio_value, output_hash, report_bundle_id, created_at } ]
```
- Optional `portfolio_id` query parameter to filter

**Get run details**
```http
GET /runs/{run_id}
Response: { run_id, portfolio_id, engine_version, run_params, outputs, output_hash, report_bundle_id, created_at }
```
- Full outputs (pricing, greeks, var, scenarios)

**Compare runs**
```http
POST /runs/compare
Body: { run_id_a, run_id_b }
Response: { run_id_a, run_id_b, deltas, top_changes }
```
- Computes deltas for all metrics
- Returns top 5 changes sorted by magnitude

## Determinism Guarantees

1. **Same portfolio → same portfolio_id** (byte-for-byte)
2. **Same inputs → same run_id** (reproducible across machines/time)
3. **Same inputs → same outputs** (engine determinism)
4. **Same outputs → same output_hash** (verification)

## Reset Instructions

**Local development**:
```bash
rm apps/api/data/riskcanvas.db
# Database will be recreated on next request
```

**Tests**:
```python
# Automatically uses in-memory DB (see database.py)
# Each test gets fresh DB via reset_database fixture
```

## Known Limitations

- **No migrations**: Schema changes require manual DB recreation
- **No transactions**: Multi-step operations not atomic (acceptable for single-user demo)
- **No indexes**: Small dataset, full table scans acceptable
- **SQLite only**: PostgreSQL/MySQL support requires adapter layer
- **No soft deletes**: DELETE is permanent
