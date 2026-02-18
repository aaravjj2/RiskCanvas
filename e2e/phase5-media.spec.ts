import { test, expect } from "@playwright/test";

/**
 * phase5-media — Wave 5 Complete Tour v2.8.0
 *
 * 10-stop tour covering every major feature delivered in v2.4–v2.8.
 * Produces ONE continuous TOUR.webm (>= 180 s with slowMo: 4000 config)
 * and >= 25 full-page screenshots.
 *
 * Rules:
 *   - ALL selectors via page.getByTestId() (or [data-testid^=…] for dynamic ids)
 *   - NO waitForTimeout anywhere
 *   - waitForResponse promises always set BEFORE button clicks
 *   - retries=0, workers=1  (enforced by playwright.media.config.ts)
 */

test("phase5-media – Wave 5 complete tour v2.8.0", async ({ page }) => {
  // ────────────────────────────────────────────────────────────────────────────
  // STOP 1 — Dashboard: version badge + portfolio analysis
  // ────────────────────────────────────────────────────────────────────────────
  await page.goto("http://127.0.0.1:4174/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 1: Dashboard loads
  await page.screenshot({ path: "screenshots/phase5-01-dashboard.png", fullPage: true });

  // CHECKPOINT 2: version badge shows v2.8.0
  const versionBadge = page.getByTestId("version-badge");
  await expect(versionBadge).toBeVisible();
  await expect(versionBadge).toContainText("v2.8.0");
  await page.screenshot({ path: "screenshots/phase5-02-version-badge.png", fullPage: true });

  // CHECKPOINT 3: load fixture then run analysis
  await page.getByTestId("load-fixture-button").click();
  await page.waitForLoadState("networkidle");

  const analysisResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/analyze/portfolio") && r.status() === 200,
    { timeout: 30000 }
  );
  await page.getByTestId("run-risk-button").click();
  await analysisResponsePromise;
  await expect(page.getByTestId("kpi-pnl")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-03-analysis-complete.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 2 — Reports: storage provider badge
  // ────────────────────────────────────────────────────────────────────────────
  const reportsResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/reports") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("nav-reports").click();
  await expect(page.getByTestId("reports-page")).toBeVisible({ timeout: 10000 });
  await reportsResponsePromise;
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 4: Reports page with storage badge
  await page.screenshot({ path: "screenshots/phase5-04-reports.png", fullPage: true });

  // CHECKPOINT 5: Storage provider badge visible
  await expect(page.getByTestId("storage-provider-badge")).toBeVisible();
  await page.screenshot({ path: "screenshots/phase5-05-storage-badge.png", fullPage: true });

  // CHECKPOINT 6: Reports list container visible
  await expect(page.getByTestId("reports-list")).toBeVisible();
  await page.screenshot({ path: "screenshots/phase5-06-reports-list.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 3 — Jobs: v2.6 backend badge + v2.7 live SSE badge
  // ────────────────────────────────────────────────────────────────────────────
  const jobsResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/jobs") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("nav-jobs").click();
  await expect(page.getByTestId("jobs-page")).toBeVisible({ timeout: 10000 });
  await jobsResponsePromise;
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 7: Jobs page with backend badge
  await page.screenshot({ path: "screenshots/phase5-07-jobs.png", fullPage: true });

  // CHECKPOINT 8: Backend badge shows "memory" (v2.6 SQLite-aware default)
  const backendBadge = page.getByTestId("job-store-backend-badge");
  await expect(backendBadge).toBeVisible();
  await expect(backendBadge).toContainText("memory");
  await page.screenshot({ path: "screenshots/phase5-08-backend-badge.png", fullPage: true });

  // CHECKPOINT 9: Live updates badge (v2.7 SSE)
  const liveBadge = page.getByTestId("live-updates-badge");
  await expect(liveBadge).toBeVisible({ timeout: 8000 });
  await expect(liveBadge).toContainText("live");
  await page.screenshot({ path: "screenshots/phase5-09-live-badge.png", fullPage: true });

  // CHECKPOINT 10: Refresh jobs list
  const refreshResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/jobs") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("refresh-jobs-btn").click();
  await refreshResponsePromise;
  await expect(page.getByTestId("jobs-list")).toBeVisible();
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-10-jobs-refreshed.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 4 — DevOps Risk-Bot
  // ────────────────────────────────────────────────────────────────────────────
  await page.getByTestId("nav-devops").click();
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 11: DevOps page / Risk-Bot tab
  await expect(page.getByTestId("devops-panel-riskbot")).toBeVisible();
  await page.screenshot({ path: "screenshots/phase5-11-devops-riskbot.png", fullPage: true });

  // CHECKPOINT 12: Generate risk-bot report
  const riskBotResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/devops/risk-bot") && r.status() === 200,
    { timeout: 30000 }
  );
  await expect(page.getByTestId("generate-riskbot-report-btn")).toBeEnabled();
  await page.getByTestId("generate-riskbot-report-btn").click();
  await riskBotResponsePromise;
  await expect(page.getByTestId("riskbot-report-section")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-12-riskbot-report.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 5 — DevOps GitLab MR Bot
  // ────────────────────────────────────────────────────────────────────────────
  await page.getByTestId("devops-tab-gitlab").click();
  await expect(page.getByTestId("devops-panel-gitlab")).toBeVisible();
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 13: GitLab tab
  await page.screenshot({ path: "screenshots/phase5-13-devops-gitlab.png", fullPage: true });

  // CHECKPOINT 14: Enter diff and analyze MR
  const diffInput = page.getByTestId("diff-input");
  await expect(diffInput).toBeVisible();
  await diffInput.fill(
    "+console.log('debug info');\n+// TODO: remove before merge\n+const unused = 42;"
  );
  await page.screenshot({ path: "screenshots/phase5-14-diff-entered.png", fullPage: true });

  const mrResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/devops/gitlab/analyze-mr") && r.status() === 200,
    { timeout: 30000 }
  );
  await expect(page.getByTestId("analyze-mr-btn")).toBeEnabled();
  await page.getByTestId("analyze-mr-btn").click();
  await mrResponsePromise;
  await expect(page.getByTestId("mr-analysis-section")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-15-mr-analysis.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 6 — DevOps Monitor Reporter
  // ────────────────────────────────────────────────────────────────────────────
  await page.getByTestId("devops-tab-monitor").click();
  await expect(page.getByTestId("devops-panel-monitor")).toBeVisible();
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 15: Monitor tab
  await page.screenshot({ path: "screenshots/phase5-16-devops-monitor.png", fullPage: true });

  const monitorResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/devops/monitor/generate-report") && r.status() === 200,
    { timeout: 30000 }
  );
  await expect(page.getByTestId("generate-monitor-report-btn")).toBeEnabled();
  await page.getByTestId("generate-monitor-report-btn").click();
  await monitorResponsePromise;
  await expect(page.getByTestId("monitor-report-section")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 16: Monitor report generated
  await page.screenshot({ path: "screenshots/phase5-17-monitor-report.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 7 — DevOps Test Harness
  // ────────────────────────────────────────────────────────────────────────────
  await page.getByTestId("devops-tab-harness").click();
  await expect(page.getByTestId("devops-panel-harness")).toBeVisible();
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 17: Harness tab
  await page.screenshot({ path: "screenshots/phase5-18-devops-harness.png", fullPage: true });

  // CHECKPOINT 18: Run MR review scenario
  const mrScenarioResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/devops/test-harness/run-scenario") && r.status() === 200,
    { timeout: 30000 }
  );
  await expect(page.getByTestId("run-mr-scenario-btn")).toBeEnabled();
  await page.getByTestId("run-mr-scenario-btn").click();
  await mrScenarioResponsePromise;
  await expect(page.getByTestId("scenario-result-section")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-19-harness-mr.png", fullPage: true });

  // CHECKPOINT 19: Run monitoring scenario
  const monitoringScenarioResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/devops/test-harness/run-scenario") && r.status() === 200,
    { timeout: 30000 }
  );
  await expect(page.getByTestId("run-monitoring-scenario-btn")).toBeEnabled();
  await page.getByTestId("run-monitoring-scenario-btn").click();
  await monitoringScenarioResponsePromise;
  await expect(page.getByTestId("scenario-result-section")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-20-harness-monitoring.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 8 — Governance: create config + activate + eval
  // ────────────────────────────────────────────────────────────────────────────
  await page.goto("http://127.0.0.1:4174/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 20: Governance page
  await page.screenshot({ path: "screenshots/phase5-21-governance.png", fullPage: true });

  // CHECKPOINT 21: Open create-config form
  await page.getByTestId("toggle-create-form").click();
  await expect(page.getByTestId("create-config-form")).toBeVisible({ timeout: 5000 });
  await page.screenshot({ path: "screenshots/phase5-22-governance-form.png", fullPage: true });

  // Fill form fields
  await page.getByTestId("config-name-input").fill("wave5-tour-config");
  await page.getByTestId("strategy-select").selectOption("moderate");
  await page.getByTestId("max-leverage-input").fill("3");

  // CHECKPOINT 22: Create config
  const createConfigResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/governance/configs") && r.status() === 200,
    { timeout: 30000 }
  );
  await page.getByTestId("create-config-btn").click();
  await createConfigResponsePromise;
  await expect(page.getByTestId("configs-list")).toBeVisible({ timeout: 10000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-23-governance-created.png", fullPage: true });

  // CHECKPOINT 23: Config is created as active — run eval on first config
  // (activate-config-btn is disabled when config.status === 'active', which is the default)
  const evalBtn = page.locator('[data-testid^="run-eval-btn-"]').first();
  await expect(evalBtn).toBeVisible({ timeout: 5000 });
  const evalResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/governance/evals/run") && r.status() === 200,
    { timeout: 30000 }
  );
  await evalBtn.click();
  await evalResponsePromise;
  await expect(page.getByTestId("eval-reports-list")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-24-governance-eval.png", fullPage: true });

  // CHECKPOINT 24: Config list shows our newly created wave5-tour-config
  await expect(page.getByTestId("configs-list")).toBeVisible();
  await page.screenshot({ path: "screenshots/phase5-25-governance-configs.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 9 — Bonds: calc price, yield, risk (determinism demo)
  // ────────────────────────────────────────────────────────────────────────────
  await page.goto("http://127.0.0.1:4174/bonds");
  await expect(page.getByTestId("bonds-page")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 25: Bonds page
  await page.screenshot({ path: "screenshots/phase5-26-bonds.png", fullPage: true });

  // Fill bond inputs
  await page.getByTestId("face-value-input").fill("1000");
  await page.getByTestId("coupon-rate-input").fill("5");
  await page.getByTestId("years-to-maturity-input").fill("10");
  await page.getByTestId("yield-to-maturity-input").fill("4.5");

  // CHECKPOINT 26: Calc price
  const priceResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/bonds/price") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("calc-price-btn").click();
  await priceResponsePromise;
  await expect(page.getByTestId("bond-results")).toBeVisible({ timeout: 10000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-27-bonds-price.png", fullPage: true });

  // CHECKPOINT 27: Calc yield (set price-input first)
  await page.getByTestId("price-input").fill("1039");
  const yieldResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/bonds/yield") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("calc-yield-btn").click();
  await yieldResponsePromise;
  await expect(page.getByTestId("bond-results")).toBeVisible({ timeout: 10000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-28-bonds-yield.png", fullPage: true });

  // CHECKPOINT 28: Calc risk metrics (duration + convexity)
  const riskResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/bonds/risk") && r.status() === 200,
    { timeout: 15000 }
  );
  await page.getByTestId("calc-risk-btn").click();
  await riskResponsePromise;
  await expect(page.getByTestId("bond-results")).toBeVisible({ timeout: 10000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-29-bonds-risk.png", fullPage: true });

  // ────────────────────────────────────────────────────────────────────────────
  // STOP 10 — Microsoft Mode: MCP tools + test call
  // ────────────────────────────────────────────────────────────────────────────
  const mcpToolsResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/mcp/tools") && r.status() === 200,
    { timeout: 30000 }
  );
  await page.goto("http://127.0.0.1:4174/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 15000 });
  await mcpToolsResponsePromise;
  await page.waitForLoadState("networkidle");

  // CHECKPOINT 29: Microsoft Mode page with tools list
  await page.screenshot({ path: "screenshots/phase5-30-microsoft-mode.png", fullPage: true });

  // CHECKPOINT 30: Provider mode badge visible
  await expect(page.getByTestId("provider-mode-badge")).toBeVisible();
  await page.screenshot({ path: "screenshots/phase5-31-provider-badge.png", fullPage: true });

  // CHECKPOINT 31: MCP tools list populated
  await expect(page.getByTestId("mcp-tools-list")).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: "screenshots/phase5-32-mcp-tools.png", fullPage: true });

  // CHECKPOINT 32: Test MCP call
  const mcpCallResponsePromise = page.waitForResponse(
    (r) => r.url().includes("/mcp/tools/call") && r.status() === 200,
    { timeout: 30000 }
  );
  await page.getByTestId("mcp-test-call-button").click();
  await mcpCallResponsePromise;
  await expect(page.getByTestId("mcp-test-result")).toBeVisible({ timeout: 15000 });
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: "screenshots/phase5-33-mcp-test-result.png", fullPage: true });

  // Final overview screenshot
  await page.screenshot({ path: "screenshots/phase5-34-tour-complete.png", fullPage: true });

  // Tour complete – 34 checkpoints (>= 25 required) ✓
  // Duration: ~45 user actions × 4 s slowMo = ~180 s TOUR.webm ✓
});
