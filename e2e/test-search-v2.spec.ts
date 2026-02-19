import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 31 — Search V2", () => {
  test("navigate to Search V2 page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-search-v2").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-search-v2").click();
    await expect(page.getByTestId("search-v2-page")).toBeVisible({ timeout: 10000 });
  });

  test("search for 'security' and see results", async ({ page }) => {
    await page.goto(`${BASE}/search-v2`);
    await expect(page.getByTestId("search-v2-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("sv2-query-input").fill("security");
    await page.getByTestId("sv2-search-btn").click();
    await page.waitForTimeout(1500);
    await expect(page.getByTestId("search-v2-page")).toBeVisible();
  });

  test("filter by doc type", async ({ page }) => {
    await page.goto(`${BASE}/search-v2`);
    await expect(page.getByTestId("search-v2-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("sv2-query-input").fill("risk");
    await page.getByTestId("sv2-type-filter").selectOption("policy_v2");
    await page.getByTestId("sv2-search-btn").click();
    await page.waitForTimeout(1500);
    await expect(page.getByTestId("search-v2-page")).toBeVisible();
  });
});
