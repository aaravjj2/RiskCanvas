import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w14");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({
    path: path.join(SHOTS_DIR, `${name}.png`),
    fullPage: true,
  });
}

test(
  "phase14-judge-demo: full Wave 13+14 tour (v4.6–v4.9)",
  { tag: "@judge" },
  async ({ page }) => {
    // ─── 01: Dashboard ────────────────────────────────────────────────────────
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");

    // ─── 02: Version badge shows v4.9.0 ──────────────────────────────────────
    await expect(page.getByTestId("version-badge")).toContainText("v4.9.0");
    await shot(page, "02-version-badge-4-9-0");

    // ─── 03: Navigate to Market Data via nav ─────────────────────────────────
    await page.getByTestId("nav-market").click();
    await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "03-market-page");

    // ─── 04: Market as-of loads ───────────────────────────────────────────────
    await expect(page.getByTestId("market-asof")).toBeVisible({ timeout: 8000 });
    await shot(page, "04-market-asof");

    // ─── 05: Market provider shown ────────────────────────────────────────────
    await expect(page.getByTestId("market-provider")).toBeVisible();
    await shot(page, "05-market-provider");

    // ─── 06: Spot lookup input ────────────────────────────────────────────────
    const spotInput = page.getByTestId("market-spot-symbol-input");
    await expect(spotInput).toBeVisible();
    await spotInput.fill("AAPL");
    await shot(page, "06-spot-input-aapl");

    // ─── 07: Submit spot lookup ───────────────────────────────────────────────
    await page.getByTestId("market-spot-submit").click();
    await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 8000 });
    await shot(page, "07-spot-result-aapl");

    // ─── 08: Series lookup for MSFT ───────────────────────────────────────────
    const seriesInput = page.getByTestId("market-series-symbol-input");
    await expect(seriesInput).toBeVisible();
    await seriesInput.fill("MSFT");
    await page.getByTestId("market-series-submit").click();
    await expect(page.getByTestId("market-series-ready")).toBeVisible({ timeout: 8000 });
    await shot(page, "08-series-result-msft");

    // ─── 09: Rates curve lookup ────────────────────────────────────────────────
    const curveInput = page.getByTestId("market-curve-id-input");
    await expect(curveInput).toBeVisible();
    await curveInput.fill("USD_SOFR");
    await page.getByTestId("market-curve-submit").click();
    await expect(page.getByTestId("market-curve-ready")).toBeVisible({ timeout: 8000 });
    await shot(page, "09-curve-usd-sofr");

    // ─── 10: Spot SPY ─────────────────────────────────────────────────────────
    await page.getByTestId("market-spot-symbol-input").fill("SPY");
    await page.getByTestId("market-spot-submit").click();
    await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 8000 });
    await shot(page, "10-spot-result-spy");

    // ─── 11: Navigate to Hedge Studio ─────────────────────────────────────────
    await page.getByTestId("nav-hedge").click();
    await expect(page.getByTestId("hedge-studio-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "11-hedge-studio-v1");

    // ─── 12: v1 portfolio input ───────────────────────────────────────────────
    await page.getByTestId("portfolio-id-input").fill("port-demo-001");
    await page.getByTestId("run-id-input").fill("run-001");
    await shot(page, "12-hedge-v1-inputs");

    // ─── 13: Generate hedges v1 ───────────────────────────────────────────────
    await page.getByTestId("generate-hedges-btn").click();
    await expect(page.getByTestId("hedges-list")).toBeVisible({ timeout: 15000 });
    await shot(page, "13-hedge-v1-results");

    // ─── 14: v1 hedge card visible ────────────────────────────────────────────
    await expect(page.getByTestId("hedge-card-0")).toBeVisible();
    await shot(page, "14-hedge-card-0");

    // ─── 15: Init Hedge Studio Pro (v2) ──────────────────────────────────────
    await page.getByTestId("hedge-v2-init-btn").click();
    await expect(page.getByTestId("hedge-v2-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "15-hedge-v2-ready");

    // ─── 16: Template cards visible ───────────────────────────────────────────
    await expect(page.getByTestId("hedge-template-protective_put")).toBeVisible();
    await expect(page.getByTestId("hedge-template-collar")).toBeVisible();
    await expect(page.getByTestId("hedge-template-delta_hedge")).toBeVisible();
    await expect(page.getByTestId("hedge-template-duration_hedge")).toBeVisible();
    await shot(page, "16-hedge-templates-all-four");

    // ─── 17: Select collar template ───────────────────────────────────────────
    await page.getByTestId("hedge-template-collar").click();
    await shot(page, "17-template-collar-selected");

    // ─── 18: Constraints ready ────────────────────────────────────────────────
    await expect(page.getByTestId("hedge-constraints-ready")).toBeVisible();
    await shot(page, "18-hedge-constraints");

    // ─── 19: Run optimizer v2 ─────────────────────────────────────────────────
    await page.getByTestId("hedge-suggest-btn").click();
    await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 20000 });
    await shot(page, "19-hedge-v2-results-table");

    // ─── 20: Select protective_put and run again ──────────────────────────────
    await page.getByTestId("hedge-template-protective_put").click();
    await page.getByTestId("hedge-suggest-btn").click();
    await expect(page.getByTestId("hedge-results-table")).toBeVisible({ timeout: 20000 });
    await shot(page, "20-hedge-protective-put-results");

    // ─── 21: Compare runs ─────────────────────────────────────────────────────
    await page.getByTestId("hedge-compare-btn").click();
    await expect(page.getByTestId("hedge-delta-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "21-hedge-compare-deltas");

    // ─── 22: Build Decision Memo ──────────────────────────────────────────────
    await page.getByTestId("hedge-build-memo-btn").click();
    await expect(page.getByTestId("hedge-memo-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "22-hedge-memo-ready");

    // ─── 23: Export Markdown memo button visible ──────────────────────────────
    await expect(page.getByTestId("hedge-memo-export-md")).toBeVisible();
    await shot(page, "23-memo-export-md-btn");

    // ─── 24: Export Decision Pack button visible ──────────────────────────────
    await expect(page.getByTestId("hedge-memo-export-pack")).toBeVisible();
    await shot(page, "24-memo-export-pack-btn");

    // ─── 25: Click Export Markdown ────────────────────────────────────────────
    await page.getByTestId("hedge-memo-export-md").click();
    await shot(page, "25-memo-md-exported");

    // ─── 26: Navigate back to Market Data ─────────────────────────────────────
    await page.getByTestId("nav-market").click();
    await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "26-back-to-market");

    // ─── 27: Determinism check – reload market page ───────────────────────────
    const asofBefore = await page.getByTestId("market-asof").textContent();
    await page.reload();
    await expect(page.getByTestId("market-asof")).toBeVisible({ timeout: 8000 });
    const asofAfter = await page.getByTestId("market-asof").textContent();
    expect(asofBefore).toEqual(asofAfter);
    await shot(page, "27-market-determinism-reload");

    // ─── 28: Navigate to Dashboard to close tour ─────────────────────────────
    await page.getByTestId("nav-dashboard").click();
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 8000 });
    await shot(page, "28-dashboard-tour-complete");

    // Verify screenshot count
    const files = fs.readdirSync(SHOTS_DIR).filter((f) => f.endsWith(".png"));
    expect(files.length).toBeGreaterThanOrEqual(25);
  }
);
