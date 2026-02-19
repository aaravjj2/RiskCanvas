import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 26 — Agentic MR Review", () => {
  test("navigate to MR Review page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-mr-review").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-mr-review").click();
    await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
  });

  test("plan a review for MR-101", async ({ page }) => {
    await page.goto(`${BASE}/mr-review`);
    await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("mr-plan-btn").click();
    await expect(page.getByTestId("mr-plan-ready")).toBeVisible({ timeout: 15000 });
  });

  test("run the review after planning", async ({ page }) => {
    await page.goto(`${BASE}/mr-review`);
    await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("mr-plan-btn").click();
    await expect(page.getByTestId("mr-plan-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("mr-run-btn").click();
    await expect(page.getByTestId("mr-review-ready")).toBeVisible({ timeout: 15000 });
  });

  test("preview and post comments", async ({ page }) => {
    await page.goto(`${BASE}/mr-review`);
    await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("mr-plan-btn").click();
    await expect(page.getByTestId("mr-plan-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("mr-run-btn").click();
    await expect(page.getByTestId("mr-review-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("mr-preview-btn").click();
    await expect(page.getByTestId("mr-comments-ready")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("mr-post-btn").click();
    await page.waitForTimeout(1000);
    await expect(page.getByTestId("mr-review-page")).toBeVisible();
  });

  test("export MR review pack", async ({ page }) => {
    await page.goto(`${BASE}/mr-review`);
    await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("mr-plan-btn").click();
    await expect(page.getByTestId("mr-plan-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("mr-run-btn").click();
    await expect(page.getByTestId("mr-review-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("mr-export-btn").click();
    await expect(page.getByTestId("mr-export-ready")).toBeVisible({ timeout: 10000 });
  });
});
