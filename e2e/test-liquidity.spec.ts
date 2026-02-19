import { test, expect } from "@playwright/test";

test("wave21: Liquidity page computes haircuts, t-costs, tradeoff, exports", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-liquidity").click();
  await expect(page.getByTestId("liq-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("liq-haircut-btn").click();
  await expect(page.getByTestId("liq-ready")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("liq-tcost-btn").click();
  await expect(page.getByTestId("liq-ready")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("liq-export-btn").click();
  await expect(page.getByTestId("liq-export-ready")).toBeVisible({ timeout: 10000 });
});
