import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 30 — Policy Registry V2", () => {
  test("navigate to Policies V2 page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-policies-v2").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-policies-v2").click();
    await expect(page.getByTestId("policies-v2-page")).toBeVisible({ timeout: 10000 });
  });

  test("create a new policy", async ({ page }) => {
    await page.goto(`${BASE}/policies-v2`);
    await expect(page.getByTestId("policies-v2-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("pv2-create-btn").click();
    await expect(page.getByTestId("pv2-created-ready")).toBeVisible({ timeout: 15000 });
  });

  test("publish and rollback policy", async ({ page }) => {
    await page.goto(`${BASE}/policies-v2`);
    await expect(page.getByTestId("policies-v2-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("pv2-create-btn").click();
    await expect(page.getByTestId("pv2-created-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("pv2-publish-btn").click();
    await page.waitForTimeout(1000);
    await page.getByTestId("pv2-rollback-btn").click();
    await page.waitForTimeout(1000);
    await expect(page.getByTestId("policies-v2-page")).toBeVisible();
  });

  test("view policy version history", async ({ page }) => {
    await page.goto(`${BASE}/policies-v2`);
    await expect(page.getByTestId("policies-v2-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("pv2-create-btn").click();
    await expect(page.getByTestId("pv2-created-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("pv2-publish-btn").click();
    await page.waitForTimeout(1000);
    await page.getByTestId("pv2-versions-btn").click();
    await expect(page.getByTestId("pv2-versions-ready")).toBeVisible({ timeout: 10000 });
  });
});
