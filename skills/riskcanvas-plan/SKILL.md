---
name: riskcanvas-plan
description: Generate TASKS.md + milestones with verification gates.
openclaw:
  requires:
    bins:
      - git
      - node
      - npm
---

# RiskCanvas Plan
Create/refresh TASKS.md with milestones + acceptance criteria.
Every task must have a verification step (tests, snapshot hash, or reproducible artifact).
Output:
1) TASKS.md
2) Next 3 tasks to run immediately.
