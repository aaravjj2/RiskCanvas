import { test, expect } from "@playwright/test";

test("wave20: Credit Risk page loads, computes risk, exports", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-credit").click();
  await expect(page.getByTestId("credit-page")).toBeVisible({ timeout: 10000 });

  // Load curves
  await page.getByTestId("credit-curves-btn").click();
  await expect(page.getByTestId("credit-curve-ready")).toBeVisible({ timeout: 10000 });

  // Compute risk
  await page.getByTestId("credit-shock-input").fill("100");
  await page.getByTestId("credit-risk-btn").click();
  await expect(page.getByTestId("credit-risk-ready")).toBeVisible({ timeout: 10000 });

  // Export pack
  await page.getByTestId("credit-export-btn").click();
  await expect(page.getByTestId("credit-export-ready")).toBeVisible({ timeout: 10000 });
});
