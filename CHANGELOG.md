# Changelog

All notable changes to RiskCanvas are documented in this file.

## [5.21.0] – 2026-02-19 — Wave 41-48 Enterprise Layer

### Added (Wave 47 — Judge Mode v2, v5.18.0-v5.21.0)

- **`apps/api/judge_mode_v2.py`** — `generate_judge_pack_v2()`, `list_judge_packs_v2()`, `get_pack_definitions()`; 3 vendor packs: microsoft, gitlab, digitalocean; deterministic `generation_id`; `GET /judge/v2/packs`, `POST /judge/v2/generate`, `GET /judge/v2/definitions`

### Added (Wave 44 — Compliance Pack, v5.10.0-v5.13.0)

- **`apps/api/compliance_pack.py`** — `generate_compliance_pack()` produces 7-file SOC2-ish evidence bundle; `verify_compliance_pack()` validates manifest hashes; `POST /compliance/generate-pack`, `GET /compliance/packs/{id}`, `POST /compliance/packs/{id}/verify`
- **`apps/web/src/pages/CompliancePage.tsx`** — Pack generator UI with verify action; testids: `compliance-page`, `compliance-generate-btn`, `compliance-pack-row-{i}`

### Added (Wave 43 — Attestations, v5.06.0-v5.09.0)

- **`apps/api/attestations.py`** — `issue_attestation()`, `get_chain_head()`, `build_receipts_pack()`; per-tenant hash chain; `GET /attestations`, `POST /attestations/receipts-pack`
- **`apps/web/src/pages/AttestationsPage.tsx`** — Timeline with hash chain navigation; testids: `attestations-page`, `attestation-row-{i}`, `attestation-drawer-ready`
- **`apps/web/src/components/ui/PermissionBadge.tsx`** — Role permission chip + `PermExplainDrawer`; testids: `perm-badge-{action}`, `perm-explain-drawer`

### Added (Wave 42 — Artifact Registry, v5.02.0-v5.05.0)

- **`apps/api/artifacts_registry.py`** — 5 demo artifacts with deterministic SHA-256; `list_artifacts()`, `get_artifact()`, `get_download_descriptor()`; `GET /artifacts`, `GET /artifacts/{id}/downloads`
- **`apps/web/src/pages/ArtifactsPage.tsx`** — Artifact browser with verify; testids: `artifacts-page`, `artifact-row-{i}`, `artifact-drawer-ready`
- **`apps/web/src/components/ui/EvidenceBadge.tsx`** — SHA-256 hash display + copy; testids: `evidence-badge`, `evidence-hash`, `evidence-verified`

### Added (Wave 41 — Tenancy v2 / RBAC, v4.98.0-v5.01.0)

- **`apps/api/tenancy_v2.py`** — 3 demo tenants, 4 demo users, `has_permission()`, `require_perm()`; `GET /tenants`, `GET /tenants/{id}/members`, `POST /tenants/{id}/members`, `GET /tenants/~context`
- **`apps/web/src/pages/AdminPage.tsx`** — Tenant/member management + audit log tabs; testids: `admin-page`, `tenant-row-{i}`, `member-row-{i}`, `invite-btn`
- **`apps/web/src/components/ui/TenantSwitcher.tsx`** — Sidebar tenant dropdown; testids: `tenant-switcher`, `tenant-current`, `tenant-option-{id}`

### Changed

- **`apps/api/main.py`** — Registered 5 new routers (tenancy_v2, artifacts_registry, attestations, compliance_pack, judge_mode_v2)
- **`apps/web/src/App.tsx`** — Added routes `/admin`, `/artifacts`, `/attestations`, `/compliance`
- **`apps/web/src/components/layout/AppLayout.tsx`** — 4 new nav items, TenantSwitcher in brand, version badge v5.21.0
- **`apps/web/src/lib/api.ts`** — 15 new API helper functions for Wave 41-48
- **`apps/api/judge_mode_v2.py`** — `get_pack_definitions()` public helper

### Tests

- **`apps/api/tests/test_wave41_48.py`** — 72 new tests (17+4+8+4+9+4+7+4+9+4); suite total: 1087 passed
- **`conftest.py`** — Root conftest adds apps/api to sys.path
- **`pytest.ini`** — Root pytest.ini with `asyncio_mode = auto`

### Docs

- **`docs/TESTIDS.md`** — 30 new Wave 41-48 testids documented
- **`.gitignore`** — `artifacts/` dir now gitignored (fixes test_report_files_not_committed)

---

## [4.9.0] – 2026-01-15

### Added (v4.9 – Decision Memo Export)

- **`apps/api/decision_memo.py`** — `DecisionMemoBuilder` that generates Markdown + JSON memos from hedge results; `_now_iso()` returns deterministic timestamp in DEMO_MODE; `decision_memo_router` at `POST /hedge/v2/memo`; `exports_router` at `POST /exports/hedge-decision-pack`
- **`apps/api/tests/test_decision_memo.py`** — 20 tests (memo build, hash determinism, DEMO asof, export pack endpoint)
- **Frontend**: `HedgeStudio.tsx` — Build Memo button, Decision Pack export buttons (`hedge-build-memo-btn`, `hedge-memo-ready`, `hedge-memo-export-md`, `hedge-memo-export-pack`)
- **`apps/web/src/lib/api.ts`** — `buildDecisionMemo()`, `exportHedgeDecisionPack()` functions
- **`e2e/test-hedge-v2.spec.ts`** — hv2-7 (build memo), hv2-8 (export pack), hv2-9 (v1 still works)
- `API_VERSION` updated to `"4.9.0"`

---

## [4.8.0] – 2026-01-15

### Added (v4.8 – Hedge Studio Pro)

- **`apps/api/hedge_engine_v2.py`** — `HEDGE_TEMPLATES` dict (4 strategies: protective_put, collar, delta_hedge, duration_hedge); `generate_hedge_v2_candidates()` returning up to 10 scored candidates; `compare_hedge_runs()` producing deltas + pct_changes; `hedge_v2_router` at `POST /hedge/v2/suggest`, `POST /hedge/v2/compare`, `GET /hedge/v2/templates`
- **`apps/api/tests/test_hedge_v2.py`** — 24 tests
- **Frontend**: `HedgeStudio.tsx` — v2 Pro section with template selection, constraint inputs, optimizer and compare workflow; all v1 data-testids preserved
- **`apps/web/src/lib/api.ts`** — `getHedgeTemplates()`, `suggestHedgesV2()`, `compareHedgeV2()` functions
- **`e2e/test-hedge-v2.spec.ts`** — 9 tests covering pro mode init, template cards, constraints, suggest, compare, delta display

---

## [4.7.0] – 2026-01-15

### Added (v4.7 – Cache v2 Layered)

- **`apps/api/cache_v2.py`** — `CacheV2` with per-layer `OrderedDict` LRU eviction; `LAYER_MAX_SIZE = 128`; `make_cache_key()` for provenance-safe 32-char hex keys; `cache_v2_router` at `GET /cache/v2/stats`, `POST /cache/v2/clear` (DEMO only), `GET /cache/v2/keys`; `get_cache_v2()` singleton and `reset_cache_v2()` for test isolation
- **`apps/api/tests/test_cache_v2.py`** — 22 tests
- **`apps/web/src/lib/api.ts`** — `getCacheV2Stats()`, `clearCacheV2()`, `getCacheV2Keys()` functions

---

## [4.6.0] – 2026-01-15

### Added (v4.6 – Market Data Provider Abstraction)

- **`apps/api/market_data.py`** — `MarketDataProvider` ABC; `FixtureMarketDataProvider` loading from `fixtures/market/`; `get_market_data_provider()` factory; `market_router` at `GET /market/asof`, `GET /market/spot`, `POST /market/series`, `GET /market/curves/{curve_id}`
- **`apps/api/fixtures/market/`** — 6 JSON fixture files: `asof.json`, `spot.json`, `series/AAPL.json`, `series/MSFT.json`, `series/SPY.json`, `curves/USD_SOFR.json`
- **`apps/api/tests/test_market_data.py`** — 19 tests
- **`apps/web/src/pages/MarketDataPage.tsx`** — Market Data page with spot lookup, series, and rates curve UI (`data-testid="market-page"`)
- **`apps/web/src/components/layout/AppLayout.tsx`** — `nav-market` nav item (BarChart2 icon); version badge `v4.9.0`
- **`apps/web/src/App.tsx`** — `/market` route pointing to `MarketDataPage`
- **`e2e/test-market.spec.ts`** — 7 tests covering market page render, as-of load, spot lookup, series, curve, nav, and determinism

### How to Run (Wave 13+14)

```powershell
# Backend pytest (578 tests)
cd apps/api; python -m pytest tests/ -q

# Build
cd apps/web; npm run build

# Start servers
$env:DEMO_MODE="true"; Start-Job { cd apps/api; python -m uvicorn main:app --port 8090 }
Start-Job { cd apps/web; npm run preview -- --port 4174 }

# Playwright uiunit harness (10/10)
cd e2e; npx playwright test --project uiunit

# Playwright Wave 13+14 specs
cd e2e; npx playwright test test-market.spec.ts test-hedge-v2.spec.ts --project=main
```

---

## [4.5.0] – 2026-02-18


### Changed (v4.5 – Frontend Testing Migration: Playwright-Only)

**Vitest removed** — all frontend unit-test confidence is now delivered by Playwright MCP headed tests.

#### Removed
- `apps/web/src/App.test.tsx` — Vitest test suite (10 tests; replicated by Playwright harness)
- `apps/web/src/setupTests.ts` — `@testing-library/jest-dom` setup file
- `apps/web/src/__mocks__/fileMock.ts` — jsdom SVG/image mock
- `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` from `devDependencies`
- `"test": "vitest run"` npm script
- `test:vitest` job from `.gitlab-ci.yml`
- `vitest/config` import and `test` block from `vite.config.ts`

#### Added
- **apps/web/src/pages/TestHarnessPage.tsx** — deterministic UI unit harness at route `/__harness`; all checks run synchronously on mount; shows `data-testid=harness-ready` (data-all-pass), `data-testid=harness-check-<slug>` rows with `data-pass`, `data-expected-hash`, `data-actual-hash`; 12 checks covering: demo headers, auth mode, auth headers, CommandPalette NAV_COMMANDS, API mock constants, EventClient lifecycle
- **e2e/test-ui-harness.spec.ts** — 10 Playwright MCP headed tests validating the harness page; no waitForTimeout, data-testid only, retries=0
- **e2e/playwright.config.ts** — added `projects` array: `uiunit` (harness spec, runs first) and `main` (all other specs, depends on uiunit)

#### Updated
- `apps/web/src/App.tsx` — added `<Route path="/__harness" element={<TestHarnessPage />} />`
- `apps/web/src/components/CommandPalette.tsx` — exported `NAV_COMMANDS` const so harness can import it
- `apps/web/vite.config.ts` — simplified: `vite` config (not `vitest/config`), removed test block and SVG mock aliases
- `apps/web/package.json` — pruned vitest and testing-library from devDependencies
- `.gitlab-ci.yml` — replaced `test:vitest` job with updated `test:playwright` comment

### How to Run

```powershell
# TypeScript typecheck
cd apps/web; npx tsc --noEmit

# Build + preview (required before E2E)
cd apps/web; npm run build
cd apps/web; npm run preview -- --port 4174 --host localhost

# Full Playwright suite (includes harness first, then all other specs)
cd e2e; npx playwright test --config playwright.config.ts

# Harness-only suite
cd e2e; npx playwright test --config playwright.config.ts --project uiunit

# Backend pytest (unchanged)
cd apps/api; python -m pytest tests/ -q
```

---

## [4.4.0] – 2026-02-21

### Added (v4.4 – Command Palette + Judge Demo + Stabilization)
- **apps/web/src/components/CommandPalette.tsx** — Ctrl+K quick-navigation panel; 8 NAV_COMMANDS; type-to-search routes to `/search?q=`; `data-testid`: `cmdk-open`, `cmdk-input`, `cmdk-item-{id}`
- **apps/web/src/components/layout/AppLayout.tsx** — CommandPalette rendered globally; version badge `v4.4.0`
- **e2e/phase12-judge-demo.spec.ts** — 27-screenshot full Wave 11+12 tour (≥25 required)
- **e2e/playwright.w11w12.judge.config.ts** — `slowMo: 4000`, `video: on`, `retries: 0`, `workers: 1`
- **apps/api/tests/test_repo_invariants.py** — 5 tests checking Wave 11+12 spec invariants (no waitForTimeout, no getByText/Role, no forbidden ports)

### Changed
- API version bumped to 4.4.0
- Frontend version badge updated to v4.4.0

---

## [4.3.0] – 2026-02-21

### Added (v4.3 – Global Search: local index)
- **apps/api/search_index_local.py** — `SearchIndexLocal` (15 DEMO_INDEX_DOCS, 7 types: run/report/audit/activity/policy/eval/sre_playbook); `tokenize()`, `score_doc()`; `SearchIndexElastic` stub; endpoints: `POST /search/query`, `POST /search/reindex`, `GET /search/status`
- **apps/web/src/pages/SearchPage.tsx** — global search input, type filter chips, grouped results; click navigates to `result.url`; `data-testid`: `search-page`, `search-input`, `search-chips`, `search-chip-{type}`, `search-results-ready`, `search-result-{idx}`, `search-empty`, `search-submit`, `search-reindex`
- **apps/web/src/lib/api.ts** — `searchQuery()`, `searchReindex()`, `searchStatus()`
- **apps/web/src/components/layout/AppLayout.tsx** — `nav-search` with Search icon
- **apps/web/src/App.tsx** — route `/search`
- **apps/api/tests/test_search_index.py** — 15 tests (status, query, reindex, direct local index)
- **e2e/test-search.spec.ts** — 8 Playwright E2E tests

### Changed
- `/test/reset` now resets + rebuilds search index

---

## [4.2.0] – 2026-02-21

### Added (v4.2 – Live Run View: SSE progress stream)
- **apps/api/live_run.py** — `RunStatusStore` (DEMO_STAGES: VALIDATE→PRICE→VAR→REPORT→DONE); `run_progress_generator()`, `activity_stream_generator()`, `presence_stream_generator()`; endpoints: `GET /events/run-progress`, `GET /events/activity`, `GET /events/presence`, `GET /runs/{run_id}/status`
- **apps/web/src/pages/RunHistory.tsx** — `LiveRunPanel` component: SSE connection, stage/pct display; `data-testid`: `run-live-ready`, `run-live-stage`, `run-live-pct`, `run-live-done`, `run-live-connect`
- **apps/api/tests/test_live_run.py** — 18 tests (run status, SSE run progress, SSE activity, SSE presence)

### Changed
- `/test/reset` now resets + seeds run status store

---

## [4.1.0] – 2026-02-21

### Added (v4.1 – Activity Stream + Presence)
- **apps/api/activity_stream.py** — `ActivityStore` (8 DEMO_SEED events, 6 event types); `emit_activity()`, `seed_demo_activity()`; endpoints: `GET /activity`, `POST /activity/reset`
- **apps/api/presence.py** — `PresenceStore` (4 DEMO_PRESENCE actors: alice/bob=online, carol=idle, dave=offline); `seed_demo_presence()`; endpoints: `GET /presence`, `POST /presence/update`
- **apps/web/src/pages/ActivityPage.tsx** — activity feed + type filters + SSE live connection + presence panel with status chips; `data-testid`: `activity-page`, `activity-feed-ready`, `activity-item-{idx}`, `presence-ready`, `presence-user-{idx}`, `activity-live-badge`, `activity-connect-live`, `activity-refresh`, `activity-reset`
- **apps/web/src/lib/api.ts** — `getActivity()`, `resetActivity()`, `getPresence()`, `updatePresence()`, `getRunStatus()`
- **apps/web/src/components/layout/AppLayout.tsx** — `nav-activity` with Radio icon
- **apps/web/src/App.tsx** — route `/activity`
- **apps/api/tests/test_activity_stream.py** — 15 tests (list, reset, determinism)
- **apps/api/tests/test_presence.py** — 13 tests (list, update, hash stability)
- **e2e/test-activity.spec.ts** — 8 Playwright E2E tests

### Changed
- `/test/reset` now seeds activity + presence stores
- Test count: 422 → 493 passing

---

## [4.0.0] – 2026-02-20


### Added (v4.0 – SRE Playbooks + Judge Demo + Proof/Submission Pack)
- **apps/api/sre_playbook.py** — `sre_router` (POST /sre/playbook/generate); deterministic triage→mitigate→follow-up playbooks; all facts cited by hash
- **apps/web/src/pages/SREPlaybooksPage.tsx** — incident parameter form + steps timeline + export MD; `data-testid`: `sre-page`, `sre-generate`, `sre-playbook-ready`, `sre-export-md`, `sre-steps-list`
- **apps/web/src/components/layout/AppLayout.tsx** — `nav-sre` with ShieldCheck icon; version badge `v4.0.0`
- **apps/api/tests/test_sre_playbook.py** — 12 tests (empty inputs, P0 escalation, hash stability, all 3 phases)
- **e2e/test-sre-playbooks.spec.ts** — 8 Playwright E2E tests
- **e2e/phase10-judge-demo.spec.ts** — 28-screenshot full Wave 9+10 tour (≥25 required)
- **e2e/playwright.w9w10.judge.config.ts** — `slowMo: 4000` judge config for ≥180s TOUR.webm

### Changed
- API version bumped to 4.0.0
- Frontend version badge updated to v4.0.0

---

## [3.9.0] – 2026-02-20

### Added (v3.9 – DevOps Pro: MR Review + Pipeline Analyzer + Artifacts)
- **apps/api/devops_pro.py** — `devops_pro_router` (POST /devops/mr/review-bundle, /devops/pipeline/analyze, /devops/artifacts/build); deterministic ZIP artifact packs with manifest hash
- **apps/web/src/pages/DevOpsPage.tsx** — 3 new tabs: MR Review, Pipeline Analyzer, Artifacts; `data-testid`: `devops-mr-generate`, `devops-mr-ready`, `devops-pipe-analyze`, `devops-pipe-ready`, `devops-artifacts-build`, `devops-artifacts-ready`, `devops-download-pack`
- **apps/api/tests/test_devops_pro.py** — 20 tests (clean diff, secret diff blocks, TODO warns, OOM detection, artifact pack determinism)
- **e2e/test-devops-pro.spec.ts** — 8 Playwright E2E tests

### Changed
- DevOps page headline updated to v3.9+

---

## [3.8.0] – 2026-02-20

### Added (v3.8 – Eval Harness v2 + Scorecard)
- **apps/api/eval_harness_v2.py** — `eval_router` (GET /governance/evals/suites, POST /governance/evals/run-suite, GET /governance/evals/results/{run_id}, /scorecard/{run_id}/md, /scorecard/{run_id}/json); 3 built-in suites (governance_policy_suite, rates_curve_suite, stress_library_suite); deterministic run_id (sha256[:32])
- **apps/web/src/pages/GovernancePage.tsx** — "Suites" tab with load + run + scorecard table + export MD; `data-testid`: `eval-suites-list`, `eval-run-btn-{suite_id}`, `eval-scorecard-ready`, `eval-export-md`
- **apps/api/tests/test_eval_harness_v2.py** — 16 tests (suite list, run_id determinism, scorecard hash stability)
- **apps/web/src/lib/api.ts** — `listEvalSuites`, `runEvalSuite`, `getEvalResult`, `getScorecardMd`

---

## [3.7.0] – 2026-02-20

### Added (v3.7 – PolicyEngine v2 + Narrative Validator)
- **apps/api/policy_engine.py** — `governance_v2_router` (POST /governance/policy/evaluate, /apply, /governance/narrative/validate); tool allowlists by mode; call budgets; secret/PII redaction; "no hallucinated numbers" narrative validator
- **apps/web/src/pages/GovernancePage.tsx** — "Policy v2" tab + "Narrative" tab; `data-testid`: `gov-policy-ready`, `gov-validate-btn`, `gov-validate-result`, `gov-narrative-badge`
- **apps/api/tests/test_policy_engine.py** — 25 tests (allow/block, budget exceeded, secret in prompt, narrative valid/invalid, redaction determinism)
- **apps/web/src/lib/api.ts** — `evaluatePolicy`, `applyPolicy`, `validateNarrative`
- **e2e/test-governance-policy.spec.ts** — 8 Playwright E2E tests

### Changed
- API version bumped to 3.7.0 (then to 4.0.0 as final)

---

## [3.6.0] – 2026-02-19

### Added (v3.6 – Phase 8 Judge Demo + Proof Pack)
- **e2e/phase8-judge-demo.spec.ts** — full Wave 7+8 tour, ≥25 screenshots, TOUR.webm ≥ 180s
- **e2e/playwright.w7w8.judge.config.ts** — `slowMo: 4000` judge config with 1920×1080 viewport
- **scripts/run_wave7_8.ps1** — full proof runner: engine → backend → vitest → tsc → vite build, manifest.json + MANIFEST.md in timestamped artifacts dir

### Changed
- API version bumped to 3.6.0
- Frontend version badge updated to v3.6.0

---

## [3.5.0] – 2026-02-19

### Added (v3.5 – Stress Library + Compare)
- **packages/engine/src/stress.py** — 5 canonical stress scenario presets (rates_up_200bp, rates_down_200bp, vol_up_25pct, equity_down_10pct, credit_spread_up_100bp) + `apply_preset()`
- **packages/engine/tests/test_stress.py** — 29 pytest tests (TestPresetDefinitions ×13, TestApplyPreset ×16)
- **apps/api/stress_library.py** — `stress_router` (GET /stress/presets, GET /stress/presets/{id}, POST /stress/apply) + `compare_router` (POST /compare/runs)
- **apps/api/tests/test_stress_compare.py** — 20 pytest tests (TestStressPresets, TestStressApply, TestCompareRuns)
- **apps/web/src/pages/StressPage.tsx** — stress preset cards, run-btn, results panel with delta table; nav via `nav-stress`
- **e2e/test-stress-compare.spec.ts** — 8 Playwright E2E tests

### Changed
- `packages/engine/src/__init__.py` — added stress exports
- `apps/api/main.py` — stress_router + compare_router registered

---

## [3.4.0] – 2026-02-19

### Added (v3.4 – Rates Curve Bootstrap)
- **packages/engine/src/rates.py** — deterministic rates curve bootstrap (deposits + swaps), `bond_price_from_curve()`
- **packages/engine/tests/test_rates.py** — 30 pytest tests (TestBootstrapDepositsOnly ×10, TestBootstrapWithSwaps ×5, TestBondPriceFromCurve ×5)
- **apps/api/rates_curve.py** — `rates_router` with GET /rates/fixtures/simple, POST /rates/curve/bootstrap, POST /rates/bond/price-curve
- **apps/api/fixtures/rates_curve_simple.json** + **apps/api/fixtures/bond_curve_case.json** — deterministic test fixtures
- **apps/api/tests/test_rates_curve.py** — 20 pytest tests
- **apps/web/src/pages/RatesPage.tsx** — instruments editor, Bootstrap Curve button, zero-rate table, bond price panel
- **e2e/test-rates.spec.ts** — 8 Playwright E2E tests

### Changed
- `packages/engine/src/__init__.py` — added rates exports
- `apps/api/main.py` — rates_router registered
- `apps/web/src/components/layout/AppLayout.tsx` — added `nav-rates` (TrendingUp icon)

---

## [3.3.0] – 2026-02-19

### Added (v3.3 – AuditV2 Hash Chain + Provenance)
- **apps/api/audit_v2.py** — immutable sha256 hash-chained audit log; `emit_audit_v2()`, `get_chain_head()`; endpoints GET /audit/v2/events, POST /audit/v2/reset, GET /audit/v2/verify
- **apps/api/provenance.py** — provenance record store; `record_provenance()`, GET /provenance/{kind}/{id}
- **apps/api/tests/test_audit_v2.py** — 23 pytest tests (TestAuditV2Events ×9, TestAuditV2Reset ×3, TestAuditV2Verify ×4, TestAuditChainDeterminism ×2, TestProvenanceEndpoint ×5)
- **apps/web/src/components/ProvenanceDrawer.tsx** — collapsible provenance panel: `provenance-open`, `provenance-drawer`, `provenance-input-hash`, `provenance-output-hash`, `provenance-audit-head`, `provenance-verify`, `provenance-verify-ok`
- **e2e/test-audit-provenance.spec.ts** — 8 Playwright E2E tests

### Changed
- `apps/api/main.py` — audit_v2_router + provenance_router registered; audit+provenance emitted in /runs/execute (both cache-hit and non-hit paths)
- `apps/api/devops_policy.py` — `_emit_audit_safe()` lazy audit integration on policy evaluate
- `apps/web/src/pages/RunHistory.tsx` — ProvenanceDrawer added per run row
- `apps/web/src/pages/DevOpsPage.tsx` — ProvenanceDrawer added in policy result section
- `apps/web/src/components/layout/AppLayout.tsx` — added `nav-stress` (FlameKindling icon)
- `apps/web/src/lib/api.ts` — 11 new API client functions (audit, provenance, rates, stress, compare)

---

## [3.2.0] – 2026-02-18

### Added (v3.2 – Submission Pack + Judge Demo)
- **phase6-judge-demo.spec.ts** — full Wave 6 tour E2E spec, 26 screenshots, covers all 10+ stops
- **playwright.judge.config.ts** — `slowMo: 4000` judge demo config for TOUR.webm ≥ 180s
- **scripts/submission/build_submission.ps1** — generates SUBMISSION.md, ARCHITECTURE.mmd, DEMO_SCRIPT.md, LINKS.md in timestamped zip
- **scripts/proof/run_wave6.ps1** — full proof runner: pytest → vitest → tsc → vite build with summary report
- **.env.example** — comprehensive environment template at repo root

### Changed
- API version bumped to 3.2.0
- Frontend version badge updated to v3.2.0

## [3.1.0] – 2026-02-18

### Added (v3.1 – DevOps Policy Gate)
- **apps/api/devops_policy.py** — `policy_router` with deterministic policy evaluation engine
  - `POST /devops/policy/evaluate` — scan diff for blockers (secrets, TODO, bare except, wildcards)
  - `POST /devops/policy/export` — generate MR comment markdown + reliability report + policy JSON
  - `GET /devops/policy/rules` — list all active policy rules
- **apps/api/tests/test_devops_policy.py** — 36 pytest tests across 3 test classes (TestPolicyEvaluate, TestPolicyExport, TestPolicyRules)
- **Policy Gate tab** in `DevOpsPage.tsx` — diff input, evaluate button, result badge, reasons list, markdown export preview
  - data-testids: `devops-tab-policy`, `devops-panel-policy`, `policy-evaluate-btn`, `policy-result-badge`, `policy-reasons-list`, `export-markdown-btn`, `export-json-btn`
- **e2e/test-devops-policy.spec.ts** — 8 Playwright E2E tests

### Changed
- DevOpsPage imports Badge component for policy decision display

## [3.0.0] – 2026-02-18

### Added (v3.0 – Multi-Agent Orchestration)
- **apps/api/multi_agent_orchestrator.py** — REST router wrapping existing IntakeAgent→RiskAgent→ReportAgent→SREAgent pipeline
  - `GET /orchestrator/plan` — 4-step agent execution plan with agents[] and flow[]
  - `POST /orchestrator/run` — execute full pipeline, returns audit_log + sre_checks + decision
  - `GET /orchestrator/agents` — list registered agents with name/role
- **apps/api/tests/test_multi_agent_orchestrator.py** — 15 pytest tests across 3 test classes
- **MicrosoftModePage** upgraded to 3-step wizard:
  - Step 1: Provider Status (`wizard-step-1`, `provider-status-card`)
  - Step 2: MCP Tools list + test call (`wizard-step-2`, `mcp-tools-list`, `mcp-test-call-button`)
  - Step 3: Multi-Agent Run + audit log + SRE checks (`wizard-step-3`, `multi-agent-run-btn`, `audit-log-table`, `sre-checks-list`)
- **SREAgent stub** — post-execution reliability checks (portfolio_value_positive, pnl_within_bounds, var_computed, audit_log_complete)
- **e2e/test-microsoft-wizard.spec.ts** — 10 Playwright E2E tests

## [2.9.0] – 2026-02-18

### Added (v2.9 – Platform Health & Readiness)
- **apps/api/platform_health.py** — `platform_router` with offline infra validation
  - `GET /platform/health/details` — expanded health with services, demo_mode, port
  - `GET /platform/readiness` — k8s-style readiness probe (checks api/engine/storage)
  - `GET /platform/liveness` — k8s-style liveness probe
  - `GET /platform/infra/validate` — offline infra invariant checks (port consistency, required files, .env.example)
- **apps/web/src/pages/PlatformPage.tsx** — platform health dashboard
  - data-testids: `platform-page`, `platform-health-card`, `platform-readiness-card`, `platform-liveness-card`, `platform-infra-card`, `platform-port-badge`, `platform-refresh-btn`
  - Real-time service status cards with latency, StatusDot indicators
- **apps/api/tests/test_platform_health.py** — 25 pytest tests across 5 test classes
- **e2e/test-platform.spec.ts** — 8 Playwright E2E tests
- **nav-platform** item added to AppLayout sidebar (Activity icon)
- **/platform route** added to App.tsx

## [2.8.0] – 2026-02-18


### Added (v2.8 — Proof Automation + Media Capture)
- **phase5-media tour** — single continuous E2E tour covering all 10 feature stops (Dashboard, Reports, Jobs, DevOps x4, Governance, Bonds, Microsoft Mode)
- **playwright.media.config.ts** — dedicated Playwright config with `slowMo: 4000` ensuring TOUR.webm >= 180 s without any `waitForTimeout` calls
- **scripts/proof/run_wave5.ps1** — one-command proof runner: TypeScript check → Vitest → frontend build → pytest → phase5-media tour → full Playwright suite → proof pack assembly
- **version-badge testid** — `data-testid="version-badge"` added to AppLayout sidebar version element for E2E verification
- **proof pack** — manifest.json + MANIFEST.md + TOUR.webm + screenshots/ generated by proof runner
- **34 phase5 screenshots** — full-page captures at every tour checkpoint (>= 25 required)

### Changed
- API version bumped from 2.5.1 to 2.8.0
- Frontend version bumped from v2.5.1 to v2.8.0
- All 15 Phase 4 E2E tests continue passing (0 failed, 0 skipped, retries=0)

## [2.7.0] — 2026-02-18

### Added (v2.7 — SSE Live Updates)
- **SSE infrastructure** (`apps/api/sse.py`) — `EventStream`, `sse_generator()`, `emit_job_event()`, `emit_run_event()` with in-memory fan-out to connected clients
- **SSE endpoints** — `/events/jobs` and `/events/runs` (streaming) + `/events/history/jobs` and `/events/history/runs` (last-N replay)
- **EventClient** (`apps/web/src/lib/eventClient.ts`) — TypeScript SSE client with auto-reconnect, typed event handlers, and clean unmount disconnect
- **live-updates-badge** on JobsPage — pulsing radio icon badge showing SSE connection status
- **phase4-14 test** — verifies live-updates-badge visible and contains "live"
- **SSE event emission** in `submit_job()` and `cancel_job()` API handlers
- **7 SSE pytest tests** (`apps/api/tests/test_sse.py`) — EventStream lifecycle, emit, multi-client fan-out

### Changed
- Total pytest count: 22 tests (15 original + 7 SSE)
- Total Phase 4 E2E: 15 tests (added phase4-13 + phase4-14)

## [2.6.0] — 2026-02-18

### Added (v2.6 — Persistent Job Store)
- **JobStoreSQLite** (`apps/api/jobs.py`) — SQLModel-backed persistent job store with full CRUD parity to in-memory JobStore
- **JobModel** — SQLModel table schema for job persistence (job_id, workspace_id, job_type, status, payload, result, timestamps)
- **get_job_store_backend()** — factory function returning current backend ("memory" or "sqlite") based on `JOB_STORE_BACKEND` env var
- **`/jobs/config/backend`** endpoint — reports active job store backend for UI badge
- **job-store-backend-badge** on JobsPage — displays current backend with "persistent" label for SQLite
- **Worker entrypoint** (`apps/api/worker.py`) — `Worker` class with signal handling, graceful shutdown, retry logic for background job processing
- **phase4-13 test** — verifies job-store-backend-badge visible and shows "memory" default
- **7 SQLite pytest tests** (`apps/api/tests/test_jobs.py`) — TestJobStoreSQLite covers CRUD, update status, cancel, list-with-filters

### Changed
- Total pytest tests: 18 (11 original + 7 new SQLite tests)
- JobStore protocol formalised via `JobStoreProtocol` duck-typing

## [2.5.1] — 2026-02-17

### Fixed (v2.5.1 — Media Gate Hotfix)
- **phase4-media test** — fixed API endpoint parameter mismatches and improved deterministic waits
- **Monitor endpoint** — `/devops/monitor/generate-report` now accepts JSON body instead of query parameters (consistent with other DevOps endpoints)
- **waitForResponse pattern** — set up response promises before button clicks to reliably catch API responses
- **networkidle waits** — added deterministic `waitForLoadState("networkidle")` to ensure pages fully load before proceeding
- **Test timeout** — increased playwright test timeout from 30s to 240s to accommodate media capture tests
- **Screenshot generation** — phase4-media now reliably generates >= 25 screenshots (30 checkpoints)

### Changed
- API version bumped from 2.5.0 to 2.5.1
- Frontend version bumped from 2.5.0 to 2.5.1
- All 13 Phase 4 E2E tests passing (0 failed, 0 skipped, retries=0)

## [2.5.0] — 2026-02-16

### Added (v2.5 — DevOps Automations)
- **GitLab MR Bot** — automated code review comment generation from git diffs (offline DEMO mode)
- **Monitor Reporter** — automated health check and coverage reporting with deterministic output
- **Test Harness** — offline test scenarios for MR review and monitoring cycles
- **DevOps API endpoints** — `/devops/gitlab/analyze-mr`, `/devops/gitlab/post-comment`, `/devops/gitlab/comments` (DEMO only)
- **Monitor endpoints** — `/devops/monitor/generate-report`, `/devops/monitor/reports`
- **Test harness endpoints** — `/devops/test-harness/run-scenario`, `/devops/test-harness/scenarios`
- **DevOps UI** — tabbed interface for Risk-Bot, GitLab MR Bot, Monitor Reporter, and Test Harness
- **Diff analysis** — detects debug logging, TODO comments, long lines in code changes
- **Health monitoring** — API status, database, storage, test coverage metrics
- **Offline validation** — all DevOps features work without external services in DEMO mode

### Changed
- DevOps page expanded with comprehensive automation tools
- API version remains 2.5.0 (includes v2.3-v2.5 features)

## [2.4.0] — 2026-02-16

### Added (v2.4 — Async Job Queue)
- **Deterministic Job model** — job_id = SHA256(workspace_id + canonical_payload + version)
- **JobStore** — in-memory CRUD operations for job lifecycle management
- **Job execution** — inline execution in DEMO mode with full job record tracking
- **Job API endpoints** — `/jobs/submit`, `/jobs/{job_id}`, `/jobs`, `/jobs/{job_id}/cancel`
- **Job types** — RUN, REPORT, HEDGE with deterministic execution
- **Job statuses** — QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
- **Async mode support** — existing endpoints support `?async=true` query parameter
- **Jobs UI** — dedicated Jobs page with filters, status badges, refresh capability
- **Job determinism** — same input produces same job_id across submissions
- **Job filtering** — filter by workspace_id, job_type, status

### Changed
- API version bumped from 2.3.0 to 2.4.0
- Navigation added Jobs page with full job queue management
- `execute_job_inline()` provides deterministic worker entrypoint for DEMO mode

## [2.3.0] — 2026-02-16

### Added (v2.3 — Storage + Signed Downloads)
- **Storage abstraction** — IStorage interface with LocalStorage and AzureBlobStorage implementations
- **LocalStorage provider** — deterministic filesystem storage under `./data/storage` (DEMO default)
- **AzureBlobStorage provider** — Azure Blob SDK integration with SAS token generation (optional, OFF by default)
- **Storage factory** — `get_storage_provider()` returns appropriate storage based on environment
- **Report bundle storage** — persist report.html, run.json, manifest.json with stable filenames
- **Download URLs** — deterministic download descriptors in DEMO, SAS URLs in production (when enabled)
- **Storage API endpoints** — `/reports/{id}/downloads`, `/storage/files/{key}` (DEMO proxy)
- **Storage provider badge** — UI显示 current storage provider (LocalStorage/AzureBlobStorage)
- **Download buttons** — reports page with download capability via storage endpoints
- **Deterministic storage** — write-twice same-input produces byte-identical files and hashes
- **Metadata files** — `.meta.json` sidecar files track storage timestamps and hashes

### Changed
- API version bumped from 2.2.0 to 2.3.0
- Reports page enhanced with storage integration and download functionality
- Report bundle builder uses storage backend for artifact persistence

## [2.2.0] — 2026-02-16

### Added (v2.2 — Microsoft Hero Tech Integration)
- **Azure AI Foundry provider** — text generation via Azure AI Foundry with strict "numbers policy" (no hallucinated metrics)
- **MCP server** — Model Context Protocol endpoints exposing RiskCanvas tools (`/mcp/tools`, `/mcp/tools/call`, `/mcp/health`)
- **MCP tool catalog** — `portfolio_analyze`, `report_build`, `hedge_suggest`, `governance_eval_run` available via MCP
- **Numbers policy enforcement** — Foundry provider validates that model output only references computed values from context
- **Agent Framework integration** — documentation and samples for Microsoft Agent Framework wiring
- **Microsoft Mode UI** — frontend panel showing MCP tools, provider status, and test execution
- **Mock provider** — deterministic fallback for testing without Azure credentials (`FOUNDRY_MODE=mock`)
- **Integration documentation** — `/integrations/microsoft/README.md` with complete setup guide

### Changed
- API version bumped to 2.2.0
- Backend includes MCP router in main.py (`app.include_router(mcp_router)`)
- Frontend adds `/microsoft` route with MCP tool visualization

## [2.1.0] — 2026-02-16

### Added (v2.1 — Real Deployment: Azure + DigitalOcean)
- **Azure Container Apps deployment** — Bicep templates for production deployment (`/infra/azure/main.bicep`)
- **Azure Container Registry** — automated docker image builds and pushes
- **GitHub Actions workflow** — `.github/workflows/azure-deploy.yml` for CI/CD to Azure
- **Dockerfiles** — production-ready containers for API (port 8090) and Web (nginx)
- **Azure Log Analytics** — centralized logging and monitoring with Application Insights integration
- **DigitalOcean deploy docs** — updated deployment guide for DO with auth modes
- **Environment-based configuration** — dev/staging/prod parameter support in Bicep
- **HTTPS ingress** — Container Apps configured with external ingress and TLS

### Changed
- API Dockerfile uses Python 3.11-slim with optimized layer caching
- Web Dockerfile uses multi-stage build (node builder + nginx production)
- Deploy docs moved to `/docs/deploy-azure.md` and `/docs/deploy-digitalocean.md`

## [2.0.0] — 2026-02-16

### Added (v2.0 — Authentication & Enterprise Hardening)
- **Azure Entra ID authentication** — JWT validation with JWKS fetching (`AUTH_MODE=entra`)
- **Role-based access control (RBAC)** — maps Entra ID roles to RiskCanvas roles (viewer/analyst/admin)
- **auth_entra module** — `validate_auth()` dependency for endpoint protection
- **Workspace ownership verification** — `get_workspace()` and `delete_workspace()` now enforce owner checks
- **Auth mode detection** — frontend displays current auth mode (demo/none/entra) in Settings
- **Token management** — localStorage-based auth token storage with `getAuthToken()`, `setAuthToken()`, `clearAuthToken()`
- **Authorization headers** — API client automatically attaches `Authorization: Bearer <token>` in Entra mode
- **Auth tests** — comprehensive test coverage for DEMO, none, and Entra modes (mocked JWT validation)
- **Backward compatibility** — DEMO mode still works with `X-Demo-User`/`X-Demo-Role` headers

### Changed
- **BREAKING: API_VERSION changed to 2.0.0** — major version bump for auth changes
- **BREAKING: AUTH_MODE default is "none"** — production requires explicit configuration
- `main.py` imports `validate_auth` from `auth_entra` module instead of `get_demo_user_context` from `rbac`
- All workspace endpoints now pass `requesting_user` for ownership verification
- Settings page shows auth mode badge with DEMO/NONE/ENTRA indicator (data-testid="auth-mode-indicator")
- `config.ts` exports `getAuthMode()`, `getAuthHeaders()` for mode-aware header injection
- `api.ts` uses `getAuthHeaders()` instead of `getDemoHeaders()` for universal auth support

## [1.9.0] — 2026-02-16

### Added (v1.9 — Caching Layer)
- **Deterministic cache layer** — SHA256-based cache keys for pricing, VaR, and Greeks calculations
- **Cache hit indicators** — API responses now include `x-cache-hit` header and `from_cache` field
- **Cache statistics** — performance metrics showing cache hit rates across endpoints
- **Cache module** — `caching.py` with thread-safe in-memory cache and cache key generation
- **Backend integration** — all compute-intensive endpoints (pricing, runs/execute) now use cache layer

### Changed
- **BREAKING: DEMO_MODE default changed from true to false** — production deployments now require explicit DEMO_MODE=true
- API version bumped to 1.9.0
- Backend tests: 116 passed (including cache hit verification)
- E2E tests: 29 passed (retries=0, workers=1) — comprehensive coverage of all v1.1-v1.9 features
- Test infrastructure: All gates green with strict validation (0 failed, 0 skipped)

## [1.8.0] — 2026-02-16

### Added (v1.8 — Bonds Module)
- **Fixed-rate bond pricing** — `POST /bonds/price` calculates bond present value using yield discounting
- **Yield calculation** — `POST /bonds/yield-from-price` computes yield to maturity from market price
- **Risk metrics** — duration, convexity, DV01 (dollar value of 1 basis point) calculations
- **Deterministic calculations** — all bond computations use fixed precision for reproducibility
- **Bonds frontend** — React page for interactive bond calculator with real-time pricing
- **Bond validation** — input validation for face_value, coupon_rate, years_to_maturity, yield/price

### Changed
- API version bumped to 1.8.0
- Backend tests: 116 passed (including 8 bond pricing tests)
- Frontend: Bonds page added to navigation with data-testid selectors

## [1.7.0] — 2026-02-16

### Added (v1.7 — Governance Module)
- **Agent configuration registry** — `POST /governance/agents`, `GET /governance/agents` for storing AI agent configs
- **Deterministic agent IDs** — `agent_id = SHA256(name + model + provider + system_prompt)[:32]`
- **Evaluation harness** — `POST /governance/agents/{id}/eval` runs test cases against agent configurations
- **Activation tracking** — agent configs can be activated/deactivated with timestamp tracking
- **Governance frontend** — React page for agent config management and evaluation result display
- **EVAL_CASES library** — predefined test cases for portfolio pricing and VaR validation
- **Test coverage** — 7 new E2E tests for governance and bonds features

### Changed
- API version bumped to 1.7.0  
- Backend tests: 116 passed (including governance agent CRUD and eval tests)
- Frontend: Governance page added with create/eval/activate workflows

## [1.6.0] — 2026-02-15

### Added (v1.6 — Monitoring & Drift Detection)
- **Monitor management** — `POST /monitors`, `GET /monitors`, `GET /monitors/{id}` for portfolio monitoring
- **Monitor execution** — `POST /monitors/{id}/run-now` triggers on-demand analysis with threshold checks
- **Alert system** — automatic alert generation when VaR exceeds configured thresholds (severity: info/medium/high/critical)
- **Drift detection** — `GET /drift-summaries` computes portfolio changes between consecutive runs
- **Drift scoring** — quantifies portfolio changes using asset-level deltas and VaR changes
- **Sequence-based determinism** — global counters for monitors, alerts, and drift summaries (no real timestamps)
- **Schedule support** — hourly, daily, weekly monitoring schedules
- **Monitoring frontend** — React pages for monitor creation, run-now execution, alert display, drift summary cards

### Added (v1.5 — DevOps Pack)
- **Risk-bot CLI** — `POST /devops/risk-bot` generates deterministic reports for CI/CD pipelines
- **Determinism hashes** — all artifacts (portfolios, runs, reports) include SHA256 hashes for verification
- **CI-ready outputs** — markdown reports with embedded hashes for GitLab/GitHub integration
- **DevOps frontend** — report generation UI with hash display and CI checklist

### Added (v1.4 — Enterprise Readiness: Workspaces + RBAC + Audit)
- **Workspace management** — `POST /workspaces`, `GET /workspaces`, `GET /workspaces/{id}`, `DELETE /workspaces/{id}`
- **Deterministic workspace IDs** — `workspace_id = SHA256(owner + seed)[:32]` for reproducibility
- **RBAC (Role-Based Access Control)** — roles: viewer, analyst, admin with permission matrices
- **DEMO mode RBAC** — uses `X-Demo-User` and `X-Demo-Role` headers for testing (no real auth complexity)
- **Audit logging** — all operations recorded in `AuditEventModel` with input/output hashes
- **Audit event IDs** — deterministic `event_id = SHA256(workspace + actor + action + resource + sequence)`
- **Audit retrieval** — `GET /audit` with filters for workspace, actor, resource_type
- **Workspace isolation** — portfolios, runs, and reports scoped to workspaces
- **Frontend UI pages**:
  - Portfolio Library (`/library`) — save portfolios, run analysis, view list
  - Run History (`/history`) — view all runs, select and compare
  - Compare page (`/compare`) — side-by-side delta KPIs and top asset changes
  - Reports Hub (`/reports-hub`) — build report bundles, view hashes, download artifacts
  - Hedge Studio (`/hedge`) — generate hedge suggestions with target VaR reduction
  - Workspaces page (`/workspaces`) — create/switch/delete workspaces
  - Audit page (`/audit`) — view audit events with filters and hash display
  - DevOps page (`/devops`) — generate risk-bot reports
  - Monitoring page (`/monitoring`) — create monitors, run analysis, view alerts/drift

### Changed
- API version bumped to 1.6.0
- Backend tests: 116 passed (all v1.0-v1.6 endpoints)
- Frontend: 8 new pages, all routes added to App.tsx
- Database: Enhanced with `_import_all_models()` to load WorkspaceModel, AuditEventModel, MonitorModel, AlertModel, DriftSummaryModel
- UI components: Added Slider and Select from @radix-ui
- E2E tests: 5 new test files (18+ tests) covering Phase 2A + Phase 2B flows
- Test suite: Comprehensive tour test (≥180s) demonstrating all v1.1-v1.6 features

## [1.3.0] — 2026-02-15

### Added (v1.3 — Hedge Studio)
- **Deterministic hedge suggestions** — `POST /hedge/suggest` generates ranked hedge candidates to reduce VaR
- **Hedge evaluation** — `POST /hedge/evaluate` runs scenario analysis on hedge candidates
- **Hedge engine** — grid search over protective puts and exposure reduction strategies
- **Cost-effectiveness scoring** — ranks hedges by VaR reduction per dollar spent
- **Scenario testing** — evaluates hedge performance under price shocks (-20%, -10%, 0%, +10%)
- **Hedge Studio frontend APIs** — `suggestHedges()`, `evaluateHedge()` in api.ts

### Added (v1.2 — Reporting Engine v2)
- **Report Bundle Builder** — self-contained HTML reports with embedded SVG charts (no CDN dependencies)
- **Deterministic chart generation** — SVG bar charts for VaR distribution and portfolio Greeks
- **Report bundle IDs** — stable hashes based on run_id + outputs
- **Report endpoints** — `POST /reports/build`, `GET /reports/{id}/manifest`, `GET /reports/{id}/report.html`, `GET /reports/{id}/run.json`
- **Report manifest** — includes all hashes, file links, and metadata

### Added (v1.1 — Portfolio Library + Run History)
- **SQLite persistence** — SQLModel-based storage with deterministic IDs
- **Portfolio CRUD** — `GET /portfolios`, `POST /portfolios`, `GET /portfolios/{id}`, `DELETE /portfolios/{id}`
- **Run execution** — `POST /runs/execute` runs analysis and stores results with deterministic run_id
- **Run history** — `GET /runs`, `GET /runs/{id}` with filtering by portfolio_id
- **Run comparison** — `POST /runs/compare` computes deltas between two runs
- **Deterministic IDs** — portfolio_id = hash(canonical_portfolio), run_id = hash(portfolio_id + params + engine_version)
- **Canonical JSON** — sorted keys, no whitespace, consistent encoding
- **In-memory DB for tests** — uses sqlite:///:memory: when running under pytest
- **14 persistence tests** — full coverage of portfolio/run CRUD and determinism
- **Frontend API extensions** — all v1.1+ endpoints added to api.ts

### Changed
- API version bumped to 1.3.0
- Backend tests increased to 116 (from 102)

## [1.0.0] — 2025-07-19

### Added
- **Consolidated API v1.0** — all v1 legacy endpoints + v2+ engine endpoints + determinism check
- **Error taxonomy** — `ErrorCode` enum with structured error responses (`errors.py`)
- **Determinism endpoint** — `POST /determinism/check` verifies all computations are repeatable
- **Edge-case tests** — 42 engine edge-case tests (near-expiry, zero vol, deep ITM/OTM, negative rates, empty portfolios)
- **API determinism tests** — 7 tests verifying endpoint-level determinism
- **Monte Carlo guardrails** — max 100,000 paths, seed range validation
- **Phase 1 frontend** — React 19 SPA with portfolio table, risk analysis, determinism check, export with download
- **DEMO fallback** — frontend works standalone with mock data when API is unreachable
- **DigitalOcean deployment** — Docker Compose setup with Dockerfile.api, Dockerfile.web, nginx reverse proxy
- **GitLab CI pipeline** — lint, test, build, deploy stages
- **GitLab mirror script** — `scripts/gitlab-mirror.ps1` for dual-remote setup
- **Risk Bot** — `scripts/risk-bot.py` agentic DevOps assistant for MR/PR risk commentary
- **API documentation** — `docs/api.md` with full endpoint reference
- **Threat model** — `docs/threat-model.md` with STRIDE analysis
- **Runbooks** — `docs/runbooks.md` for operations and incident response
- **Demo pack** — `demo/run_demo.py` + `demo/expected_hashes.json`
- **EditorConfig** — `.editorconfig` for consistent formatting
- **Playwright E2E** — 6 end-to-end tests with Chromium, headless, retries=0

### Fixed
- Engine import paths (orchestrator, multi_agent, mcp_server) — changed from 3 to 4 parents
- `multi_agent.py` model_dump() → `exclude_none=True` to prevent None values
- `multi_agent.py` f-string syntax errors in `_build_prompt` and `_format_scenarios_html`
- `test_artifacts_gitignore.py` — fixed git ls-files return code assertions

### Changed
- Engine imports use `packages/engine` + `from src import` pattern (supports relative imports)
- API version bumped to 1.0.0
- Dark theme CSS design system

## [0.1.0] — Initial

### Added
- Black-Scholes option pricing engine
- Greeks calculation (delta, gamma, vega, theta, rho)
- Portfolio P&L and aggregated Greeks
- Parametric and historical VaR
- Scenario analysis (price, vol, rate, combined shocks)
- FastAPI endpoints for all engine functions
- Multi-agent orchestration system
- MCP server integration
