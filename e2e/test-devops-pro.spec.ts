import { test, expect } from "@playwright/test";

/**
 * E2E – DevOps Pro: MR Review, Pipeline Analyzer, Artifacts (Wave 9 v3.9)
 * retries: 0, workers: 1, ONLY data-testid selectors
 */

test("devops-pro-1 – devops page loads", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
});

test("devops-pro-2 – MR Review tab visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("devops-tab-mr")).toBeVisible();
});

test("devops-pro-3 – MR Review generate bundle → result visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("devops-tab-mr").click();
  await expect(page.getByTestId("devops-mr-generate")).toBeVisible({ timeout: 5000 });
  await page.getByTestId("devops-mr-generate").click();
  await expect(page.getByTestId("devops-mr-ready")).toBeVisible({ timeout: 15000 });
});

test("devops-pro-4 – MR Review with secret diff shows block", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("devops-tab-mr").click();
  await page.getByTestId("devops-mr-diff-input").fill(
    "+OPENAI_API_KEY=sk-1234567890abcdef1234567890abcdef1234567890"
  );
  await page.getByTestId("devops-mr-generate").click();
  await expect(page.getByTestId("devops-mr-ready")).toBeVisible({ timeout: 15000 });
  const badgeText = await page.locator("[data-testid='devops-mr-ready'] .badge, [data-testid='devops-mr-ready'] span").first().textContent();
  expect(badgeText?.includes("BLOCK") || badgeText?.includes("block")).toBeTruthy();
});

test("devops-pro-5 – Pipeline Analyzer tab visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("devops-tab-pipeline")).toBeVisible();
});

test("devops-pro-6 – Pipeline Analyzer analyze → result visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("devops-tab-pipeline").click();
  await expect(page.getByTestId("devops-pipe-analyze")).toBeVisible({ timeout: 5000 });
  await page.getByTestId("devops-pipe-log-input").fill("Error: Java heap space\nOOM killed\n");
  await page.getByTestId("devops-pipe-analyze").click();
  await expect(page.getByTestId("devops-pipe-ready")).toBeVisible({ timeout: 15000 });
});

test("devops-pro-7 – Artifacts tab visible and build button present", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("devops-tab-artifacts").click();
  await expect(page.getByTestId("devops-artifacts-build")).toBeVisible({ timeout: 5000 });
});

test("devops-pro-8 – Build artifact pack → ready + download button", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("devops-tab-artifacts").click();
  await page.getByTestId("devops-artifacts-build").click();
  await expect(page.getByTestId("devops-artifacts-ready")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("devops-download-pack")).toBeVisible();
});
