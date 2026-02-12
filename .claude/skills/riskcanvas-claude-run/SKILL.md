---
name: riskcanvas-claude-run
description: Drive Claude Code task-by-task with test gates.
---
# RiskCanvas ClaudeRun
Use Claude Code to execute ONE task at a time from TASKS.md.
Rules:
- Create/modify files in small commits.
- After changes: run /riskcanvas-testgate.
- If tests fail: fix until pass.
- When a milestone completes: run /riskcanvas-proofpack.

If claude CLI isn't available, stop and output the exact missing dependency.

