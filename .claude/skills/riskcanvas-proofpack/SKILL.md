---
name: riskcanvas-proofpack
description: Build the proof-pack folder (manifest + reports + inventory).
---
# RiskCanvas ProofPack
When invoked:
- Create /artifacts/proof/<timestamp>-<milestone>/ structure
- Write MANIFEST.md (objective, scope, commands run, results, inventory)
- Copy in: playwright-report/, test-results/, screenshots/ if present
- Generate manifest.json with counts + hashes (if possible)

Never claim completion without artifacts present on disk.

