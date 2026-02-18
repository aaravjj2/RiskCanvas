import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

test("phase12-judge-demo: full wave 11+12 tour", async ({ page }) => {
  // 01 - Dashboard
  await page.goto("/");
  await shot(page, "01-dashboard");

  // 02 - Command Palette opens with Ctrl+K
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("cmdk-open")).toBeVisible();
  await shot(page, "02-cmdk-open");

  // 03 - Type in palette to filter
  await page.getByTestId("cmdk-input").fill("search");
  await shot(page, "03-cmdk-filter-search");

  // 04 - Navigate to search via palette
  const searchItem = page.getByTestId("cmdk-item-search");
  await expect(searchItem).toBeVisible();
  await searchItem.click();
  await expect(page.getByTestId("search-page")).toBeVisible();
  await shot(page, "04-search-page");

  // 05 - Search for portfolio
  await page.getByTestId("search-input").fill("portfolio");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  await shot(page, "05-search-results-portfolio");

  // 06 - Search result details
  const result0 = page.getByTestId("search-result-0");
  await expect(result0).toBeVisible();
  await shot(page, "06-search-result-0-visible");

  // 07 - Filter by run type chip
  await page.getByTestId("search-chip-run").click();
  await shot(page, "07-search-chip-run-filter");

  // 08 - Search for risk
  await page.getByTestId("search-input").fill("risk");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  await shot(page, "08-search-results-risk");

  // 09 - Navigate to Activity via nav
  await page.getByTestId("nav-activity").click();
  await expect(page.getByTestId("activity-page")).toBeVisible();
  await shot(page, "09-activity-page");

  // 10 - Activity feed loaded
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await shot(page, "10-activity-feed-ready");

  // 11 - Activity item details
  await expect(page.getByTestId("activity-item-0")).toBeVisible();
  await shot(page, "11-activity-item-0");

  // 12 - Presence panel loaded
  await expect(page.getByTestId("presence-ready")).toBeVisible();
  await shot(page, "12-presence-panel");

  // 13 - Presence user status
  const user0 = page.getByTestId("presence-user-0");
  await expect(user0).toBeVisible();
  await shot(page, "13-presence-user-0");

  // 14 - Activity filter by run.execute
  await page.getByTestId("activity-filter-run-execute").click();
  await shot(page, "14-activity-filter-run-execute");

  // 15 - Activity filter all
  await page.getByTestId("activity-filter-all").click();
  await shot(page, "15-activity-filter-all");

  // 16 - Activity refresh
  await page.getByTestId("activity-refresh").click();
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await shot(page, "16-activity-refresh");

  // 17 - Navigate to runs page
  await page.getByTestId("nav-devops").click();
  await shot(page, "17-devops-page");

  // 18 - Cmd palette from devops
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("cmdk-open")).toBeVisible();
  await shot(page, "18-cmdk-from-devops");

  // 19 - Navigate to activity via palette
  await page.getByTestId("cmdk-input").fill("activity");
  await expect(page.getByTestId("cmdk-item-activity")).toBeVisible();
  await shot(page, "19-cmdk-filter-activity");
  await page.keyboard.press("Escape");

  // 20 - Navigate to governance
  await page.getByTestId("nav-governance").click();
  await shot(page, "20-governance-page");

  // 21 - Open cmd palette on governance
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("cmdk-open")).toBeVisible();
  await page.getByTestId("cmdk-input").fill("dashboard");
  await shot(page, "21-cmdk-filter-dashboard");
  await page.getByTestId("cmdk-item-dashboard").click();
  await shot(page, "22-back-to-dashboard");

  // 23 - Search with empty query shows search-empty
  await page.getByTestId("nav-search").click();
  await expect(page.getByTestId("search-page")).toBeVisible();
  await page.getByTestId("search-input").fill("");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-empty")).toBeVisible();
  await shot(page, "23-search-empty");

  // 24 - Reindex action
  await page.getByTestId("search-reindex").click();
  await shot(page, "24-search-reindex");

  // 25 - Search for var
  await page.getByTestId("search-input").fill("var");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  await shot(page, "25-search-results-var");

  // 26 - SRE page
  await page.getByTestId("nav-sre").click();
  await shot(page, "26-sre-page");

  // 27 - Final summary: back to activity
  await page.getByTestId("nav-activity").click();
  await expect(page.getByTestId("activity-page")).toBeVisible();
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await expect(page.getByTestId("presence-ready")).toBeVisible();
  await shot(page, "27-final-activity-summary");
});
