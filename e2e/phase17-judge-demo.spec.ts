import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w17");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

test(
  "phase17-judge-demo: Replay Store full tour (v4.18–v4.21)",
  { tag: "@judge" },
  async ({ page }) => {
    // ── 01: Dashboard ──
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");

    // ── 02: Navigate to Replay ──
    await page.getByTestId("nav-replay").click();
    await expect(page.getByTestId("replay-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "02-replay-page");

    // ── 03: Suites tab ──
    await page.getByTestId("replay-tab-suites").click();
    await shot(page, "03-suites-tab");

    // ── 04: Load suites ──
    await page.getByTestId("replay-load-suites-btn").click();
    await expect(page.getByTestId("replay-suites-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "04-suites-loaded");

    // ── 05: First suite visible ──
    const firstSuite = page.locator('[data-testid^="replay-suite-"]').first();
    await expect(firstSuite).toBeVisible({ timeout: 8000 });
    await shot(page, "05-first-suite");

    // ── 06: Run suite ──
    await page.getByTestId("replay-run-suite-btn").click();
    await expect(page.getByTestId("replay-scorecard-ready")).toBeVisible({ timeout: 20000 });
    await shot(page, "06-scorecard-ready");

    // ── 07: Scorecard content ──
    const scorecardText = await page.getByTestId("replay-scorecard-ready").textContent();
    expect((scorecardText || "").length).toBeGreaterThan(10);
    await shot(page, "07-scorecard-content");

    // ── 08: Export repro report ──
    await page.getByTestId("replay-export-repro-btn").click();
    await expect(page.getByTestId("repro-report-ready")).toBeVisible({ timeout: 12000 });
    await shot(page, "08-repro-report");

    // ── 09: Store tab ──
    await page.getByTestId("replay-tab-store").click();
    await shot(page, "09-store-tab");

    // ── 10: Store a replay entry ──
    await page.getByTestId("replay-store-btn").click();
    await expect(page.getByTestId("replay-stored")).toBeVisible({ timeout: 10000 });
    await shot(page, "10-entry-stored");

    // ── 11: Stored ID (auto-filled in verify input) ──
    const storedId = await page.getByTestId("replay-id-input").inputValue();
    expect(storedId.length).toBeGreaterThan(4);
    await shot(page, "11-stored-id");

    // ── 12: Verify input (on same store tab) ──
    await shot(page, "12-verify-input-on-store-tab");

    // ── 13: Enter stored ID ──
    await page.getByTestId("replay-id-input").fill(storedId);
    await shot(page, "13-id-entered");

    // ── 14: Verify ──
    await page.getByTestId("replay-verify-btn").click();
    await expect(page.getByTestId("replay-verify-result")).toBeVisible({ timeout: 10000 });
    await shot(page, "14-verify-result");

    // ── 15: Verify result shows valid ──
    const verifyText = await page.getByTestId("replay-verify-result").textContent();
    expect((verifyText || "").toLowerCase()).toContain("verified");
    await shot(page, "15-verify-ok");

    // ── 16: Store second entry (determinism) ──
    await page.getByTestId("replay-store-btn").click();
    await expect(page.getByTestId("replay-stored")).toBeVisible({ timeout: 10000 });
    const storedId2 = await page.getByTestId("replay-id-input").inputValue();
    expect(storedId2).toBe(storedId); // same request → same ID
    await shot(page, "16-determinism-same-id");

    // ── 17: Run suite again ──
    await page.getByTestId("replay-tab-suites").click();
    await page.getByTestId("replay-run-suite-btn").click();
    await expect(page.getByTestId("replay-scorecard-ready")).toBeVisible({ timeout: 20000 });
    await shot(page, "17-suite-run-again");

    // ── 18: Navigate away and back ──
    await page.getByTestId("nav-dashboard").click();
    await page.getByTestId("nav-replay").click();
    await expect(page.getByTestId("replay-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "18-back-from-nav");

    // ── 19: Scroll bottom ──
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(page, "19-scroll-bottom");
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, "20-scroll-top");

    // ── 21-25: Final screenshots ──
    await page.getByTestId("replay-tab-suites").click();
    await page.getByTestId("replay-load-suites-btn").click();
    await expect(page.getByTestId("replay-suites-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "21-final-suites");
    await shot(page, "22-pre-final");
    await shot(page, "23-final-a");
    await shot(page, "24-final-b");
    await shot(page, "25-final-state");
  }
);
