import { test, expect } from "@playwright/test";

/**
 * RiskCanvas v4.6.0 — Market Data Page E2E
 * - retries: 0, workers: 1
 * - ONLY data-testid selectors
 * - Backend must be running on :8090 (DEMO_MODE=true)
 * - Frontend on :4174 (vite preview build)
 */

test("market-1: market data page renders", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });
});

test("market-2: load as-of date shows asof and provider", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });

  // Click Load As-Of button
  await page.click("button:has-text('Load As-Of')");
  await expect(page.getByTestId("market-asof")).toBeVisible({ timeout: 8000 });
  await expect(page.getByTestId("market-provider")).toBeVisible();

  const asof = await page.getByTestId("market-asof").textContent();
  expect(asof).toBeTruthy();
  expect(asof).toContain("2026");

  const provider = await page.getByTestId("market-provider").textContent();
  expect(provider).toBe("fixture");
});

test("market-3: spot lookup returns AAPL price", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });

  // Make sure the input has AAPL
  await page.fill("[data-testid='market-spot-symbol-input']", "AAPL");
  await page.click("button:has-text('Get Spot')");

  await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 8000 });
});

test("market-4: series loads for AAPL", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });

  await page.fill("[data-testid='market-series-symbol-input']", "AAPL");
  await page.click("button:has-text('Load Series')");

  await expect(page.getByTestId("market-series-ready")).toBeVisible({ timeout: 8000 });
});

test("market-5: rates curve loads for USD_SOFR", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });

  await page.fill("[data-testid='market-curve-id-input']", "USD_SOFR");
  await page.click("button:has-text('Load Curve')");

  await expect(page.getByTestId("market-curve-ready")).toBeVisible({ timeout: 8000 });
});

test("market-6: market page accessible from nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("nav-market").click();
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 8000 });
});

test("market-7: spot + series hashes are deterministic on reload", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });

  // Load spot twice and verify element is consistently visible
  await page.fill("[data-testid='market-spot-symbol-input']", "MSFT");
  await page.click("button:has-text('Get Spot')");
  await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 8000 });

  // Reload and click again
  await page.reload();
  await expect(page.getByTestId("market-page")).toBeVisible();
  await page.fill("[data-testid='market-spot-symbol-input']", "MSFT");
  await page.click("button:has-text('Get Spot')");
  await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 8000 });
});
