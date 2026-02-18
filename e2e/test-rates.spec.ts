import { test, expect } from "@playwright/test";

/**
 * Wave 7 E2E — Rates Curve (v3.4)
 * retries=0, workers=1, data-testid selectors only
 */

test("w74-1 – rates page loads via nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("nav-rates").click();
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
});

test("w74-2 – rates page has bootstrap button", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("rates-bootstrap-btn")).toBeVisible();
});

test("w74-3 – bootstrap curve produces table", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bootstrap-btn").click();
  await expect(page.getByTestId("rates-curve-ready")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("rates-curve-table")).toBeVisible();
});

test("w74-4 – curve table has at least 3 rows", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bootstrap-btn").click();
  await expect(page.getByTestId("rates-curve-table")).toBeVisible({ timeout: 10000 });
  const rows = page.getByTestId("rates-curve-table").locator("tbody tr");
  await expect(rows).toHaveCount(6); // 3 deposits + 3 swaps = 6 tenors
});

test("w74-5 – bond price button visible on curve ready", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bootstrap-btn").click();
  await expect(page.getByTestId("rates-curve-ready")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("rates-bond-price-btn")).toBeVisible();
});

test("w74-6 – bond price with curve shows dollar result", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bootstrap-btn").click();
  await expect(page.getByTestId("rates-curve-ready")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bond-price-btn").click();
  await expect(page.getByTestId("rates-bond-price-result")).toBeVisible({ timeout: 8000 });
  const text = await page.getByTestId("rates-bond-price-result").textContent();
  expect(text).toContain("$");
});

test("w74-7 – rates page instruments input is editable", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  const input = page.getByTestId("rates-instruments-input");
  await expect(input).toBeVisible();
  await expect(input).toBeEditable();
});

test("w74-8 – curve hash displayed after bootstrap", async ({ page }) => {
  await page.goto("/rates");
  await expect(page.getByTestId("rates-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("rates-bootstrap-btn").click();
  await expect(page.getByTestId("rates-curve-ready")).toBeVisible({ timeout: 10000 });
  // Hash should be visible as abbreviated hex in panel
  const hashText = await page.getByTestId("rates-curve-ready").textContent();
  expect(hashText).toMatch(/[0-9a-f]{12}/);
});
