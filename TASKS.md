# TASKS

## Milestone 0 — Scaffold + Gates (must be green before anything else)
- [x] M0.1 Scaffold monorepo: apps/web, apps/api, packages/engine, e2e, scripts/, artifacts/
- [x] M0.2 Web: React+TS+Vitest configured; typecheck + unit tests pass (0 failed/0 skipped)
- [x] M0.3 API: FastAPI + Pytest configured; unit tests pass (0 failed/0 skipped)
- [x] M0.4 E2E: Playwright configured (retries=0 workers=1, video/trace/screenshot on); tests pass; selectors are data-testid only
- [x] M0.5 Add deterministic fixtures: 3 sample portfolios in fixtures/ (JSON)
- [x] M0.6 Add export skeleton: JSON report file written to artifacts/ on demand (stub ok)

## Milestone 1 — Pricing Engine (deterministic)
- [x] M1.1 Implement Black–Scholes price for European calls/puts
- [x] M1.2 Implement closed-form Greeks: delta, gamma, vega, theta, rho
- [x] M1.3 Implement fixed-coupon bond PV + duration + convexity + DV01
- [x] M1.4 Implement stock P&L + delta exposure
- [x] M1.5 Engine unit tests: put–call parity, monotonicity, bond price vs yield, invariants (0 failed/0 skipped)

## Milestone 2 — Scenario Engine
- [x] M2.1 Deterministic scenarios: spot ±1/5/10/20%, vol ±10/30 pts, rates +50/+100/+200 bps, curve twist
- [x] M2.2 Scenario P&L table + worst-case highlight
- [x] M2.3 Factor attribution buckets: delta/vega/rates for scenario P&L

## Milestone 3 — UI (judges remember this)
- [x] M3.1 Portfolio builder UI (stocks/options/bonds) with templates + guardrails
- [x] M3.2 Risk dashboard: top 3 drivers + exposures + scenario worst-case
- [x] M3.3 Scenario explorer: select scenario set; recompute; show P&L table
- [ ] M3.4 Export: HTML + JSON report downloadable, offline

## Milestone 4 — Proof + determinism
- [ ] M4.1 Determinism check: run same fixture twice; outputs hash-identical
- [ ] M4.2 Proof packs: /artifacts/proof/<timestamp>-<milestone>/ with MANIFEST.md + reports
