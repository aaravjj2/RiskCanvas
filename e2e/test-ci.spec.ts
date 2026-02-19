import { test, expect } from "@playwright/test";

test("wave24: CI Intelligence - list pipelines, analyze, generate template", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-ci").click();
  await expect(page.getByTestId("ci-page")).toBeVisible({ timeout: 10000 });

  // Pipeline list auto-loads on mount
  await expect(page.getByTestId("ci-list-ready")).toBeVisible({ timeout: 10000 });

  // Click first pipeline row to analyze
  const firstRow = page.locator('[data-testid^="ci-pipeline-row-"]').first();
  await expect(firstRow).toBeVisible({ timeout: 10000 });
  await firstRow.click();
  await expect(page.getByTestId("ci-analysis-ready")).toBeVisible({ timeout: 10000 });

  // Generate CI template
  await page.getByTestId("ci-generate-btn").click();
  await expect(page.getByTestId("ci-template-ready")).toBeVisible({ timeout: 10000 });

  // Export pack
  await page.getByTestId("ci-export-btn").click();
  await expect(page.getByTestId("ci-export-ready")).toBeVisible({ timeout: 10000 });
});
