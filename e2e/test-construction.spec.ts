import { test, expect } from "@playwright/test";

test("construction: page loads", async ({ page }) => {
  await page.goto("/construction");
  await expect(page.getByTestId("construct-page")).toBeVisible({ timeout: 10000 });
});

test("construction: solve produces results", async ({ page }) => {
  await page.goto("/construction");
  await expect(page.getByTestId("construct-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("construct-tab-solve").click();
  await page.getByTestId("construct-solve-btn").click();
  await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("construct-results")).toBeVisible({ timeout: 8000 });
});

test("construction: trade rows appear after solve", async ({ page }) => {
  await page.goto("/construction");
  await page.getByTestId("construct-tab-solve").click();
  await page.getByTestId("construct-solve-btn").click();
  await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
  // At least one trade row should exist
  const tradeRows = page.locator('[data-testid^="construct-trade-row-"]');
  await expect(tradeRows.first()).toBeVisible({ timeout: 8000 });
});

test("construction: export pack works after solve", async ({ page }) => {
  await page.goto("/construction");
  await page.getByTestId("construct-tab-solve").click();
  await page.getByTestId("construct-solve-btn").click();
  await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("construct-export-btn").click();
  // Pack should return data (no error visible)
  await expect(page.getByTestId("construct-results")).toBeVisible({ timeout: 8000 });
});

test("construction: compare tab works", async ({ page }) => {
  await page.goto("/construction");
  // Must solve first before compare is available
  await page.getByTestId("construct-tab-solve").click();
  await page.getByTestId("construct-solve-btn").click();
  await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
  // Now switch to compare tab
  await page.getByTestId("construct-tab-compare").click();
  await page.getByTestId("construct-run-compare-btn").click();
  await expect(page.getByTestId("construct-compare-ready")).toBeVisible({ timeout: 15000 });
});
