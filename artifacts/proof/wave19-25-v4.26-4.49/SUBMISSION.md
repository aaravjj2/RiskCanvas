# Wave 19-25 Submission (v4.26.0 – v4.49.0)

## Delivery Summary

This submission covers Waves 19-25, introducing 7 new capability modules across
the full stack (backend Python API, React frontend, E2E Playwright tests).

---

## Wave 19 — FX Multi-Currency Risk Engine (v4.26.0 – v4.29.0)

**Focus:** Foreign exchange spot/forward/volatility surface, portfolio exposure,
and shock analysis across 10 currency pairs.

**Key capabilities:**
- 10 FX pairs (EURUSD, GBPUSD, JPYUSD, CHFUSD, AUDUSD, CADUSD, NZDUSD, SEKUSD, NOKDUD, MXNUSD)
- 4 tenor points (SP, 1W, 1M, 3M) with full vol surface
- Portfolio exposure aggregation by base currency
- Shock engine: apply % moves to named pairs, return P&L impact
- Export pack: rates + exposure + shocked P&L

**Tests:** 18 pytest, 5 Playwright E2E

---

## Wave 20 — Credit Spread Curves & Risk (v4.30.0 – v4.33.0)

**Focus:** Credit spread term structures, DV01 sensitivity, spread shock scenarios.

**Key capabilities:**
- 4 spread curves: USD-IG, USD-HY, EUR-IG, EM-HY
- 5-tenor term structure (3M, 6M, 1Y, 3Y, 5Y)
- DV01 credit risk per position
- Parallel shift shocks (+25bp, +50bp, +100bp)
- Export pack: curves + risk + shocked values

**Tests:** 14 pytest, 2 Playwright E2E

---

## Wave 21 — Liquidity Risk & Transaction Cost (v4.34.0 – v4.37.0)

**Focus:** Haircut-based liquidity tiers, transaction cost laddering, cost-vs-liquidity tradeoff.

**Key capabilities:**
- 14-symbol haircut table (3 tiers: High/Medium/Low liquidity)
- T-cost ladder: 3 trade sizes × 14 symbols
- Liquidity-vs-cost tradeoff matrix for portfolio optimization
- Export pack: haircuts + T-cost + tradeoff

**Tests:** 17 pytest, 3 Playwright E2E

---

## Wave 22 — Approval Workflow Engine (v4.38.0 – v4.41.0)

**Focus:** Structured approval state machine for trading decisions.

**Key capabilities:**
- State machine: DRAFT -> SUBMITTED -> APPROVED / REJECTED
- Immutable audit trail per approval (`approval_id` field)
- 3 pre-seeded demo approvals (limit trade, hedge, unwind)
- Decision pack export (JSON)

**Tests:** 22 pytest, 3 Playwright E2E

---

## Wave 23 — GitLab MR Risk Intelligence (v4.42.0 – v4.45.0)

**Focus:** Offline GitLab adapter analyzing merge requests for risk exposure.

**Key capabilities:**
- 4 fixture MRs (iid 101-104): pricing model, VaR tweak, FX hedge, limits
- Per-MR diff analysis + risk tagging (PRICING/RISK/CONFIG/COMPLIANCE)
- Risk score aggregation
- Export pack: MR list + diffs + analysis

**Tests:** 20 pytest, 2 Playwright E2E

---

## Wave 24 — CI/CD Intelligence (v4.46.0 – v4.47.0)

**Focus:** Pipeline analysis and automated CI template generation.

**Key capabilities:**
- 5 demo pipelines with stage breakdown (build/test/security/deploy/notify)
- Pipeline health analysis (duration, failure rate, coverage, security score)
- YAML CI template generator with configurable feature flags
- Export pack: pipelines + analysis + template

**Tests:** 17 pytest, 2 Playwright E2E

---

## Wave 25 — DevSecOps Security Suite (v4.48.0 – v4.49.0)

**Focus:** Automated secret scanning, SBOM generation, and cryptographic attestation.

**Key capabilities:**
- 8 regex detection rules: SEC-001 (AWS keys) through SEC-008 (GitHub PATs)
- Demo diff pre-seeded with 3 CRITICAL secret findings → BLOCKED gate
- SBOM generator: 12-package SBOMs with SHA256 hashes
- Attestation engine: 3 levels (SCAN_PASSED, SBOM_GENERATED, APPROVED)
- Export pack: findings + SBOM + attestation

**Tests:** 28 pytest, scan/SBOM/attest Playwright E2E

---

## Integration Commit (v4.49.0)

The mega final commit at v4.49.0 integrates all Wave 19-25 work into the core app:

- `apps/api/main.py`: 14 new routers registered
- `apps/api/pytest.ini`: `pythonpath = .` for bare module imports  
- `apps/web/src/App.tsx`: 7 new routes (`/fx`, `/credit`, `/liquidity`, `/approvals`, `/gitlab`, `/ci`, `/security`)
- `apps/web/src/components/layout/AppLayout.tsx`: 7 nav items + version badge `v4.49.0`
- `apps/web/src/lib/api.ts`: All Wave 19-25 API client functions

---

## All Gates Passed

```
tsc -b                          0 errors
npm run build                   built in 2.71s
pytest -q                       767 passed  0 failed  0 skipped
npx playwright test (units)     17 passed   0 failed  0 skipped  retries=0 workers=1
npx playwright test (judge)      1 passed   0 failed  0 skipped  retries=0 workers=1
```
