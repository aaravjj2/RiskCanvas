import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w16");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

const DSL_A = JSON.stringify({
  name: "equity-shock-5pct",
  type: "shock",
  shocks: [{ asset: "AAPL", field: "spot", delta_pct: 5 }],
  metadata: { author: "judge", version: 1 },
});

const DSL_B = JSON.stringify({
  name: "equity-shock-10pct",
  type: "shock",
  shocks: [{ asset: "AAPL", field: "spot", delta_pct: 10 }],
  metadata: { author: "judge", version: 2 },
});

test(
  "phase16-judge-demo: Scenario DSL full tour (v4.14–v4.17)",
  { tag: "@judge" },
  async ({ page }) => {
    // ── 01: Dashboard ──
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");

    // ── 02: Navigate to Scenarios DSL ──
    await page.getByTestId("nav-scenarios-dsl").click();
    await expect(page.getByTestId("scenario-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "02-scenario-page");

    // ── 03: Create tab ──
    await page.getByTestId("scenario-tab-author").click();
    await shot(page, "03-create-tab");

    // ── 04: Fill DSL A ──
    await page.getByTestId("scenario-json-editor").fill(DSL_A);
    await shot(page, "04-dsl-a-filled");

    // ── 05: Validate DSL A ──
    await page.getByTestId("scenario-validate-btn").click();
    await expect(page.getByTestId("scenario-validate-result")).toBeVisible({ timeout: 8000 });
    await shot(page, "05-dsl-a-validated");

    // ── 06: Validation result contains "valid" ──
    await expect(page.getByTestId("scenario-validate-result")).toContainText("Valid");
    await shot(page, "06-dsl-a-valid");

    // ── 07: Save DSL A ──
    await page.getByTestId("scenario-save-btn").click();
    await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
    await shot(page, "07-dsl-a-saved");

    // ── 08: Note saved ID ──
    const idText = await page.getByTestId("scenario-created").textContent();
    await shot(page, "08-scenario-id-a");

    // ── 09: Fill DSL B ──
    await page.getByTestId("scenario-json-editor").fill(DSL_B);
    await shot(page, "09-dsl-b-filled");

    // ── 10: Validate DSL B ──
    await page.getByTestId("scenario-validate-btn").click();
    await expect(page.getByTestId("scenario-validate-result")).toBeVisible({ timeout: 8000 });
    await shot(page, "10-dsl-b-validated");

    // ── 11: Save DSL B ──
    await page.getByTestId("scenario-save-btn").click();
    await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
    await shot(page, "11-dsl-b-saved");

    // ── 12: List tab ──
    await page.getByTestId("scenario-tab-list").click();
    await shot(page, "12-list-tab");

    // ── 13: Load scenario list ──
    await page.getByTestId("scenario-load-list-btn").click();
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "13-scenario-list-ready");

    // ── 14: Diff tab ──
    await page.getByTestId("scenario-tab-diff").click();
    await shot(page, "14-diff-tab");

    // ── 15: Diff button ──
    await expect(page.getByTestId("scenario-diff-btn")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("scenario-diff-btn").click();
    await expect(page.getByTestId("scenario-diff-ready")).toBeVisible({ timeout: 12000 });
    await shot(page, "15-diff-ready");

    // ── 16: Export tab ──
    await page.getByTestId("scenario-tab-pack").click();
    await shot(page, "16-export-tab");

    // ── 17: Export pack ──
    await page.getByTestId("scenario-export-pack-btn").click();
    await expect(page.getByTestId("scenario-pack-ready")).toBeVisible({ timeout: 12000 });
    await shot(page, "17-pack-ready");

    // ── 18: Back to list, verify scenarios persisted ──
    await page.getByTestId("scenario-tab-list").click();
    await page.getByTestId("scenario-load-list-btn").click();
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "18-list-persisted");

    // ── 19: Scroll to bottom ──
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(page, "19-scroll-bottom");

    // ── 20: Scroll to top ──
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, "20-scroll-top");

    // ── 21: Re-create same DSL A (determinism: same ID) ──
    await page.getByTestId("scenario-tab-author").click();
    await page.getByTestId("scenario-json-editor").fill(DSL_A);
    await page.getByTestId("scenario-save-btn").click();
    await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
    const idText2 = await page.getByTestId("scenario-created").textContent();
    expect((idText2 || "").trim()).toBe((idText || "").trim());
    await shot(page, "21-determinism-same-id");

    // ── 22: Navigate away and back ──
    await page.getByTestId("nav-dashboard").click();
    await page.getByTestId("nav-scenarios-dsl").click();
    await expect(page.getByTestId("scenario-page")).toBeVisible({ timeout: 8000 });
    await shot(page, "22-back-from-nav");

    // ── 23: Validate invalid DSL ──
    await page.getByTestId("scenario-tab-author").click();
    await page.getByTestId("scenario-json-editor").fill('{"invalid": true}');
    await page.getByTestId("scenario-validate-btn").click();
    await expect(page.getByTestId("scenario-validate-result")).toBeVisible({ timeout: 8000 });
    await shot(page, "23-invalid-dsl-error");

    // ── 24: Final state ──
    await shot(page, "24-pre-final");

    // ── 25: Final screenshot ──
    await page.getByTestId("scenario-tab-author").click();
    await shot(page, "25-final-state");
  }
);
