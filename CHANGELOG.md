# Changelog

All notable changes to RiskCanvas are documented in this file.

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
