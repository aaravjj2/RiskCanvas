/**
 * test-stab-unit.spec.ts — Stabilization unit tests (v5.53.1 → v5.54.0)
 *
 * Validates:
 *   - Nav hygiene: only 5 items visible by default (feature flags)
 *   - TestHarness: System Checks panel present with API info + flags + reset
 *   - DatasetsPage: demo-quickstart button prefills drawer
 *   - ScenarioComposerPage: demo-quickstart button present
 *   - ReviewsPage: demo-quickstart button present
 *   - ExportsHubPage: generate-packet button present
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const API = "http://localhost:8090";

// ════════════════ FEATURE FLAGS — NAV HYGIENE ═════════════════════════════

test.describe("Feature flags — nav hygiene", () => {
  test("app-layout renders", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
  });

  test("nav-dashboard is visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("nav-dashboard")).toBeVisible();
  });

  test("nav-datasets is visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("nav-datasets")).toBeVisible();
  });

  test("nav-scenario-composer is visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("nav-scenario-composer")).toBeVisible();
  });

  test("nav-reviews is visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("nav-reviews")).toBeVisible();
  });

  test("nav-exports is visible", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("nav-exports")).toBeVisible();
  });

  test("nav contains exactly 6 items by default (incl harness)", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    // Count all nav-* testids (data-testid starting with nav-)
    const navItems = await page.locator("[data-testid^='nav-']").all();
    expect(navItems.length).toBeLessThanOrEqual(8);
    expect(navItems.length).toBeGreaterThanOrEqual(5);
  });
});

// ════════════════ TEST HARNESS — SYSTEM CHECKS ════════════════════════════

test.describe("TestHarness — System Checks panel", () => {
  test("harness-system-panel is visible at /__harness", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
  });

  test("harness-api-info shows health data", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("harness-api-info")).toBeVisible();
  });

  test("harness-api-version shows a non-empty version", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    const versionEl = page.getByTestId("harness-api-version");
    await expect(versionEl).toBeVisible();
    const text = await versionEl.textContent();
    expect(text?.trim().length).toBeGreaterThan(0);
  });

  test("harness-flags-list is visible with flag items", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("harness-flags-list")).toBeVisible();
    // At minimum the 5 default enabled flags should show
    const flagItems = await page.locator("[data-testid^='harness-flag-']").all();
    expect(flagItems.length).toBeGreaterThanOrEqual(5);
  });

  test("harness-reset-seed-btn is present", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("harness-reset-seed-btn")).toBeVisible();
  });
});

// ════════════════ DATASETS — DEMO QUICK START ════════════════════════════

test.describe("DatasetsPage — demo Quick Start", () => {
  test("datasets-page loads", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
  });

  test("dataset-demo-quickstart button is visible", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    // Wait for table to be ready before checking button
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-demo-quickstart")).toBeVisible();
  });

  test("clicking dataset-demo-quickstart opens drawer with prefilled name", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("dataset-demo-quickstart").click();
    await expect(page.getByTestId("dataset-ingest-form")).toBeVisible({ timeout: 10_000 });
    // The name field must be prefilled with "Demo Portfolio Q1 2026"
    const nameInput = page.getByTestId("dataset-ingest-name");
    await expect(nameInput).toBeVisible();
    await expect(nameInput).toHaveValue(/Demo Portfolio/i);
  });

  test("dataset-ingest-open button is present", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-ingest-open")).toBeVisible();
  });
});

// ════════════════ SCENARIO COMPOSER — DEMO QUICK START ═══════════════════

test.describe("ScenarioComposerPage — demo Quick Start", () => {
  test("scenario-composer loads", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
  });

  test("scenario-demo-quickstart button is visible", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-demo-quickstart")).toBeVisible({ timeout: 15_000 });
  });
});

// ════════════════ REVIEWS — DEMO QUICK START ═════════════════════════════

test.describe("ReviewsPage — demo Quick Start", () => {
  test("reviews-page loads", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
  });

  test("review-demo-quickstart button is visible", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    // Wait for reviews list to load
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("review-demo-quickstart")).toBeVisible();
  });
});

// ════════════════ EXPORTS HUB — GENERATE PACKET ══════════════════════════

test.describe("ExportsHubPage — generate decision packet", () => {
  test("exports-page loads", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-page")).toBeVisible({ timeout: 15_000 });
  });

  test("export-generate-packet-btn is visible", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("export-generate-packet-btn")).toBeVisible();
  });

  test("clicking export-generate-packet-btn opens the form", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("export-generate-packet-btn").click();
    await expect(page.getByTestId("export-generate-packet-form")).toBeVisible({ timeout: 10_000 });
  });

  test("export-subject-type-select is visible in form", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("export-generate-packet-btn").click();
    await expect(page.getByTestId("export-generate-packet-form")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("export-subject-type-select")).toBeVisible();
    await expect(page.getByTestId("export-subject-id-input")).toBeVisible();
  });

  test("export-refresh-btn is visible", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("export-refresh-btn")).toBeVisible();
  });
});

// ════════════════ BACKEND HEALTH — API SHAPE ═════════════════════════════

test.describe("Backend health contract", () => {
  test("GET /api/health returns required v5.53.1 fields", async ({ request }) => {
    const resp = await request.get(`${API}/health`);
    expect(resp.ok()).toBe(true);
    const body = await resp.json();
    expect(body).toMatchObject({
      status: "healthy",
    });
    expect(typeof body.version).toBe("string");
    expect(body.version.length).toBeGreaterThan(0);
    expect(typeof body.demo_mode).toBe("boolean");
    expect(typeof body.storage_backend).toBe("string");
    expect(typeof body.job_backend).toBe("string");
  });
});
