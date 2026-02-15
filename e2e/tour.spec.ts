import { test, expect } from "@playwright/test";

/**
 * RiskCanvas 2-Minute Demo Tour
 * This test performs the complete demo flow and generates a video (TOUR.webm)
 * for the proof pack documentation.
 */

test("complete 2-minute demo flow", async ({ page }) => {
  // 1. Load Dashboard
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
  
  // Take screenshot: Dashboard landing
  await page.screenshot({ path: "../test-results/tour-01-dashboard.png", fullPage: true });
  await page.waitForTimeout(1000);
  
  // 2. Load fixture (auto-loaded, but click button to show interaction)
  await page.getByTestId("load-fixture-button").click();
  await page.waitForTimeout(500);
  
  // 3. Run Risk Analysis
  await page.getByTestId("run-risk-button").click();
  await expect(page.getByTestId("metric-pnl")).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(1000);
  
  // Take screenshot: Analysis Results
  await page.screenshot({ path: "../test-results/tour-02-analysis-results.png", fullPage: true });
  
  // 4. Run Determinism Check
  await page.getByTestId("determinism-button").click();
  await expect(page.getByTestId("determinism-section")).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(1000);
  
  // Take screenshot: Determinism Report
  await page.screenshot({ path: "../test-results/tour-03-determinism.png", fullPage: true });
  
  // 5. Navigate to Portfolio
  await page.getByTestId("nav-portfolio").click();
  await expect(page.getByTestId("portfolio-page")).toBeVisible();
  await expect(page.getByTestId("portfolio-table")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Take screenshot: Portfolio View
  await page.screenshot({ path: "../test-results/tour-04-portfolio.png", fullPage: true });
  
  // 6. Export Portfolio
  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("export-portfolio-button").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain(".json");
  await page.waitForTimeout(500);
  
  // 7. Navigate to Scenarios
  await page.getByTestId("nav-scenarios").click();
  await expect(page.getByTestId("scenarios-page")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Take screenshot: Scenarios
  await page.screenshot({ path: "../test-results/tour-05-scenarios.png", fullPage: true });
  
  // 8. Navigate to Agent
  await page.getByTestId("nav-agent").click();
  await expect(page.getByTestId("agent-page")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Take screenshot: Agent
  await page.screenshot({ path: "../test-results/tour-06-agent.png", fullPage: true });
  
  // 9. Navigate to Reports
  await page.getByTestId("nav-reports").click();
  await expect(page.getByTestId("reports-page")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Take screenshot: Reports
  await page.screenshot({ path: "../test-results/tour-07-reports.png", fullPage: true });
  
  // 10. Navigate to Settings
  await page.getByTestId("nav-settings").click();
  await expect(page.getByTestId("settings-page")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Take screenshot: Settings
  await page.screenshot({ path: "../test-results/tour-08-settings.png", fullPage: true });
  
  // 11. Back to Dashboard
  await page.getByTestId("nav-dashboard").click();
  await expect(page.getByTestId("dashboard-page")).toBeVisible();
  await page.waitForTimeout(1000);
  
  // Final screenshot: Dashboard with full data
  await page.screenshot({ path: "../test-results/tour-09-dashboard-complete.png", fullPage: true });
});
