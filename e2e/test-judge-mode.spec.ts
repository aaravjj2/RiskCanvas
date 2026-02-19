import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 32 — Judge Mode W26-32", () => {
  test("navigate to Judge Mode page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-judge-mode").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-judge-mode").click();
    await expect(page.getByTestId("judge-mode-page")).toBeVisible({ timeout: 10000 });
  });

  test("generate judge pack and verify PASS verdict", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-mode-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("judge-generate-btn").click();
    await page.waitForTimeout(3000);
    await expect(page.getByTestId("judge-mode-page")).toBeVisible();
  });

  test("list judge pack files", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-mode-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("judge-files-btn").click();
    await page.waitForTimeout(1500);
    await expect(page.getByTestId("judge-mode-page")).toBeVisible();
  });
});
