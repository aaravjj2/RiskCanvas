#!/usr/bin/env bash
# run_wave_depth_v5.56.1-5.60.0.sh — Depth Wave proof runner
# Reproduces all gates for v5.56.1 → v5.60.0
#
# Requirements:
#   - API server running on :8090
#   - Vite preview running on :4178
#   - Python .venv activated
#   - Playwright browsers installed

set -e
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

echo "════════════════════════════════════════"
echo " Depth Wave v5.56.1-v5.60.0 — Proof Run"
echo "════════════════════════════════════════"

# ── Gate 1: TypeScript ────────────────────────────────────────────────────────
echo ""
echo "── Gate 1: tsc --noEmit ─────────────────"
cd apps/web && npx tsc --noEmit && echo "✓ 0 TypeScript errors" && cd "$REPO"

# ── Gate 2: Build ─────────────────────────────────────────────────────────────
echo ""
echo "── Gate 2: npm run build ────────────────"
cd apps/web && npm run build && echo "✓ Build succeeded" && cd "$REPO"

# ── Gate 3: pytest ────────────────────────────────────────────────────────────
echo ""
echo "── Gate 3: pytest ──────────────────────"
cd apps/api && python -m pytest tests/test_depth_wave_contract.py -v --tb=short && cd "$REPO"

# ── Gate 4: Playwright depth E2E ─────────────────────────────────────────────
echo ""
echo "── Gate 4: playwright depth E2E (28) ───"
npx playwright test --config e2e/playwright.depth.e2e.config.ts

# ── Gate 5: Playwright judge demo v5 ─────────────────────────────────────────
echo ""
echo "── Gate 5: playwright judge demo v5 (17) ─"
npx playwright test --config e2e/playwright.depth.judge.config.ts

# ── Gate 6: Playwright stab regression ───────────────────────────────────────
echo ""
echo "── Gate 6: stab regression ─────────────"
npx playwright test --config e2e/playwright.stab.e2e.config.ts
npx playwright test --config e2e/playwright.stab.unit.config.ts

echo ""
echo "════════════════════════════════════════"
echo " ALL GATES GREEN — Depth Wave v5.60.0 ✓"
echo "════════════════════════════════════════"
echo ""
echo "TOUR.webm: artifacts/proof/TOUR.webm"
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  artifacts/proof/TOUR.webm 2>/dev/null | \
  awk '{printf "  Duration: %.1fs\n", $1}'
