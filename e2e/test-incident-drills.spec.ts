import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 27 — Incident Drills", () => {
  test("navigate to Incident Drills page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-incidents").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-incidents").click();
    await expect(page.getByTestId("incidents-page")).toBeVisible({ timeout: 10000 });
  });

  test("run api_latency_spike drill", async ({ page }) => {
    await page.goto(`${BASE}/incidents`);
    await expect(page.getByTestId("incidents-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("drill-run-btn").click();
    await expect(page.getByTestId("drill-run-ready")).toBeVisible({ timeout: 15000 });
  });

  test("export incident drill pack", async ({ page }) => {
    await page.goto(`${BASE}/incidents`);
    await expect(page.getByTestId("incidents-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("drill-run-btn").click();
    await expect(page.getByTestId("drill-run-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("drill-export-btn").click();
    await expect(page.getByTestId("drill-export-ready")).toBeVisible({ timeout: 10000 });
  });
});
