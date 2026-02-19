/**
 * test-w37-workbench.spec.ts
 * Wave 37 — Workbench page (all-in-one terminal)
 * v4.90-v4.93
 *
 * ALL selectors use data-testid ONLY.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 37 — Workbench Layout", () => {
  test("navigate to /workbench via nav", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("nav-workbench").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-workbench").click();
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
  });

  test("workbench has left panel", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("workbench-left-panel")).toBeVisible();
  });

  test("workbench has center panel", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("workbench-center-panel")).toBeVisible();
  });

  test("left panel has nav items", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("workbench-nav-mr-review")).toBeVisible();
    await expect(page.getByTestId("workbench-nav-incidents")).toBeVisible();
    await expect(page.getByTestId("workbench-nav-readiness")).toBeVisible();
  });
});

test.describe("Wave 37 — Workbench Panel Switching", () => {
  test("switching to incidents panel updates view", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-nav-incidents").click();
    await expect(page.getByTestId("workbench-panel-incidents")).toBeVisible({ timeout: 5000 });
  });

  test("switching to readiness panel works", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-nav-readiness").click();
    await expect(page.getByTestId("workbench-panel-readiness")).toBeVisible({ timeout: 5000 });
  });

  test("switching to workflows panel works", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-nav-workflows").click();
    await expect(page.getByTestId("workbench-panel-workflows")).toBeVisible({ timeout: 5000 });
  });

  test("action log shows items after panel switch", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-nav-incidents").click();
    await expect(page.getByTestId("workbench-action-log")).toBeVisible();
    // Initial action items
    await expect(page.getByTestId("workbench-action-item-0")).toBeVisible();
  });
});

test.describe("Wave 37 — Workbench Context Drawer", () => {
  test("context open button exists", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("workbench-context-open")).toBeVisible();
  });

  test("clicking context-open shows right drawer", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-right-drawer")).toBeVisible({ timeout: 5000 });
  });

  test("context drawer shows audit hash", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-context-hash")).toBeVisible({ timeout: 5000 });
    const hash = await page.getByTestId("workbench-context-hash").textContent();
    expect(hash).toContain("sha256:");
  });

  test("context drawer shows last export pack", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-context-last-export")).toBeVisible({ timeout: 5000 });
    const lastExport = await page.getByTestId("workbench-context-last-export").textContent();
    expect((lastExport ?? "").length).toBeGreaterThan(0);
  });

  test("copy hash button is clickable in context drawer", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-copy-hash-btn")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("workbench-copy-hash-btn").click();
    // Should trigger a toast
    await expect(page.getByTestId("toast-item-0")).toBeVisible({ timeout: 5000 });
  });

  test("context drawer closes on second click of context-open", async ({ page }) => {
    await page.goto(`${BASE}/workbench`);
    await expect(page.getByTestId("workbench-page")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-right-drawer")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("workbench-context-open").click();
    await expect(page.getByTestId("workbench-right-drawer")).not.toBeVisible({ timeout: 3000 });
  });
});
