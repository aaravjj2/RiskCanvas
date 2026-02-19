/**
 * test-w49-w56-unit.spec.ts
 * Wave 49-56 — Mega-Delivery: Datasets, ScenarioComposer, Reviews + backend modules
 * v5.22.0 → v5.45.0
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

// ── WAVE 49: Datasets Nav ─────────────────────────────────────────────────

test.describe("Wave 49 — Datasets nav and page", () => {
  test("nav-datasets is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-datasets").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-datasets")).toBeVisible();
  });

  test("clicking nav-datasets navigates to /datasets", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-datasets").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-datasets").click();
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
  });

  test("datasets-page loads at /datasets", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
  });

  test("datasets-table-ready is visible after load", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("dataset-kind-filter is visible", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-kind-filter")).toBeVisible();
  });

  test("dataset-ingest-open button is visible", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-ingest-open")).toBeVisible();
  });

  test("clicking dataset-ingest-open reveals dataset-drawer-ready", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("dataset-ingest-open").click();
    await expect(page.getByTestId("dataset-drawer-ready")).toBeVisible({ timeout: 10_000 });
  });

  test("dataset-validate-btn visible in drawer", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("dataset-ingest-open").click();
    await expect(page.getByTestId("dataset-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("dataset-validate-btn")).toBeVisible();
  });

  test("dataset-save-btn visible in drawer", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("dataset-ingest-open").click();
    await expect(page.getByTestId("dataset-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("dataset-save-btn")).toBeVisible();
  });

  test("dataset-row-0 renders in table", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-row-0")).toBeVisible({ timeout: 10_000 });
  });
});

// ── WAVE 50: Scenario Composer Nav ────────────────────────────────────────

test.describe("Wave 50 — ScenarioComposer nav and page", () => {
  test("nav-scenario-composer is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-scenario-composer").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-scenario-composer")).toBeVisible();
  });

  test("clicking nav-scenario-composer navigates to /scenario-composer", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-scenario-composer").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-scenario-composer").click();
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-composer loads at /scenario-composer", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-list-ready visible after load", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-kind-select is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-kind-select")).toBeVisible();
  });

  test("scenario-validate button is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-validate")).toBeVisible();
  });

  test("scenario-run button is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-run")).toBeVisible();
  });

  test("scenario-replay button is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-replay")).toBeVisible();
  });

  test("scenario-preview-ready panel is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-preview-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-action-log panel is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-action-log")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-row-0 renders in list", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-row-0")).toBeVisible({ timeout: 10_000 });
  });
});

// ── WAVE 51: Reviews Nav ─────────────────────────────────────────────────

test.describe("Wave 51 — Reviews nav and page", () => {
  test("nav-reviews is present in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-reviews").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-reviews")).toBeVisible();
  });

  test("clicking nav-reviews navigates to /reviews", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-reviews").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-reviews").click();
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
  });

  test("reviews-page loads at /reviews", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
  });

  test("reviews-table-ready visible after load", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("review-row-0 renders in table", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("review-row-0")).toBeVisible({ timeout: 10_000 });
  });

  test("clicking review-row-0 opens drawer", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("review-row-0").click();
    await expect(page.getByTestId("review-drawer-ready")).toBeVisible({ timeout: 10_000 });
  });
});

// ── WAVE 49-56: Version Badge ─────────────────────────────────────────────

test.describe("Wave 49-56 — Version badge v5.45.0", () => {
  test("version-badge shows v5.45", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    const badge = page.getByTestId("version-badge");
    await badge.evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(badge).toBeVisible();
    const text = await badge.textContent();
    expect(text).toContain("5.45");
  });
});
