# Week Plan (autopilot)

## Engine + API foundations
- [x] M1.4 Implement stock P&L + delta exposure (API + tests)
- [x] M1.5 Implement portfolio aggregation: net delta, gross exposure, sector breakdown (fixtures-driven)
- [x] M1.6 Add API endpoint: POST /portfolio/report reads fixture-like payload and returns summary JSON (stable schema)
- [x] M1.7 Add API validation: pydantic models for positions, raise clean 422s, add tests
- [x] M1.8 Add deterministic timestamps/IDs to report output (testable; no “now” in unit tests)
- [x] M1.9 Move report outputs to repo-root artifacts/ and gitignore them; add tests to ensure not committed

## Options surface + scenario analysis
- [x] M2.1 Implement implied volatility solver (Newton/bisection) for BS price; tests with known examples
- [x] M2.2 Implement scenario shocks for options: S shock, vol shock, rate shock; return P&L grid
- [x] M2.3 Add API endpoint: POST /options/scenario-grid returns grid + metadata; tests
- [x] M2.4 Add fixtures: 2 option-heavy portfolios (mixed calls/puts, expiries), deterministic
- [x] M2.5 Add “risk summary” API: VaR placeholders + scenario worst-case placeholder (explicit TODOs, stable schema)

## VaR / CVaR (real risk)
- [ ] [blocked] M3.1 Implement returns calculation for equities: simple + log returns; tests  // Claude hit max turns. See artifacts/logs/20260212-132518-implement.log
- [x] M3.2 Implement historical simulation VaR + CVaR for a portfolio of stocks (using fixture prices); tests
- [x] M3.3 Implement parametric (normal) VaR for stocks; tests + compare to historical
- [x] M3.4 Add bond price sensitivity approximation using duration/convexity to estimate P&L under yield shocks; tests
- [ ] [blocked] M3.5 Add portfolio VaR aggregation across stocks + bonds (document assumptions); tests  // Claude hit max turns. See artifacts/logs/20260212-145142-implement.log
- [x] M3.6 Add API endpoint: POST /risk/var supports method=historical|parametric; tests

## Monte Carlo (keeps it busy and impressive)
- [x] M4.1 Implement GBM path simulation for equities; seeded RNG; tests for determinism
- [x] M4.2 Implement Monte Carlo VaR for stocks with seeded paths; tests
- [x] M4.3 Extend MC to include option pricing along paths (fast approximation is ok); tests on small case
- [x] M4.4 Add API endpoint: POST /risk/mc-var with configurable paths/steps/seed; tests
- [ ] [blocked] M4.5 Add performance guardrails: cap paths in API + clear error messages; tests  // Gates never passed after 5 attempts.

## Web app: real UI + data-testid everywhere
- [ ] [blocked] W1 Build Portfolio page: load one fixture via button, show positions table (data-testid only)  // Gates never passed after 5 attempts.
- [ ] [blocked] W2 Build Risk Summary panel: show delta exposure, DV01, VaR placeholders; unit tests  // Gates never passed after 5 attempts.
- [ ] [blocked] W3 Add “Run Risk” button calling API /portfolio/report; mock in unit tests  // Gates never passed after 5 attempts.
- [ ] [blocked] W4 Show scenario grid results (table) for option-heavy fixture; unit tests  // Gates never passed after 5 attempts.
- [ ] [blocked] W5 Add export button that downloads JSON report; unit tests  // Gates never passed after 5 attempts.

## E2E: real flow
- [ ] [blocked] E1 Playwright: load app, click “Load fixture”, verify table rows appear (data-testid only)  // Gates never passed after 5 attempts.
- [ ] [blocked] E2 Playwright: click “Run Risk”, wait for results, verify risk summary fields appear  // Gates never passed after 5 attempts.
- [ ] [blocked] E3 Playwright: click “Export JSON”, verify download happens (or mocked endpoint); no flaky waits  // Claude hit max turns. See artifacts/logs/20260212-224555-implement.log

## Quality + repo hygiene
- [ ] Q1 Add .gitattributes to normalize line endings (fix CRLF/LF warnings)
- [ ] Q2 Tighten gitignore for python bytecode + artifacts + test outputs; ensure repo is clean
- [ ] Q3 Add CI workflow (GitHub Actions): run scripts/testgate.ps1 on PR/push
- [ ] Q4 Add README: one-command setup + run instructions + demo script
- [ ] Q5 Add “demo mode” script that runs API, runs web, generates a sample report into artifacts/

## Stretch: portfolio optimization
- [ ] O1 Implement mean-variance optimizer (basic constraints) using deterministic input; tests
- [ ] O2 Add API endpoint: POST /optimize returns weights + expected risk/return; tests
- [ ] O3 Add UI: “Optimize” panel for one fixture; unit tests
- [ ] O4 Add E2E: run optimize and verify weights sum to 1
