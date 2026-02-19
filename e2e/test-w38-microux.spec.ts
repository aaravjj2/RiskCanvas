/**
 * test-w38-microux.spec.ts
 * Wave 38 — Micro-interactions: copy buttons, bulk actions, version badge
 * v4.94-v4.95
 *
 * ALL selectors use data-testid ONLY.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 38 — Inline Copy", () => {
  test("workbench copy-hash-btn exists", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-copy-hash-btn")).toBeVisible({ timeout: 5000 });
  });

  test("copy-hash triggers success toast", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await page.getByTestId("workbench-copy-hash-btn").click();
    await expect(page.getByTestId("toast-item-0")).toBeVisible({ timeout: 5000 });
  });

  test("version-badge shows v4.97.0", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("version-badge")).toBeVisible({ timeout: 10000 });
    const version = await page.getByTestId("version-badge").textContent();
    expect(version).toContain("v4.97.0");
  });
});

test.describe("Wave 38 — Bulk Actions in DataTable", () => {
  test("selecting a row shows bulk-bar", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-select-0").click();
    await expect(page.getByTestId("data-table-bulk-bar")).toBeVisible({ timeout: 3000 });
  });

  test("selecting two rows updates count", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-select-0").click();
    await page.getByTestId("data-table-select-1").click();
    const bar = await page.getByTestId("data-table-bulk-bar").textContent();
    expect(bar).toContain("2");
  });

  test("select-all then deselect clears bulk-bar", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-select-all").click();
    await expect(page.getByTestId("data-table-bulk-bar")).toBeVisible({ timeout: 3000 });
    await page.getByTestId("data-table-select-all").click();
    await expect(page.getByTestId("data-table-bulk-bar")).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe("Wave 38 — App Layout Consistency", () => {
  test("app-title present on every page (dashboard)", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-title")).toBeVisible({ timeout: 10000 });
    const title = await page.getByTestId("app-title").textContent();
    expect(title).toContain("RiskCanvas");
  });

  test("sidebar nav is present on exports page", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("nav")).toBeVisible();
  });

  test("sidebar nav is present on workbench page", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("sidebar")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("nav")).toBeVisible();
  });

  test("main-content present on dashboard", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("main-content")).toBeVisible({ timeout: 10000 });
  });
});
