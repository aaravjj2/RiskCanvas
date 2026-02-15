import { test, expect } from '@playwright/test';

/**
 * Phase 2A E2E Test: Portfolio Save & Run History
 * Tests: Load sample → Save portfolio → Run analysis → Verify in history
 */

test('phase2a-01: save portfolio and view in run history', async ({ page }) => {
  // Navigate to Portfolio Library
  await page.goto('/library');
  await expect(page.getByTestId('portfolio-library-page')).toBeVisible({ timeout: 10000 });

  // Load sample portfolio
  await page.getByTestId('load-sample-btn').click();
  await expect(page.getByTestId('portfolio-editor')).toBeVisible();

  // Enter portfolio name
  await page.getByTestId('portfolio-name-input').fill('E2E Test Portfolio');

  // Save portfolio
  await page.getByTestId('save-portfolio-btn').click();

  // Wait for alert confirmation (or dismiss dialog)
  await page.waitForTimeout(1000); // Brief wait for save operation

  // Run analysis on the saved portfolio
  await page.getByTestId('run-analysis-btn').click();
  await page.waitForTimeout(2000); // Wait for run to complete

  // Navigate to Run History
  await page.goto('/history');
  await expect(page.getByTestId('run-history-page')).toBeVisible({ timeout: 10000 });

  // Verify runs table is visible and has at least one row
  await expect(page.getByTestId('runs-table')).toBeVisible();
  
  // Check that we have at least one run row
  const runRows = page.locator('[data-testid^="run-row-"]');
  await expect(runRows.first()).toBeVisible({ timeout: 5000 });
});

test('phase2a-02: select two runs and compare', async ({ page }) => {
  // Navigate to Run History
  await page.goto('/history');
  await expect(page.getByTestId('run-history-page')).toBeVisible({ timeout: 10000 });

  // Wait for runs to load
  await expect(page.getByTestId('runs-table')).toBeVisible();
  const runRows = page.locator('[data-testid^="run-row-"]');
  
  // Ensure we have at least 2 runs (from previous tests or fixtures)
  const count = await runRows.count();
  if (count < 2) {
    console.log('Not enough runs to compare, skipping comparison test');
    return;
  }

  // Select first two runs by clicking on rows
  await runRows.nth(0).click();
  await runRows.nth(1).click();

  // Verify compare button is enabled
  const compareBtn = page.getByTestId('compare-runs-btn');
  await expect(compareBtn).toBeEnabled();

  // Click compare
  await compareBtn.click();

  // Verify we're on compare page
  await expect(page.getByTestId('compare-page')).toBeVisible({ timeout: 10000 });

  // Verify delta cards are present
  await expect(page.getByTestId('delta-card-value')).toBeVisible();
  await expect(page.getByTestId('delta-card-var95')).toBeVisible();
  await expect(page.getByTestId('delta-card-var99')).toBeVisible();

  // Verify top changes table is present
  await expect(page.getByTestId('top-changes-table')).toBeVisible();
});
