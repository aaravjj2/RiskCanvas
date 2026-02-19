# Wave 13–18 Proof Pack Manifest
## v4.6.0 → v4.25.0 (20 versions, 16 commits in session)

**Generated**: 2025-07-22  
**Delivery**: Waves 13–18 mega integration  

## Test Gates — All Green

| Gate | Result |
|------|--------|
| `pytest` backend | **630 passed, 0 failed, 0 skipped** |
| `tsc --noEmit` | **0 errors** |
| `npm run build` | **✓ Vite 7.3.1 built in 2.52s** |
| E2E Playwright (28 tests) | **28 passed, 0 failed, 0 skipped, retries=0, workers=1** |

## Version Tags

| Tag | Description |
|-----|-------------|
| v4.6.0 | Market Data Provider Abstraction (Wave 13) |
| v4.7.0 | Cache v2 Layered + Provenance-Safe |
| v4.8.0 | Hedge Studio Pro (constraints, templates) |
| v4.9.0 | Decision Memo Export |
| v4.10.0 | PnL Attribution engine (factor bucketing) |
| v4.11.0 | PnL Attribution test suite (10 tests) |
| v4.12.0 | PnL Attribution frontend page |
| v4.13.0 | PnL E2E specs + judge demo w15 |
| v4.14.0 | Scenario DSL backend (validator, storage, diff) |
| v4.15.0 | Scenario DSL test suite (19 tests) |
| v4.16.0 | Scenario DSL frontend (author/list/diff/pack) |
| v4.17.0 | Scenario DSL E2E specs + judge demo w16 |
| v4.18.0 | Replay Store backend (tamper detection, golden suites) |
| v4.19.0 | Replay Store test suite (17 tests) |
| v4.20.0 | Replay frontend (suites/store+verify/repro) |
| v4.21.0 | Replay E2E specs + judge demo w17 |
| v4.22.0 | Construction Engine backend (constraint solver) |
| v4.23.0 | Construction Engine test suite (17 tests) |
| v4.24.0 | Construction Studio frontend (solve/compare/memo) |
| v4.25.0 | Mega delivery — all routes wired, AppLayout v4.25.0, 40-screenshot demo |

## New Backend Modules

| File | Endpoints | Tests |
|------|-----------|-------|
| `apps/api/pnl_attribution.py` | POST /pnl/attribution, GET /pnl/drivers/presets, POST /exports/pnl-attribution-pack | 10 |
| `apps/api/scenario_dsl.py` | POST /scenarios/validate, /create, GET /list, /{id}, POST /diff, POST /exports/scenario-pack | 19 |
| `apps/api/replay_store.py` | POST /replay/store, /verify, GET /suites/list, POST /run-suite, POST /exports/repro-report-pack | 17 |
| `apps/api/construction_engine.py` | POST /construct/solve, /compare, POST /exports/construction-decision-pack | 17 |

## New Frontend Pages

| File | Route | data-testids |
|------|-------|-------------|
| `PnLAttributionPage.tsx` | /pnl | pnl-page, pnl-compute-btn, pnl-ready, pnl-row-{factor}, pnl-export-md, pnl-export-pack |
| `ScenariosDSLPage.tsx` | /scenarios-dsl | scenario-page, scenario-tab-{t}, scenario-validate-btn, scenario-save-btn, scenario-list-ready |
| `ReplayPage.tsx` | /replay | replay-page, replay-tab-{t}, replay-load-suites-btn, replay-suites-ready, replay-scorecard-ready |
| `ConstructionStudioPage.tsx` | /construction | construct-page, construct-tab-{t}, construct-solve-btn, construct-ready, construct-results |

## E2E Specs

- `e2e/test-pnl.spec.ts` — 5 tests
- `e2e/test-scenario-dsl.spec.ts` — 4 tests
- `e2e/test-replay.spec.ts` — 4 tests
- `e2e/test-construction.spec.ts` — 5 tests
- `e2e/phase15-judge-demo.spec.ts` — 25 screenshots
- `e2e/phase16-judge-demo.spec.ts` — 25 screenshots
- `e2e/phase17-judge-demo.spec.ts` — 25 screenshots
- `e2e/phase18-mega-judge-demo.spec.ts` — 40 screenshots

## Determinism Properties

All engines produce identical output for same input:
- SHA256 hash comparisons in backend tests
- `_input_hash()` + `_chain_head()` for PnL
- `scenario_id = sha256(canonical_json)[:32]`
- `replay_id = sha256(canonical_request)[:32]`
- Construction solver uses sorted symbols, deterministic LP fallback
