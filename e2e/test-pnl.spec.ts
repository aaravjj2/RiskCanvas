import { test, expect } from "@playwright/test";

test("pnl-attribution: page loads and compute works", async ({ page }) => {
  await page.goto("/pnl");
  await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 10000 });
});

test("pnl-attribution: compute attribution and verify results", async ({ page }) => {
  await page.goto("/pnl");
  await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("pnl-compute-btn").click();
  await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
  // Expect at least one factor row (spot is always present)
  await expect(page.getByTestId("pnl-row-spot")).toBeVisible({ timeout: 8000 });
});

test("pnl-attribution: presets load", async ({ page }) => {
  await page.goto("/pnl");
  await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("pnl-presets-btn").click();
  await expect(page.getByTestId("pnl-presets-ready")).toBeVisible({ timeout: 10000 });
});

test("pnl-attribution: export MD works after compute", async ({ page }) => {
  await page.goto("/pnl");
  await page.getByTestId("pnl-compute-btn").click();
  await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("pnl-export-md").click();
  await expect(page.getByTestId("pnl-export-md-preview")).toBeVisible({ timeout: 8000 });
});

test("pnl-attribution: export pack works after compute", async ({ page }) => {
  await page.goto("/pnl");
  await page.getByTestId("pnl-compute-btn").click();
  await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("pnl-export-pack").click();
  await expect(page.getByTestId("pnl-export-ready")).toBeVisible({ timeout: 10000 });
});
