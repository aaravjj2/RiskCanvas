import { test, expect } from "@playwright/test";

/**
 * Phase 10 Judge Demo – Wave 9 + Wave 10 (v3.7 → v4.0)
 *
 * This spec produces ≥25 annotated screenshots documenting the full
 * end-to-end tour of all Wave 9+10 features.
 *
 * retries: 0, workers: 1, ONLY data-testid selectors, no waitForTimeout
 */

const SHOT = (page: any, name: string) =>
  page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: false });

test("phase10 judge demo – full Wave 9+10 tour", async ({ page }) => {
  // ── 01: App loads with v4.0.0 version badge ──────────────────────────────
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("version-badge")).toHaveText("v4.0.0");
  await SHOT(page, "01-app-v4-badge");

  // ── 02: Navigate sidebar shows SRE entry ─────────────────────────────────
  await expect(page.getByTestId("nav-sre")).toBeVisible();
  await SHOT(page, "02-sidebar-nav-sre");

  // ── 03: Navigate to Governance page ──────────────────────────────────────
  await page.getByTestId("nav-governance").click();
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "03-governance-page");

  // ── 04: Governance Policy tab ────────────────────────────────────────────
  await page.getByTestId("gov-tab-policy").click();
  await expect(page.getByTestId("gov-validate-btn")).toBeVisible({ timeout: 5000 });
  await SHOT(page, "04-gov-policy-tab");

  // ── 05: Evaluate policy – ALLOW decision ─────────────────────────────────
  await page.getByTestId("gov-validate-btn").click();
  await expect(page.getByTestId("gov-policy-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "05-gov-policy-allow");

  // ── 06: Policy block – too many tool calls ────────────────────────────────
  await page.getByTestId("gov-calls-input").fill("999");
  await page.getByTestId("gov-validate-btn").click();
  await expect(page.getByTestId("gov-validate-result")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "06-gov-policy-block-budget");

  // ── 07: Narrative validator tab ───────────────────────────────────────────
  await page.getByTestId("gov-tab-narrative").click();
  await expect(page.getByTestId("gov-validate-narrative-btn")).toBeVisible({ timeout: 5000 });
  await SHOT(page, "07-gov-narrative-tab");

  // ── 08: Validate valid narrative ─────────────────────────────────────────
  await page.getByTestId("gov-narrative-text").fill(
    "The portfolio value is 18250.75 USD."
  );
  await page.getByTestId("gov-computed-json").fill(
    '{"portfolio_value": 18250.75}'
  );
  await page.getByTestId("gov-validate-narrative-btn").click();
  await expect(page.getByTestId("gov-narrative-badge")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "08-gov-narrative-valid");

  // ── 09: Validate invalid narrative ───────────────────────────────────────
  await page.getByTestId("gov-narrative-text").fill(
    "The portfolio value is 99999.00 USD."
  );
  await page.getByTestId("gov-validate-narrative-btn").click();
  await expect(page.getByTestId("gov-narrative-badge")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "09-gov-narrative-invalid");

  // ── 10: Eval Suites tab ───────────────────────────────────────────────────
  await page.getByTestId("gov-tab-suites").click();
  await page.getByTestId("gov-load-suites-btn").click();
  await expect(page.getByTestId("eval-suites-list")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "10-gov-eval-suites-list");

  // ── 11: Run governance policy suite ──────────────────────────────────────
  await page.getByTestId("eval-run-btn-governance_policy_suite").click();
  await expect(page.getByTestId("eval-scorecard-ready")).toBeVisible({ timeout: 20000 });
  await SHOT(page, "11-gov-eval-scorecard");

  // ── 12: Scorecard export MD button ───────────────────────────────────────
  await expect(page.getByTestId("eval-export-md")).toBeVisible();
  await SHOT(page, "12-gov-eval-export-md");

  // ── 13: Run rates curve suite ─────────────────────────────────────────────
  await page.getByTestId("eval-run-btn-rates_curve_suite").click();
  await expect(page.getByTestId("eval-scorecard-ready")).toBeVisible({ timeout: 20000 });
  await SHOT(page, "13-gov-eval-rates-suite");

  // ── 14: Navigate to DevOps ────────────────────────────────────────────────
  await page.getByTestId("nav-devops").click();
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "14-devops-page");

  // ── 15: MR Review tab ────────────────────────────────────────────────────
  await page.getByTestId("devops-tab-mr").click();
  await expect(page.getByTestId("devops-mr-generate")).toBeVisible({ timeout: 5000 });
  await SHOT(page, "15-devops-mr-tab");

  // ── 16: MR Review with clean diff – ALLOW ────────────────────────────────
  await page.getByTestId("devops-mr-diff-input").fill(
    "+def calculate_var(portfolio):\n+    return portfolio * 0.05\n"
  );
  await page.getByTestId("devops-mr-generate").click();
  await expect(page.getByTestId("devops-mr-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "16-devops-mr-allow");

  // ── 17: MR Review with secret diff – BLOCK ───────────────────────────────
  await page.getByTestId("devops-mr-diff-input").fill(
    "+OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef1234567890\n"
  );
  await page.getByTestId("devops-mr-generate").click();
  await expect(page.getByTestId("devops-mr-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "17-devops-mr-block-secret");

  // ── 18: Pipeline Analyzer tab ─────────────────────────────────────────────
  await page.getByTestId("devops-tab-pipeline").click();
  await expect(page.getByTestId("devops-pipe-analyze")).toBeVisible({ timeout: 5000 });
  await SHOT(page, "18-devops-pipeline-tab");

  // ── 19: Pipeline OOM detection ────────────────────────────────────────────
  await page.getByTestId("devops-pipe-log-input").fill(
    "ERROR: Java heap space\nkilled\nfatal: out of memory\n"
  );
  await page.getByTestId("devops-pipe-analyze").click();
  await expect(page.getByTestId("devops-pipe-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "19-devops-pipeline-oom");

  // ── 20: Pipeline clean log ────────────────────────────────────────────────
  await page.getByTestId("devops-pipe-log-input").fill("All steps succeeded.\nPipeline complete.\n");
  await page.getByTestId("devops-pipe-analyze").click();
  await expect(page.getByTestId("devops-pipe-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "20-devops-pipeline-clean");

  // ── 21: Artifacts build tab ───────────────────────────────────────────────
  await page.getByTestId("devops-tab-artifacts").click();
  await expect(page.getByTestId("devops-artifacts-build")).toBeVisible({ timeout: 5000 });
  await page.getByTestId("devops-artifacts-build").click();
  await expect(page.getByTestId("devops-artifacts-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "21-devops-artifacts-ready");

  // ── 22: Download pack button visible ─────────────────────────────────────
  await expect(page.getByTestId("devops-download-pack")).toBeVisible();
  await SHOT(page, "22-devops-artifacts-download");

  // ── 23: Navigate to SRE page ──────────────────────────────────────────────
  await page.getByTestId("nav-sre").click();
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await SHOT(page, "23-sre-page");

  // ── 24: Generate empty SRE playbook ──────────────────────────────────────
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "24-sre-playbook-empty");

  // ── 25: SRE playbook – policy blocked incident ───────────────────────────
  await page.getByTestId("sre-param-policy-blocked").check();
  await page.getByTestId("sre-param-fatals").fill("2");
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "25-sre-playbook-incident");

  // ── 26: SRE steps list visible ────────────────────────────────────────────
  await expect(page.getByTestId("sre-steps-list")).toBeVisible();
  await SHOT(page, "26-sre-steps-list");

  // ── 27: SRE export MD button ─────────────────────────────────────────────
  await expect(page.getByTestId("sre-export-md")).toBeVisible();
  await SHOT(page, "27-sre-export-md");

  // ── 28: SRE with degraded services ────────────────────────────────────────
  await page.getByTestId("sre-param-services").fill("order-api, auth-svc, db-replica");
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  await SHOT(page, "28-sre-degraded-services");
});
