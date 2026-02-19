import { test, expect } from "@playwright/test";

test("wave19: FX Risk page loads and computes exposure", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-fx").click();
  await expect(page.getByTestId("fx-page")).toBeVisible({ timeout: 10000 });

  // Load spot rates
  await page.getByTestId("fx-spot-btn").click();
  await expect(page.getByTestId("fx-spot-ready")).toBeVisible({ timeout: 10000 });

  // Compute exposure
  await page.getByTestId("fx-exposure-btn").click();
  await expect(page.getByTestId("fx-exposure-ready")).toBeVisible({ timeout: 10000 });

  // Apply shocks
  await page.getByTestId("fx-shock-btn").click();
  await expect(page.getByTestId("fx-shock-ready")).toBeVisible({ timeout: 10000 });

  // Export pack
  await page.getByTestId("fx-export-btn").click();
  await expect(page.getByTestId("fx-export-ready")).toBeVisible({ timeout: 10000 });
});
