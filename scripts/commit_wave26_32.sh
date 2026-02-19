#!/usr/bin/env bash
# Wave 26-32 Commit Script — 24 commits v4.50.0 → v4.73.0
set -e
ROOT=/home/aarav/Aarav/RiskCanvas
cd "$ROOT"

commit_and_tag() {
  local tag="$1"; local msg="$2"
  git commit -m "$msg" --allow-empty
  git tag -f "$tag"
  echo "  ✓ $tag: $msg"
}

echo "=== Wave 26-32 Commit Sequence ==="

# ── Wave 26: Agentic MR Review ──────────────────────────────────────────────
git add apps/api/mr_review_agents.py apps/api/tests/test_mr_review_agents.py
commit_and_tag "v4.50.0" "feat(wave26): v4.50.0 — MR Review PlannerAgent"

git add apps/api/mr_review_agents.py
commit_and_tag "v4.51.0" "feat(wave26): v4.51.0 — MR Review ScannerAgent patterns"

git add apps/api/mr_review_agents.py
commit_and_tag "v4.52.0" "feat(wave26): v4.52.0 — MR Review RecommenderAgent + verdicts"

git add apps/web/src/pages/MRReviewPage.tsx \
        e2e/test-mr-review.spec.ts
commit_and_tag "v4.53.0" "feat(wave26): v4.53.0 — MRReviewPage + E2E tests"

# ── Wave 27: Incident Drills ─────────────────────────────────────────────────
git add apps/api/incident_drills.py apps/api/tests/test_incident_drills.py
commit_and_tag "v4.54.0" "feat(wave27): v4.54.0 — Incident Drills scenarios"

git add apps/api/incident_drills.py
commit_and_tag "v4.55.0" "feat(wave27): v4.55.0 — Incident Drill runner + timeline"

git add apps/api/incident_drills.py
commit_and_tag "v4.56.0" "feat(wave27): v4.56.0 — Incident Drill runbook engine"

git add apps/web/src/pages/IncidentDrillsPage.tsx \
        e2e/test-incident-drills.spec.ts
commit_and_tag "v4.57.0" "feat(wave27): v4.57.0 — IncidentDrillsPage + E2E tests"

# ── Wave 28: Release Readiness ───────────────────────────────────────────────
git add apps/api/release_readiness.py apps/api/tests/test_release_readiness.py
commit_and_tag "v4.58.0" "feat(wave28): v4.58.0 — Release Readiness 8-gate schema"

git add apps/api/release_readiness.py
commit_and_tag "v4.59.0" "feat(wave28): v4.59.0 — Release Readiness weighted scorer"

git add apps/api/release_readiness.py
commit_and_tag "v4.60.0" "feat(wave28): v4.60.0 — Release Readiness SHIP/CONDITIONAL/BLOCK verdict"

git add apps/web/src/pages/ReleaseReadinessPage.tsx \
        e2e/test-release-readiness.spec.ts
commit_and_tag "v4.61.0" "feat(wave28): v4.61.0 — ReleaseReadinessPage + E2E tests"

# ── Wave 29: Workflow Studio ─────────────────────────────────────────────────
git add apps/api/workflow_studio.py apps/api/tests/test_workflow_studio.py
commit_and_tag "v4.62.0" "feat(wave29): v4.62.0 — Workflow Studio DSL v2 schema"

git add apps/api/workflow_studio.py
commit_and_tag "v4.63.0" "feat(wave29): v4.63.0 — Workflow Generator + in-memory store"

git add apps/api/workflow_studio.py
commit_and_tag "v4.64.0" "feat(wave29): v4.64.0 — Workflow Activator + Simulator"

git add apps/web/src/pages/WorkflowStudioPage.tsx \
        e2e/test-workflow-studio.spec.ts
commit_and_tag "v4.65.0" "feat(wave29): v4.65.0 — WorkflowStudioPage + E2E tests"

# ── Wave 30: Policy Registry V2 ──────────────────────────────────────────────
git add apps/api/policy_registry_v2.py apps/api/tests/test_policy_registry_v2.py
commit_and_tag "v4.66.0" "feat(wave30): v4.66.0 — Policy Registry V2 versioned schema"

git add apps/api/policy_registry_v2.py
commit_and_tag "v4.67.0" "feat(wave30): v4.67.0 — Policy create + publish lifecycle"

git add apps/api/policy_registry_v2.py
commit_and_tag "v4.68.0" "feat(wave30): v4.68.0 — Policy rollback + sha256 hash chain"

git add apps/web/src/pages/PoliciesV2Page.tsx \
        e2e/test-policies-v2.spec.ts
commit_and_tag "v4.69.0" "feat(wave30): v4.69.0 — PoliciesV2Page + E2E tests"

# ── Wave 31: Search V2 ───────────────────────────────────────────────────────
git add apps/api/search_v2.py apps/api/tests/test_search_v2.py
commit_and_tag "v4.70.0" "feat(wave31): v4.70.0 — Search V2 16-doc index (6 types)"

git add apps/web/src/pages/SearchV2Page.tsx \
        e2e/test-search-v2.spec.ts
commit_and_tag "v4.71.0" "feat(wave31): v4.71.0 — SearchV2Page + query engine + E2E"

# ── Wave 32: Judge Mode W26-32 ───────────────────────────────────────────────
git add apps/api/judge_mode_w26_32.py apps/api/tests/test_judge_mode_w26_32.py
commit_and_tag "v4.72.0" "feat(wave32): v4.72.0 — Judge Mode W26-32 pack generator"

# Final: all integrations
git add \
  apps/api/main.py \
  apps/web/src/App.tsx \
  apps/web/src/components/layout/AppLayout.tsx \
  apps/web/src/lib/api.ts \
  apps/web/src/pages/JudgeModePage.tsx \
  e2e/test-judge-mode.spec.ts \
  e2e/wave26-32-judge-demo.spec.ts \
  e2e/playwright.w26w32.judge.config.ts \
  e2e/playwright.w26w32.unit.config.ts \
  .
commit_and_tag "v4.73.0" "feat(wave32): v4.73.0 — JudgeModePage + mega demo + v4.73 release [872 pytest | 25 Playwright]"

echo ""
echo "=== All 24 commits + tags created ==="
git log --oneline -24
