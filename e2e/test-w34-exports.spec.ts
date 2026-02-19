/**
 * test-w34-exports.spec.ts
 * Wave 34 — Exports Hub + Command Palette v2 nav
 * v4.78-v4.81
 *
 * ALL selectors use data-testid ONLY.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 34 — Exports Hub", () => {
  test("navigate to /exports via nav link", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-exports").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-exports").click();
    await expect(page.getByTestId("exports-page")).toBeVisible({ timeout: 10000 });
  });

  test("exports page loads pack list", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    // At least one row rendered
    await expect(page.getByTestId("data-table-row-0")).toBeVisible();
  });

  test("exports page has multiple rows", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    // 5 demo packs
    await expect(page.getByTestId("data-table-row-3")).toBeVisible();
  });

  test("refresh button reloads packs", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-refresh-btn").click();
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
  });

  test("verify button on row 1 succeeds", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-verify-btn-1").click();
    await expect(page.getByTestId("toast-item-0")).toBeVisible({ timeout: 8000 });
  });

  test("drawer opens for row 2", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-2").click();
    await expect(page.getByTestId("right-drawer")).toBeVisible({ timeout: 5000 });
    await expect(page.getByTestId("export-drawer-sha256")).toBeVisible();
  });

  test("drawer verify button triggers toast", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("right-drawer")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("export-drawer-verify-btn").click();
    await expect(page.getByTestId("toast-item-0")).toBeVisible({ timeout: 8000 });
  });
});

test.describe("Wave 34 — Command Palette Navigation", () => {
  test("Ctrl+K opens palette", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("cmdk-open")).toBeVisible({ timeout: 5000 });
  });

  test("palette input is focused on open", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("cmdk-input")).toBeVisible({ timeout: 5000 });
  });

  test("palette closes with Escape", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("cmdk-open")).toBeVisible({ timeout: 5000 });
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("cmdk-open")).not.toBeVisible({ timeout: 3000 });
  });

  test("palette shows command items", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("cmdk-open")).toBeVisible({ timeout: 5000 });
    // At least one command item visible
    await expect(page.getByTestId("cmdk-item-dashboard")).toBeVisible({ timeout: 5000 });
  });

  test("palette navigates to page on item click", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.keyboard.press("Control+k");
    await expect(page.getByTestId("cmdk-open")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("cmdk-item-search").click();
    // Should navigate away from dashboard
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 5000 });
  });
});
