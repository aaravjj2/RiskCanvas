import { test, expect } from "@playwright/test";

test("home shows RiskCanvas title (data-testid only)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("title")).toHaveText("RiskCanvas");
});
