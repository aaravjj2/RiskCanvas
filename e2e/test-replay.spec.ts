import { test, expect } from "@playwright/test";

test("replay: page loads", async ({ page }) => {
  await page.goto("/replay");
  await expect(page.getByTestId("replay-page")).toBeVisible({ timeout: 10000 });
});

test("replay: load suites shows built-in suites", async ({ page }) => {
  await page.goto("/replay");
  await page.getByTestId("replay-tab-suites").click();
  await page.getByTestId("replay-load-suites-btn").click();
  await expect(page.getByTestId("replay-suites-ready")).toBeVisible({ timeout: 10000 });
});

test("replay: run a suite produces scorecard", async ({ page }) => {
  await page.goto("/replay");
  await page.getByTestId("replay-tab-suites").click();
  await page.getByTestId("replay-load-suites-btn").click();
  await expect(page.getByTestId("replay-suites-ready")).toBeVisible({ timeout: 10000 });
  // Select first suite and run
  await page.getByTestId("replay-run-suite-btn").click();
  await expect(page.getByTestId("replay-scorecard-ready")).toBeVisible({ timeout: 15000 });
});

test("replay: store entry then verify", async ({ page }) => {
  await page.goto("/replay");
  await page.getByTestId("replay-tab-store").click();
  // Store a demo entry (auto-fills the replayId input)
  await page.getByTestId("replay-store-btn").click();
  await expect(page.getByTestId("replay-stored")).toBeVisible({ timeout: 10000 });
  // The store handler auto-fills replay-id-input with the stored ID
  // Click verify directly
  await page.getByTestId("replay-verify-btn").click();
  await expect(page.getByTestId("replay-verify-result")).toBeVisible({ timeout: 10000 });
});
