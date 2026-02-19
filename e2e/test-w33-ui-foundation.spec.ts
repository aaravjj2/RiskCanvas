/**
 * test-w33-ui-foundation.spec.ts
 * Wave 33 — PageShell + DataTable + RightDrawer + ToastCenter
 * v4.74-v4.77
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. No retries. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 33 — UI Foundation: PageShell", () => {
  test("exports page has page-shell and page-title", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-page")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("page-shell")).toBeVisible();
    await expect(page.getByTestId("page-title")).toBeVisible();
  });

  test("page-title text is not empty", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("page-title")).toBeVisible({ timeout: 10000 });
    const text = await page.getByTestId("page-title").textContent();
    expect(text).toBeTruthy();
    expect((text ?? "").length).toBeGreaterThan(0);
  });

  test("page-statusbar renders on exports page", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("page-statusbar")).toBeVisible({ timeout: 10000 });
  });

  test("page-actions slot renders refresh button", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("page-actions")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("export-refresh-btn")).toBeVisible();
  });
});

test.describe("Wave 33 — UI Foundation: DataTable", () => {
  test("data-table renders on exports page", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId("data-table")).toBeVisible();
  });

  test("data-table-header renders", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId("data-table-header")).toBeVisible();
  });

  test("data-table has sortable columns", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    // Sort by label column
    await expect(page.getByTestId("data-table-sort-label")).toBeVisible();
    await page.getByTestId("data-table-sort-label").click();
    await expect(page.getByTestId("data-table-row-0")).toBeVisible();
  });

  test("data-table sort toggles direction on second click", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-sort-type").click();
    await page.getByTestId("data-table-sort-type").click();
    // After two clicks, rows are still visible (sort desc)
    await expect(page.getByTestId("data-table-row-0")).toBeVisible();
  });

  test("data-table row selection works", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-select-0").click();
    await expect(page.getByTestId("data-table-bulk-bar")).toBeVisible();
  });

  test("data-table select-all works", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("data-table-select-all").click();
    await expect(page.getByTestId("data-table-bulk-bar")).toBeVisible();
    // Deselect all
    await page.getByTestId("data-table-select-all").click();
    await expect(page.getByTestId("data-table-bulk-bar")).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe("Wave 33 — UI Foundation: RightDrawer", () => {
  test("clicking Details opens right-drawer", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("right-drawer")).toBeVisible({ timeout: 5000 });
  });

  test("right-drawer title is visible", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("right-drawer-title")).toBeVisible();
  });

  test("right-drawer closes via close button", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("right-drawer")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("right-drawer-close").click();
    await expect(page.getByTestId("right-drawer")).not.toBeVisible({ timeout: 3000 });
  });

  test("right-drawer closes via ESC key", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("right-drawer")).toBeVisible({ timeout: 5000 });
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("right-drawer")).not.toBeVisible({ timeout: 3000 });
  });

  test("right-drawer shows sha256", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("export-drawer-open-0").click();
    await expect(page.getByTestId("export-drawer-sha256")).toBeVisible({ timeout: 5000 });
    const sha = await page.getByTestId("export-drawer-sha256").textContent();
    expect((sha ?? "").length).toBeGreaterThan(10);
  });
});

test.describe("Wave 33 — UI Foundation: Toast", () => {
  test("toast-center container is in DOM", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-page")).toBeVisible({ timeout: 10000 });
    // ToastCenter is always in DOM (empty)
    await expect(page.getByTestId("toast-center")).toBeAttached({ timeout: 5000 });
  });

  test("verify action triggers success toast", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15000 });
    // Click verify button on first row
    await page.getByTestId("export-verify-btn-0").click();
    // Wait for toast to appear
    await expect(page.getByTestId("toast-item-0")).toBeVisible({ timeout: 8000 });
  });
});
