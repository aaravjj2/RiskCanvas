import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

/**
 * v3.2 – Judge Demo Tour
 *
 * This spec is the authoritative judge demo recording spec.
 * - Uses slowMo (configured via playwright.judge.config.ts)
 * - Takes ≥25 screenshots at each tour stop
 * - Records TOUR.webm via video: "on" in playwright.judge.config.ts
 * - Covers all Wave 6 features end-to-end
 *
 * retries: 0, workers: 1, ONLY data-testid selectors
 */

const SCREENSHOT_DIR = path.join(__dirname, "../artifacts/proof/screenshots");

async function snap(page: any, name: string) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `${String(Date.now()).slice(-8)}-${name}.png`),
    fullPage: false,
  });
}

test("judge-demo – tour of all Wave 6 features", async ({ page }) => {
  // ── Stop 1: Dashboard ───────────────────────────────────────────────────────
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15000 });
  await snap(page, "01-dashboard");

  // ── Stop 2: Verify version badge v3.2.0 ────────────────────────────────────
  await expect(page.getByTestId("version-badge")).toContainText("v3.2.0");
  await snap(page, "02-version-badge");

  // ── Stop 3: Platform nav item ───────────────────────────────────────────────
  await expect(page.getByTestId("nav-platform")).toBeVisible();
  await snap(page, "03-nav-platform");

  // ── Stop 4: Navigate to Platform page ──────────────────────────────────────
  await page.getByTestId("nav-platform").click();
  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "04-platform-page");

  // ── Stop 5: Platform health cards ──────────────────────────────────────────
  await expect(page.getByTestId("platform-health-card")).toBeVisible({ timeout: 20000 });
  await expect(page.getByTestId("platform-readiness-card")).toBeVisible();
  await snap(page, "05-platform-health-cards");

  // ── Stop 6: Platform liveness + infra ──────────────────────────────────────
  await expect(page.getByTestId("platform-liveness-card")).toBeVisible();
  await expect(page.getByTestId("platform-infra-card")).toBeVisible();
  await snap(page, "06-platform-infra");

  // ── Stop 7: Port badge 8090 ─────────────────────────────────────────────────
  const portBadge = page.getByTestId("platform-port-badge");
  await expect(portBadge).toBeVisible({ timeout: 15000 });
  await expect(portBadge).toContainText("8090");
  await snap(page, "07-port-badge");

  // ── Stop 8: Navigate to Microsoft wizard ────────────────────────────────────
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "08-microsoft-step1");

  // ── Stop 9: Provider status card ────────────────────────────────────────────
  await expect(page.getByTestId("provider-status-card")).toBeVisible();
  await snap(page, "09-provider-status");

  // ── Stop 10: Advance to MCP Tools (Step 2) ──────────────────────────────────
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 15000 });
  await snap(page, "10-wizard-step2");

  // ── Stop 11: MCP tools list ──────────────────────────────────────────────────
  await expect(page.getByTestId("mcp-tools-list")).toBeVisible({ timeout: 15000 });
  await snap(page, "11-mcp-tools");

  // ── Stop 12: Test MCP call ───────────────────────────────────────────────────
  await page.getByTestId("mcp-test-call-button").click();
  await expect(page.getByTestId("mcp-test-result")).toBeVisible({ timeout: 20000 });
  await snap(page, "12-mcp-test-result");

  // ── Stop 13: Advance to Multi-Agent (Step 3) ────────────────────────────────
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible({ timeout: 15000 });
  await snap(page, "13-wizard-step3");

  // ── Stop 14: Run multi-agent pipeline ───────────────────────────────────────
  await page.getByTestId("multi-agent-run-btn").click();
  await expect(page.getByTestId("audit-log-table")).toBeVisible({ timeout: 40000 });
  await snap(page, "14-audit-log");

  // ── Stop 15: SRE checks ──────────────────────────────────────────────────────
  await expect(page.getByTestId("sre-checks-list")).toBeVisible();
  await snap(page, "15-sre-checks");

  // ── Stop 16: Navigate to DevOps ─────────────────────────────────────────────
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "16-devops-page");

  // ── Stop 17: Policy Gate tab ─────────────────────────────────────────────────
  await page.getByTestId("devops-tab-policy").click();
  await expect(page.getByTestId("devops-panel-policy")).toBeVisible();
  await snap(page, "17-policy-tab");

  // ── Stop 18: Policy evaluate clean diff ─────────────────────────────────────
  const diffInput = page.getByTestId("policy-diff-input");
  await diffInput.fill("+def calculate_risk():\n+    return 0.05\n");
  await snap(page, "18-clean-diff-entered");

  await page.getByTestId("policy-evaluate-btn").click();
  const allowBadge = page.getByTestId("policy-result-badge");
  await expect(allowBadge).toBeVisible({ timeout: 15000 });
  await snap(page, "19-policy-allow");

  // ── Stop 19: Policy evaluate dirty diff ─────────────────────────────────────
  await diffInput.fill('+api_key = "sk-1234567890abcdef"\n+password = "s3cr3t"\n');
  await page.getByTestId("policy-evaluate-btn").click();
  const blockBadge = page.getByTestId("policy-result-badge");
  await expect(blockBadge).toBeVisible({ timeout: 15000 });
  await expect(blockBadge).toContainText("BLOCK");
  await snap(page, "20-policy-block");

  // ── Stop 20: Export markdown ─────────────────────────────────────────────────
  await page.getByTestId("export-markdown-btn").click();
  await expect(page.getByTestId("policy-export-section")).toBeVisible({ timeout: 15000 });
  await snap(page, "21-policy-export-markdown");

  // ── Stop 21: Navigate to Portfolio ──────────────────────────────────────────
  await page.goto("/portfolio");
  await expect(page.getByTestId("portfolio-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "22-portfolio-page");

  // ── Stop 22: Navigate to Agent ────────────────────────────────────────────
  await page.goto("/agent");
  await expect(page.getByTestId("agent-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "23-agent-page");

  // ── Stop 23: Navigate to Jobs ─────────────────────────────────────────────
  await page.goto("/jobs");
  await expect(page.getByTestId("jobs-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "24-jobs-page");

  // ── Stop 24: Navigate back to Platform to close the loop ────────────────────
  await page.getByTestId("nav-platform").click();
  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "25-platform-close-loop");

  // ── Stop 25: Final dashboard ─────────────────────────────────────────────────
  await page.getByTestId("nav-dashboard").click();
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 15000 });
  await snap(page, "26-final-dashboard");
});
