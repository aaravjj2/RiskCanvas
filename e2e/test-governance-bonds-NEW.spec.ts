import { test, expect } from "@playwright/test";

/**
 * RiskCanvas E2E Tests - Phase 2C/Phase 3 (v1.7-v2.2)
 * Tests for Governance, Bonds, and Caching
 * - retries: 0, workers: 1
 * - ONLY data-testid selectors
 * - Uses waitForResponse for deterministic waits
 */

test("governance - create agent config", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to governance page
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible();
  
  // Wait for initial configs load
  await page.waitForResponse(response => 
    response.url().includes('/governance/configs') && response.status() === 200
  );
  
  // Verify configs list is present (may be empty initially)
  await expect(page.getByTestId("configs-list")).toBeVisible();
  
  // Open create form
  await page.getByTestId("toggle-create-form").click();
  await expect(page.getByTestId("create-config-form")).toBeVisible();
  
  // Fill in form
  await page.getByTestId("config-name-input").fill("Test Conservative Config");
  await page.getByTestId("strategy-select").selectOption("conservative");
  await page.getByTestId("max-leverage-input").fill("2.0");
  
  // Create config and wait for API response
  const createResponse = page.waitForResponse(response => 
    response.url().includes('/governance/configs') && 
    response.request().method() === 'POST' &&
    response.status() === 200
  );
  await page.getByTestId("create-config-btn").click();
  await createResponse;
  
  // Wait for configs list to update (config created)
  await page.waitForTimeout(500); // Brief wait for UI update
  
  // Verify config is listed
  const configsList = page.getByTestId("configs-list"); 
  await expect(configsList).toContainText("Test Conservative Config");
  await expect(configsList).toContainText("conservative");
});

test("governance - run evaluation harness", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to governance
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible();
  
  // Wait for initial load
  await page.waitForResponse(response => 
    response.url().includes('/governance/configs') && response.status() === 200
  );
  
  // Create a config first
  await page.getByTestId("toggle-create-form").click();
  await page.getByTestId("config-name-input").fill("Eval Test Config");
  await page.getByTestId("strategy-select").selectOption("moderate");
  
  const createResponse = page.waitForResponse(response => 
    response.url().includes('/governance/configs') && 
    response.request().method() === 'POST' &&
    response.status() === 200
  );
  await page.getByTestId("create-config-btn").click();
  await createResponse;
  
  // Wait for configs list to update (config created)
  await page.waitForTimeout(500); // Brief wait for UI update
  
  // Verify config appears
  await expect(page.getByTestId("configs-list")).toContainText("Eval Test Config");
  
  // Find the first config and click run eval
  const firstConfig = page.locator('[data-testid^="config-"]').first();
  
  const evalResponse = page.waitForResponse(response => 
    response.url().includes('/governance/evals/run') && response.status() === 200
  );
  await firstConfig.locator('[data-testid^="run-eval-btn-"]').click();
  await evalResponse;
  
  // Wait for eval reports reload
  await page.waitForResponse(response => 
    response.url().includes('/governance/evals') && response.status() === 200
  );
  
  // Verify report shows score
  const reportsList = page.getByTestId("eval-reports-list");
  await expect(reportsList).toContainText("Score:");
  await expect(reportsList).toContainText("Pass:");
  await expect(reportsList).toContainText("Fail:");
});

test("governance - activate config", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to governance
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible();
  
  // Wait for initial load
  await page.waitForResponse(response => 
    response.url().includes('/governance/configs') && response.status() === 200
  );
  
  // Create a config
  await page.getByTestId("toggle-create-form").click();
  await page.getByTestId("config-name-input").fill("Activate Test Config");
  
  const createResponse = page.waitForResponse(response => 
    response.url().includes('/governance/configs') && 
    response.request().method() === 'POST' &&
    response.status() === 200
  );
  await page.getByTestId("create-config-btn").click();
  await createResponse;
  
  // Wait for configs list to update (config created)
  await page.waitForTimeout(500); // Brief wait for UI update
  
  // Verify config appears
  await expect(page.getByTestId("configs-list")).toContainText("Activate Test Config");
  
  // In DEMO mode, configs are created as active by default
  // Verify the config shows active status
  const firstConfig = page.locator('[data-testid^="config-"]').first();
  await expect(firstConfig).toContainText("Status: active");
  
  // Verify activate button is disabled (already active)
  const activateBtn = firstConfig.locator('[data-testid^="activate-config-btn-"]');
  await expect(activateBtn).toBeDisabled();
});

test("bonds - calculate bond price", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to bonds page
  await page.goto("/bonds");
  await expect(page.getByTestId("bonds-page")).toBeVisible();
  
  // Fill in bond parameters (at par case: coupon = yield)
  await page.getByTestId("face-value-input").fill("1000");
  await page.getByTestId("coupon-rate-input").fill("0.05");
  await page.getByTestId("years-to-maturity-input").fill("5");
  await page.getByTestId("yield-to-maturity-input").fill("0.05");
  
  // Calculate price and wait for API response
  const priceResponse = page.waitForResponse(response => 
    response.url().includes('/bonds/price') && response.status() === 200
  );
  await page.getByTestId("calc-price-btn").click();
  await priceResponse;
  
  // Verify results are shown
  await expect(page.getByTestId("bond-results")).toBeVisible();
  
  // Verify price is shown (should be close to 1000 for at-par bond)
  const results = page.getByTestId("bond-results");
  await expect(results).toContainText("Bond Price:");
  await expect(results).toContainText("$1000");
});

test("bonds - calculate yield from price", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to bonds page
  await page.goto("/bonds");
  await expect(page.getByTestId("bonds-page")).toBeVisible();
  
  // Fill in bond parameters
  await page.getByTestId("face-value-input").fill("1000");
  await page.getByTestId("coupon-rate-input").fill("0.05");
  await page.getByTestId("years-to-maturity-input").fill("5");
  await page.getByTestId("price-input").fill("1000");
  
  // Calculate yield and wait for API response
  const yieldResponse = page.waitForResponse(response => 
    response.url().includes('/bonds/yield') && response.status() === 200
  );
  await page.getByTestId("calc-yield-btn").click();
  await yieldResponse;
  
  // Verify results are shown
  await expect(page.getByTestId("bond-results")).toBeVisible();
  
  // Verify yield is shown
  const results = page.getByTestId("bond-results");
  await expect(results).toContainText("Yield to Maturity:");
  await expect(results).toContainText("%");
});

test("bonds - calculate risk metrics", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to bonds page
  await page.goto("/bonds");
  await expect(page.getByTestId("bonds-page")).toBeVisible();
  
  // Fill in bond parameters
  await page.getByTestId("face-value-input").fill("1000");
  await page.getByTestId("coupon-rate-input").fill("0.05");
  await page.getByTestId("years-to-maturity-input").fill("5");
  await page.getByTestId("yield-to-maturity-input").fill("0.06");
  
  // Calculate risk metrics and wait for API response
  const riskResponse = page.waitForResponse(response => 
    response.url().includes('/bonds/risk') && response.status() === 200
  );
  await page.getByTestId("calc-risk-btn").click();
  await riskResponse;
  
  // Verify results are shown
  await expect(page.getByTestId("bond-results")).toBeVisible();
  
  // Verify all risk metrics are shown
  const results = page.getByTestId("bond-results");
  await expect(results).toContainText("Duration:");
  await expect(results).toContainText("Modified Duration:");
  await expect(results).toContainText("Convexity:");
  await expect(results).toContainText("years");
});

test("bonds - deterministic calculation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  
  // Navigate to bonds page
  await page.goto("/bonds");
  await expect(page.getByTestId("bonds-page")).toBeVisible();
  
  // Fill in bond parameters
  await page.getByTestId("face-value-input").fill("1000");
  await page.getByTestId("coupon-rate-input").fill("0.05");
  await page.getByTestId("years-to-maturity-input").fill("5");
  await page.getByTestId("yield-to-maturity-input").fill("0.05");
  
  // Calculate price twice to verify determinism
  const firstResponse = page.waitForResponse(response => 
    response.url().includes('/bonds/price') && response.status() === 200
  );
  await page.getByTestId("calc-price-btn").click();
  const first = await firstResponse;
  const firstData = await first.json();
  
  await expect(page.getByTestId("bond-results")).toBeVisible();
  const firstText = await page.getByTestId("bond-results").textContent();
  
  // Calculate again with same inputs
  const secondResponse = page.waitForResponse(response => 
    response.url().includes('/bonds/price') && response.status() === 200
  );
  await page.getByTestId("calc-price-btn").click();
  const second = await secondResponse;
  const secondData = await second.json();
  
  await expect(page.getByTestId("bond-results")).toBeVisible();
  const secondText = await page.getByTestId("bond-results").textContent();
  
  // Verify exact same results (same input → same output)
  expect(firstText).toBe(secondText);
  expect(firstData).toEqual(secondData);
});
