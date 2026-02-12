---
name: riskcanvas-proofpack
description: Build the proof-pack folder (manifest + reports + inventory).
openclaw:
  requires:
    bins:
      - git
      - node
      - npm
---

# RiskCanvas ProofPack
Create /artifacts/proof/<timestamp>-<milestone>/.
Write MANIFEST.md + manifest.json.
Copy in playwright-report/, test-results/, screenshots/ if present.
Never claim done without artifacts on disk.
