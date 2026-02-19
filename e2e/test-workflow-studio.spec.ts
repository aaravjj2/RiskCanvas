import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 29 — Workflow Studio", () => {
  test("navigate to Workflow Studio page", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-workflows").evaluate(el => el.scrollIntoView({ block: "center", behavior: "instant" }));
    await page.getByTestId("nav-workflows").click();
    await expect(page.getByTestId("workflows-page")).toBeVisible({ timeout: 10000 });
  });

  test("generate a workflow", async ({ page }) => {
    await page.goto(`${BASE}/workflows`);
    await expect(page.getByTestId("workflows-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("wf-generate-btn").click();
    await expect(page.getByTestId("wf-current-ready")).toBeVisible({ timeout: 15000 });
  });

  test("activate and simulate a workflow", async ({ page }) => {
    await page.goto(`${BASE}/workflows`);
    await expect(page.getByTestId("workflows-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("wf-generate-btn").click();
    await expect(page.getByTestId("wf-current-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("wf-activate-btn").click();
    await page.waitForTimeout(1000);
    await page.getByTestId("wf-simulate-btn").click();
    await expect(page.getByTestId("wf-sim-ready")).toBeVisible({ timeout: 10000 });
  });
});
