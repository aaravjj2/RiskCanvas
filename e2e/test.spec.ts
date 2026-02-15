import { test, expect } from "@playwright/test";

/**
 * RiskCanvas E2E Tests - Phase 1 UI Overhaul
 * - retries: 0, workers: 1
 * - ONLY data-testid selectors
 * - Tests against vite preview (production build)
 * - API on port 8090, frontend on 4173
 * - All navigation starts from "/" and uses UI clicks
 */

test("1 – dashboard loads with navigation sidebar", async ({ page }) => {
  await page.goto("/");
  
  // Wait for app to render
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
  
  // Verify sidebar navigation is present
  await expect(page.getByTestId("nav-dashboard")).toBeVisible();
  await expect(page.getByTestId("nav-portfolio")).toBeVisible();
  await expect(page.getByTestId("nav-scenarios")).toBeVisible();
  await expect(page.getByTestId("nav-agent")).toBeVisible();
  await expect(page.getByTestId("nav-reports")).toBeVisible();
  await expect(page.getByTestId("nav-settings")).toBeVisible();
  
  // Verify KPI cards are present
  await expect(page.getByTestId("kpi-portfolio-value")).toBeVisible();
  await expect(page.getByTestId("kpi-var")).toBeVisible();
  await expect(page.getByTestId("kpi-pnl")).toBeVisible();
  await expect(page.getByTestId("kpi-determinism")).toBeVisible();
});

test("2 – run risk analysis shows metrics", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  
  // Dashboard auto-loads fixture on mount, so just click run analysis
  await page.getByTestId("run-risk-button").click();
  
  // Wait for metrics to populate
  await expect(page.getByTestId("metric-pnl")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("metric-value")).toBeVisible();
  await expect(page.getByTestId("metric-var")).toBeVisible();
  
  // Verify metrics show dollar amounts
  const pnlText = await page.getByTestId("metric-pnl").textContent();
  expect(pnlText).toContain("$");
});

test("3 – navigate to portfolio and view positions", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  
  // Navigate to portfolio page via sidebar
  await page.getByTestId("nav-portfolio").click();
  await expect(page.getByTestId("portfolio-page")).toBeVisible();
  
  // Auto-loaded fixture should show positions
  await expect(page.getByTestId("portfolio-section")).toBeVisible();
  await expect(page.getByTestId("portfolio-table")).toBeVisible();
  
  // Verify position data
  await expect(page.getByTestId("table-cell-symbol-0")).toContainText("AAPL");
  await expect(page.getByTestId("table-cell-symbol-1")).toContainText("MSFT");
});

test("4 – export portfolio JSON", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  
  // Navigate to portfolio
  await page.getByTestId("nav-portfolio").click();
  await expect(page.getByTestId("portfolio-page")).toBeVisible();
  
  // Trigger export
  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("export-portfolio-button").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain(".json");
});

test("5 – determinism check displays results", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  
  // Click determinism check button
  await page.getByTestId("determinism-button").click();
  
  // Wait for results
  await expect(page.getByTestId("determinism-section")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("determinism-table")).toBeVisible();
  
  // Verify status is shown
  await expect(page.getByTestId("determinism-status")).toBeVisible();
});

test("6 – navigate all pages successfully", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  
  // Portfolio
  await page.getByTestId("nav-portfolio").click();
  await expect(page.getByTestId("portfolio-page")).toBeVisible();
  
  // Scenarios
  await page.getByTestId("nav-scenarios").click();
  await expect(page.getByTestId("scenarios-page")).toBeVisible();
  
  // Agent
  await page.getByTestId("nav-agent").click();
  await expect(page.getByTestId("agent-page")).toBeVisible();
  
  // Reports
  await page.getByTestId("nav-reports").click();
  await expect(page.getByTestId("reports-page")).toBeVisible();
  
  // Settings
  await page.getByTestId("nav-settings").click();
  await expect(page.getByTestId("settings-page")).toBeVisible();
  
  // Back to Dashboard
  await page.getByTestId("nav-dashboard").click();
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
});
