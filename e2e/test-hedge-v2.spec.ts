import { test, expect } from "@playwright/test";

/**
 * RiskCanvas v4.8.0 — Hedge Studio Pro E2E
 * - retries: 0, workers: 1
 * - ONLY data-testid selectors
 * - Backend must be running on :8090 (DEMO_MODE=true)
 * - Frontend on :4174 (vite preview build)
 */

test("hedge-v2-1: hedge studio page renders", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });
});

test("hedge-v2-2: initialize pro mode shows v2-ready panel", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });
});

test("hedge-v2-3: template selectors visible after init", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  for (const tid of ["protective_put", "collar", "delta_hedge", "duration_hedge"]) {
    await expect(page.getByTestId(`hedge-template-${tid}`)).toBeVisible();
  }
});

test("hedge-v2-4: constraints panel visible with suggest button", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  await expect(page.getByTestId("hedge-constraints-ready")).toBeVisible();
  await expect(page.getByTestId("hedge-suggest-btn")).toBeVisible();
});

test("hedge-v2-5: run optimizer v2 shows results table", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  await page.getByTestId("hedge-suggest-btn").click();
  await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 10000 });
});

test("hedge-v2-6: compare best candidate shows delta panel", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  await page.getByTestId("hedge-suggest-btn").click();
  await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-compare-btn").click();
  await expect(page.getByTestId("hedge-delta-ready")).toBeVisible({ timeout: 10000 });
});

test("hedge-v2-7: build decision memo shows memo panel", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  await page.getByTestId("hedge-suggest-btn").click();
  await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-compare-btn").click();
  await expect(page.getByTestId("hedge-delta-ready")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-build-memo-btn").click();
  await expect(page.getByTestId("hedge-memo-ready")).toBeVisible({ timeout: 10000 });
});

test("hedge-v2-8: memo export buttons visible", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-v2-init-btn").click();
  await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 8000 });

  await page.getByTestId("hedge-suggest-btn").click();
  await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-compare-btn").click();
  await expect(page.getByTestId("hedge-delta-ready")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("hedge-build-memo-btn").click();
  await expect(page.getByTestId("hedge-memo-ready")).toBeVisible({ timeout: 10000 });

  await expect(page.getByTestId("hedge-memo-export-md")).toBeVisible();
  await expect(page.getByTestId("hedge-memo-export-pack")).toBeVisible();
});

test("hedge-v2-9: v1 workflow unchanged (generate-hedges-btn exists)", async ({ page }) => {
  await page.goto("/hedge");
  await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 10000 });

  // v1 controls should still be present
  await expect(page.getByTestId("portfolio-id-input")).toBeVisible();
  await expect(page.getByTestId("run-id-input")).toBeVisible();
  await expect(page.getByTestId("target-reduction-slider")).toBeVisible();
  await expect(page.getByTestId("max-cost-input")).toBeVisible();
  await expect(page.getByTestId("generate-hedges-btn")).toBeVisible();
});
