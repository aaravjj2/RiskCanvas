---
name: riskcanvas-testgate
description: Run deterministic test gates and summarize results.
openclaw:
  requires:
    bins:
      - git
      - node
      - npm
      - python
---

# RiskCanvas TestGate
Run what exists, fail hard on any non-zero.
- TypeScript:  npm run -s typecheck
- Unit tests:  npm test --silent
- Backend:     pytest -q
- E2E:         npx playwright test --retries=0 --workers=1
Report commands executed + pass/fail counts + report paths.
