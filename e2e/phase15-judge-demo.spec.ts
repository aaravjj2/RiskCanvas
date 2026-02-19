import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w15");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

test(
  "phase15-judge-demo: PnL Attribution full tour (v4.10–v4.13)",
  { tag: "@judge" },
  async ({ page }) => {
    // ── 01: Dashboard ──
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");

    // ── 02: Version badge v4.25.0 ──
    await expect(page.getByTestId("version-badge")).toContainText("v4.25");
    await shot(page, "02-version-badge");

    // ── 03: Navigate to PnL Attribution ──
    await page.getByTestId("nav-pnl").click();
    await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "03-pnl-page");

    // ── 04: Load presets ──
    await page.getByTestId("pnl-presets-btn").click();
    await expect(page.getByTestId("pnl-presets-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "04-presets-loaded");

    // ── 05: Compute attribution ──
    await page.getByTestId("pnl-compute-btn").click();
    await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "05-pnl-computed");

    // ── 06: Spot factor row visible ──
    await expect(page.getByTestId("pnl-row-spot")).toBeVisible({ timeout: 8000 });
    await shot(page, "06-spot-row");

    // ── 07: Vol factor row visible ──
    await expect(page.getByTestId("pnl-row-vol")).toBeVisible({ timeout: 8000 });
    await shot(page, "07-vol-row");

    // ── 08: Rates factor row visible ──
    await expect(page.getByTestId("pnl-row-rates")).toBeVisible({ timeout: 8000 });
    await shot(page, "08-rates-row");

    // ── 09: Spread factor row visible ──
    await expect(page.getByTestId("pnl-row-spread")).toBeVisible({ timeout: 8000 });
    await shot(page, "09-spread-row");

    // ── 10: Residual factor row visible ──
    await expect(page.getByTestId("pnl-row-residual")).toBeVisible({ timeout: 8000 });
    await shot(page, "10-residual-row");

    // ── 11: Contributions table visible ──
    await expect(page.getByTestId("pnl-contributions-table")).toBeVisible({ timeout: 8000 });
    await shot(page, "11-contributions-table");

    // ── 12: Export MD button visible ──
    await expect(page.getByTestId("pnl-export-md")).toBeVisible();
    await shot(page, "12-export-md-visible");

    // ── 13: Click export MD ──
    await page.getByTestId("pnl-export-md").click();
    await expect(page.getByTestId("pnl-export-md-preview")).toBeVisible({ timeout: 10000 });
    await shot(page, "13-md-preview");

    // ── 14: MD preview has content ──
    const mdText = await page.getByTestId("pnl-export-md-preview").textContent();
    expect((mdText || "").length).toBeGreaterThan(50);
    await shot(page, "14-md-content");

    // ── 15: Export pack button ──
    await expect(page.getByTestId("pnl-export-pack")).toBeVisible();
    await shot(page, "15-export-pack-btn");

    // ── 16: Click export pack ──
    await page.getByTestId("pnl-export-pack").click();
    await expect(page.getByTestId("pnl-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "16-pack-ready");

    // ── 17: Re-compute (determinism) ──
    await page.getByTestId("pnl-compute-btn").click();
    await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "17-pnl-recomputed-determinism");

    // ── 18: Second attribution is same spot row ──
    await expect(page.getByTestId("pnl-row-spot")).toBeVisible();
    await shot(page, "18-spot-row-determinism");

    // ── 19: Navigate back to dashboard ──
    await page.getByTestId("nav-dashboard").click();
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 8000 });
    await shot(page, "19-back-dashboard");

    // ── 20: Return to PnL page ──
    await page.getByTestId("nav-pnl").click();
    await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "20-pnl-return");

    // ── 21: Compute again after re-navigate ──
    await page.getByTestId("pnl-compute-btn").click();
    await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "21-pnl-after-nav");

    // ── 22: Presets after re-navigate ──
    await page.getByTestId("pnl-presets-btn").click();
    await expect(page.getByTestId("pnl-presets-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "22-presets-after-nav");

    // ── 23: Full page scroll ──
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(page, "23-page-bottom");
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, "24-page-top");

    // ── 25: Final state ──
    await shot(page, "25-final-state");
  }
);
