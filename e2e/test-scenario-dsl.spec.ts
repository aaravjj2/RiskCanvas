import { test, expect } from "@playwright/test";

const VALID_DSL = JSON.stringify({
  name: "test-scenario",
  type: "shock",
  shocks: [{ asset: "AAPL", field: "spot", delta_pct: 5 }],
  metadata: { author: "e2e", version: 1 },
});

test("scenario-dsl: page loads", async ({ page }) => {
  await page.goto("/scenarios-dsl");
  await expect(page.getByTestId("scenario-page")).toBeVisible({ timeout: 10000 });
});

test("scenario-dsl: validate valid DSL shows no errors", async ({ page }) => {
  await page.goto("/scenarios-dsl");
  await expect(page.getByTestId("scenario-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("scenario-tab-author").click();
  await page.getByTestId("scenario-json-editor").fill(VALID_DSL);
  await page.getByTestId("scenario-validate-btn").click();
  await expect(page.getByTestId("scenario-validate-result")).toBeVisible({ timeout: 8000 });
  await expect(page.getByTestId("scenario-validate-result")).toContainText("Valid");
});

test("scenario-dsl: save scenario creates entry", async ({ page }) => {
  await page.goto("/scenarios-dsl");
  await page.getByTestId("scenario-tab-author").click();
  await page.getByTestId("scenario-json-editor").fill(VALID_DSL);
  await page.getByTestId("scenario-save-btn").click();
  await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
});

test("scenario-dsl: list tab shows saved scenarios", async ({ page }) => {
  await page.goto("/scenarios-dsl");
  // Create first
  await page.getByTestId("scenario-tab-author").click();
  await page.getByTestId("scenario-json-editor").fill(VALID_DSL);
  await page.getByTestId("scenario-save-btn").click();
  await expect(page.getByTestId("scenario-created")).toBeVisible({ timeout: 10000 });
  // Go to list
  await page.getByTestId("scenario-tab-list").click();
  await page.getByTestId("scenario-load-list-btn").click();
  await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 10000 });
});
