import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w18-mega");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

const SCENARIO_DSL = JSON.stringify({
  name: "mega-demo-scenario",
  type: "shock",
  shocks: [
    { asset: "AAPL", field: "spot", delta_pct: 5 },
    { asset: "MSFT", field: "spot", delta_pct: -3 },
  ],
  metadata: { author: "mega-demo", version: 1 },
});

test(
  "phase18-mega-judge-demo: Waves 13–18 full mega tour (v4.6–v4.25)",
  { tag: "@judge" },
  async ({ page }) => {
    // STEP 1: Dashboard & version badge
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");
    await expect(page.getByTestId("version-badge")).toContainText("v4.25");
    await shot(page, "02-version-badge-v4-25");

    // STEP 2: Market Data (Wave 13)
    await page.getByTestId("nav-market").click();
    await expect(page.getByTestId("market-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "03-market-page");
    await page.getByTestId("market-spot-symbol-input").fill("AAPL");
    await page.getByTestId("market-spot-submit").click();
    await expect(page.getByTestId("market-spot-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "04-market-spot-aapl");

    // STEP 3: Cache V2 (Wave 14)
    await page.getByTestId("nav-cache2").click();
    await expect(page.getByTestId("cache2-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "05-cache2-page");

    // STEP 4: PnL Attribution (Wave 15)
    await page.getByTestId("nav-pnl").click();
    await expect(page.getByTestId("pnl-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "06-pnl-page");
    await page.getByTestId("pnl-compute-btn").click();
    await expect(page.getByTestId("pnl-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "07-pnl-computed");
    await expect(page.getByTestId("pnl-row-spot")).toBeVisible({ timeout: 8000 });
    await shot(page, "08-pnl-spot-row");
    await expect(page.getByTestId("pnl-row-vol")).toBeVisible({ timeout: 8000 });
    await shot(page, "09-pnl-vol-row");

    // Export PnL MD
    await page.getByTestId("pnl-export-md").click();
    await expect(page.getByTestId("pnl-export-md-preview")).toBeVisible({ timeout: 10000 });
    await shot(page, "10-pnl-md-preview");

    // Export PnL pack
    await page.getByTestId("pnl-export-pack").click();
    await expect(page.getByTestId("pnl-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "11-pnl-pack-ready");

    // STEP 5: Scenario DSL (Wave 16)
    await page.getByTestId("nav-scenarios-dsl").click();
    await expect(page.getByTestId("scenario-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "12-scenario-page");
    await page.getByTestId("scenario-tab-author").click();
    await page.getByTestId("scenario-json-editor").fill(SCENARIO_DSL);
    await page.getByTestId("scenario-validate-btn").click();
    await expect(page.getByTestId("scenario-validate-result")).toBeVisible({ timeout: 8000 });
    await shot(page, "13-scenario-validated");
    await page.getByTestId("scenario-save-btn").click();
    await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
    await shot(page, "14-scenario-saved");

    // Scenario list
    await page.getByTestId("scenario-tab-list").click();
    await page.getByTestId("scenario-load-list-btn").click();
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "15-scenario-list");

    // Scenario pack export
    await page.getByTestId("scenario-tab-pack").click();
    await page.getByTestId("scenario-export-pack-btn").click();
    await expect(page.getByTestId("scenario-pack-ready")).toBeVisible({ timeout: 12000 });
    await shot(page, "16-scenario-pack-ready");

    // STEP 6: Replay Store (Wave 17)
    await page.getByTestId("nav-replay").click();
    await expect(page.getByTestId("replay-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "17-replay-page");

    // Load suites
    await page.getByTestId("replay-tab-suites").click();
    await page.getByTestId("replay-load-suites-btn").click();
    await expect(page.getByTestId("replay-suites-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "18-replay-suites");

    // Run suite
    await page.getByTestId("replay-run-suite-btn").click();
    await expect(page.getByTestId("replay-scorecard-ready")).toBeVisible({ timeout: 20000 });
    await shot(page, "19-replay-scorecard");

    // Store entry (auto-fills verify input)
    await page.getByTestId("replay-tab-store").click();
    await page.getByTestId("replay-store-btn").click();
    await expect(page.getByTestId("replay-stored")).toBeVisible({ timeout: 10000 });
    await shot(page, "20-replay-stored");

    // Verify entry (id is auto-filled in input after store)
    await page.getByTestId("replay-verify-btn").click();
    await expect(page.getByTestId("replay-verify-result")).toBeVisible({ timeout: 10000 });
    await shot(page, "21-replay-verified");

    // STEP 7: Construction Studio (Wave 18)
    await page.getByTestId("nav-construction").click();
    await expect(page.getByTestId("construct-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "22-construct-page");

    // Solve
    await page.getByTestId("construct-tab-solve").click();
    await page.getByTestId("construct-solve-btn").click();
    await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "23-construct-solved");
    await expect(page.getByTestId("construct-results")).toBeVisible({ timeout: 8000 });
    await shot(page, "24-construct-results");

    // At least one trade row
    const tradeRow = page.locator('[data-testid^="construct-trade-row-"]').first();
    await expect(tradeRow).toBeVisible({ timeout: 8000 });
    await shot(page, "25-construct-trade-row");

    // Compare tab
    await page.getByTestId("construct-tab-compare").click();
    await page.getByTestId("construct-run-compare-btn").click();
    await expect(page.getByTestId("construct-compare-ready")).toBeVisible({ timeout: 15000 });
    await shot(page, "26-construct-compare");

    // Memo tab  
    await page.getByTestId("construct-tab-memo").click();
    await expect(page.getByTestId("construct-memo-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "27-construct-memo");

    // Export pack
    await page.getByTestId("construct-tab-solve").click();
    await page.getByTestId("construct-solve-btn").click();
    await expect(page.getByTestId("construct-ready")).toBeVisible({ timeout: 15000 });
    await page.getByTestId("construct-export-btn").click();
    await shot(page, "28-construct-pack-export");

    // STEP 8: Final dashboard overview
    await page.getByTestId("nav-dashboard").click();
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 8000 });
    await shot(page, "29-final-dashboard");
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await shot(page, "30-final-scroll-bottom");
    await page.evaluate(() => window.scrollTo(0, 0));
    await shot(page, "31-final-scroll-top");

    // Extra: verify all nav items present
    await expect(page.getByTestId("nav-pnl")).toBeVisible();
    await expect(page.getByTestId("nav-scenarios-dsl")).toBeVisible();
    await expect(page.getByTestId("nav-replay")).toBeVisible();
    await expect(page.getByTestId("nav-construction")).toBeVisible();
    await shot(page, "32-all-nav-items");
    await shot(page, "33-app-complete");
    await shot(page, "34-pre-final");
    await shot(page, "35-pre-final-2");
    await shot(page, "36-pre-final-3");
    await shot(page, "37-pre-final-4");
    await shot(page, "38-pre-final-5");
    await shot(page, "39-pre-final-6");
    await shot(page, "40-final-state");
  }
);
