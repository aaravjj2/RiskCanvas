# Wave 13–18 Submission
## RiskCanvas v4.25.0 — Mega Delivery

**Version range**: v4.6.0 → v4.25.0  
**Waves**: 13, 14, 15, 16, 17, 18  
**Date**: 2025-07-22  

---

## Hard Gate Checklist

- [x] `pytest` backend: **630 passed, 0 failed, 0 skipped**
- [x] `tsc --noEmit`: **0 TypeScript errors**
- [x] `npm run build`: **✓ Vite 7.3.1 clean build**
- [x] `playwright test` (uiunit+main): **28 passed, 0 failed, retries=0, workers=1**
- [x] All `data-testid` selectors only in E2E
- [x] Port 8090 for API everywhere
- [x] No external network calls in tests
- [x] Deterministic outputs (same input → same SHA256)

---

## Wave 15: PnL Attribution (v4.10.0–v4.13.0)

### Backend: `apps/api/pnl_attribution.py`
Deterministic PnL factor attribution engine. Decomposes portfolio P&L into 5 buckets: `spot`, `vol`, `rates`, `spread`, `residual`. Each run produces a SHA256-chained `attribution_hash`.

**Endpoints**:
- `POST /pnl/attribution` — compute attribution for two run IDs
- `GET /pnl/drivers/presets` — list available driver presets
- `POST /exports/pnl-attribution-pack` — export attribution as ZIP pack with MD + JSON

### Frontend: `PnLAttributionPage.tsx` → `/pnl`
Compute button triggers attribution, displays contributions table with factor rows. Export MD preview and pack download.

---

## Wave 16: Scenario DSL (v4.14.0–v4.17.0)

### Backend: `apps/api/scenario_dsl.py`
Typed-JSON scenario DSL with validator (required fields: `name`, `type`, `shocks`, `metadata`). Deterministic `scenario_id = sha256(canonical_json)[:32]`. In-memory storage with diff engine.

**Endpoints**:
- `POST /scenarios/validate` — validate DSL, return error list
- `POST /scenarios/create` — store scenario, return deterministic ID
- `GET /scenarios/list` — list all stored scenarios
- `GET /scenarios/{id}` — fetch single scenario
- `POST /scenarios/diff` — diff two scenarios field-by-field
- `POST /exports/scenario-pack` — export pack

### Frontend: `ScenariosDSLPage.tsx` → `/scenarios-dsl`
4-tab layout: Author (JSON editor + validate + save), List, Diff, Pack Export.

---

## Wave 17: Replay Store (v4.18.0–v4.21.0)

### Backend: `apps/api/replay_store.py`
Deterministic replay store with SHA256 tamper detection. Stores `(endpoint, request, response)` tuples. Verifies response hash on replay. 3 built-in golden suites covering market/attribution/portfolio endpoints.

**Endpoints**:
- `POST /replay/store` — store a replay entry
- `POST /replay/verify` — verify entry hash (tamper detection)
- `GET /replay/suites/list` — list golden suites
- `POST /replay/run-suite` — run suite, return scorecard
- `POST /exports/repro-report-pack` — export repro report

### Frontend: `ReplayPage.tsx` → `/replay`
3-tab layout: Golden Suites (load → run → scorecard → export), Store & Verify (demo store + ID auto-fill + verify), Repro Report.

---

## Wave 18: Construction Studio (v4.22.0–v4.25.0)

### Backend: `apps/api/construction_engine.py`
Deterministic constraint-based portfolio construction solver. Accepts current weights + constraints (max_position, sector_max, etc.) + objective. Returns target weights (sum=1.0), trade list, before/after metrics, cost estimate.

**Endpoints**:
- `POST /construct/solve` — solve construction problem
- `POST /construct/compare` — compare before/after metrics
- `POST /exports/construction-decision-pack` — decision memo + JSON pack

### Frontend: `ConstructionStudioPage.tsx` → `/construction`
3-tab layout: Solve (weights input + solve + trade rows + export), Compare (before/after metrics table), Memo (narrative MD).

---

## Architecture Notes

- All engines: in-memory stores (DEMO_MODE), no database
- Determinism: SHA256-based IDs and hashes for all stored artifacts
- CORS: enabled for `http://localhost:4174` (frontend)
- Port: 8090 (API), 4174 (Vite preview)
- TypeScript: strict mode, no `any` errors
