# Changelog

All notable changes to RiskCanvas are documented in this file.

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
