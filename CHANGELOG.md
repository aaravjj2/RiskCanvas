# Changelog

All notable changes to RiskCanvas are documented in this file.

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
