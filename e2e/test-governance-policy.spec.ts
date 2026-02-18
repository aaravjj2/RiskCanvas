import { test, expect } from "@playwright/test";

/**
 * E2E – Governance Policy Engine v2 (Wave 9 v3.7)
 * retries: 0, workers: 1, ONLY data-testid selectors
 */

test("gov-1 – governance page loads with policy tab", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("gov-tab-policy")).toBeVisible();
});

test("gov-2 – navigate to policy tab, evaluate button visible", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-policy").click();
  await expect(page.getByTestId("gov-validate-btn")).toBeVisible({ timeout: 5000 });
});

test("gov-3 – evaluate policy with default tools → allow", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-policy").click();
  await page.getByTestId("gov-validate-btn").click();
  await expect(page.getByTestId("gov-policy-ready")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("gov-validate-result")).toBeVisible();
});

test("gov-4 – narrative tab visible and validate button present", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-narrative").click();
  await expect(page.getByTestId("gov-validate-narrative-btn")).toBeVisible({ timeout: 5000 });
});

test("gov-5 – narrative validate shows result", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-narrative").click();
  await page.getByTestId("gov-narrative-text").fill("The portfolio value is 18250.75 USD.");
  await page.getByTestId("gov-validate-narrative-btn").click();
  await expect(page.getByTestId("gov-narrative-badge")).toBeVisible({ timeout: 10000 });
});

test("gov-6 – suites tab loads suites after clicking load", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-suites").click();
  await page.getByTestId("gov-load-suites-btn").click();
  await expect(page.getByTestId("eval-suites-list")).toBeVisible({ timeout: 10000 });
});

test("gov-7 – run governance policy suite shows scorecard", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-suites").click();
  await page.getByTestId("gov-load-suites-btn").click();
  await expect(page.getByTestId("eval-suites-list")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("eval-run-btn-governance_policy_suite").click();
  await expect(page.getByTestId("eval-scorecard-ready")).toBeVisible({ timeout: 15000 });
});

test("gov-8 – export scorecard MD button present after run", async ({ page }) => {
  await page.goto("/governance");
  await expect(page.getByTestId("governance-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("gov-tab-suites").click();
  await page.getByTestId("gov-load-suites-btn").click();
  await expect(page.getByTestId("eval-suites-list")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("eval-run-btn-governance_policy_suite").click();
  await expect(page.getByTestId("eval-scorecard-ready")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("eval-export-md")).toBeVisible();
});
