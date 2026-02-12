---
name: riskcanvas-testgate
description: Run deterministic test gates and summarize results.
---
# RiskCanvas TestGate
When invoked:
1) Run the project checks deterministically.
2) Fail hard if anything is non-zero.

Default commands (run what exists):
- TypeScript:  npm run -s typecheck
- Unit tests:  npm test --silent
- Backend:     pytest -q
- E2E:         npx playwright test --retries=0 --workers=1

Report:
- command lines executed
- pass/fail counts
- paths to reports (playwright-report/, test-results/)

