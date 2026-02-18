import { test, expect } from "@playwright/test";

/**
 * v2.9 – Platform Health E2E
 * Tests the Platform health dashboard page.
 * Uses only data-testid selectors.
 * retries: 0, workers: 1
 */

test("platform – nav item exists and navigates", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  const navPlatform = page.getByTestId("nav-platform");
  await expect(navPlatform).toBeVisible();
  await navPlatform.click();

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
});

test("platform – health card visible", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("platform-health-card")).toBeVisible();
});

test("platform – readiness card visible", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("platform-readiness-card")).toBeVisible();
});

test("platform – liveness card visible", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("platform-liveness-card")).toBeVisible();
});

test("platform – infra card visible", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("platform-infra-card")).toBeVisible();
});

test("platform – port badge shows 8090", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  const badge = page.getByTestId("platform-port-badge");
  await expect(badge).toBeVisible({ timeout: 15000 });
  await expect(badge).toContainText("8090");
});

test("platform – refresh button works", async ({ page }) => {
  await page.goto("/platform");

  await expect(page.getByTestId("platform-page")).toBeVisible({ timeout: 10000 });
  const refreshBtn = page.getByTestId("platform-refresh-btn");
  await expect(refreshBtn).toBeVisible();
  await refreshBtn.click();
  // After click, page should still show the platform page
  await expect(page.getByTestId("platform-page")).toBeVisible();
});

test("platform – version badge shows v3.2.0", async ({ page }) => {
  await page.goto("/platform");
  await expect(page.getByTestId("version-badge")).toContainText("v3.2.0");
});
