---
name: riskcanvas-claude-run
description: Drive Claude Code task-by-task with test gates.
openclaw:
  requires:
    bins:
      - claude
      - git
      - node
      - npm
---

# RiskCanvas ClaudeRun
Execute ONE TASKS.md item at a time.
After changes: run /riskcanvas-testgate. Fix until green.
When milestone completes: run /riskcanvas-proofpack.
