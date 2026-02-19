import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 28 — Release Readiness", () => {
  test("navigate to Release Readiness page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-readiness").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-readiness").click();
    await expect(page.getByTestId("readiness-page")).toBeVisible({ timeout: 10000 });
  });

  test("evaluate release readiness", async ({ page }) => {
    await page.goto(`${BASE}/readiness`);
    await expect(page.getByTestId("readiness-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("readiness-evaluate-btn").click();
    await expect(page.getByTestId("readiness-result-ready")).toBeVisible({ timeout: 15000 });
  });

  test("export release readiness pack", async ({ page }) => {
    await page.goto(`${BASE}/readiness`);
    await expect(page.getByTestId("readiness-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("readiness-evaluate-btn").click();
    await expect(page.getByTestId("readiness-result-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("readiness-export-btn").click();
    await expect(page.getByTestId("readiness-export-ready")).toBeVisible({ timeout: 10000 });
  });
});
