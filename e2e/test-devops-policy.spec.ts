import { test, expect } from "@playwright/test";

/**
 * v3.1 – DevOps Policy Gate E2E
 * Tests the policy gate tab in the DevOps page.
 * Uses only data-testid selectors.
 * retries: 0, workers: 1
 */

test("devops policy – tab exists in DevOps page", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("devops-tab-policy")).toBeVisible();
});

test("devops policy – clicking tab shows policy panel", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();
  await expect(page.getByTestId("devops-panel-policy")).toBeVisible();
});

test("devops policy – evaluate button visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();
  await expect(page.getByTestId("policy-evaluate-btn")).toBeVisible();
});

test("devops policy – export buttons visible", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();
  await expect(page.getByTestId("export-markdown-btn")).toBeVisible();
  await expect(page.getByTestId("export-json-btn")).toBeVisible();
});

test("devops policy – evaluate clean diff shows allow badge", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();

  // Enter a clean diff
  const diffInput = page.getByTestId("policy-diff-input");
  await diffInput.fill("+def calculate_risk():\n+    return 0.05\n");

  await page.getByTestId("policy-evaluate-btn").click();

  // Wait for result badge
  const badge = page.getByTestId("policy-result-badge");
  await expect(badge).toBeVisible({ timeout: 15000 });
  await expect(badge).toContainText("ALLOW");
});

test("devops policy – evaluate dirty diff shows block badge", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();

  // Enter a dirty diff with secrets
  const diffInput = page.getByTestId("policy-diff-input");
  await diffInput.fill('+api_key = "sk-1234567890abcdef"\n+password = "s3cr3tPass"\n');

  await page.getByTestId("policy-evaluate-btn").click();

  const badge = page.getByTestId("policy-result-badge");
  await expect(badge).toBeVisible({ timeout: 15000 });
  await expect(badge).toContainText("BLOCK");
});

test("devops policy – export markdown shows preview", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("devops-tab-policy").click();

  await page.getByTestId("export-markdown-btn").click();

  await expect(page.getByTestId("policy-export-section")).toBeVisible({ timeout: 15000 });
});
