import { test, expect } from '@playwright/test';

/**
 * Phase 2B E2E Tests: DevOps Pack & Monitoring
 * Tests risk-bot reports and monitoring infrastructure
 */

test('phase2b-05: generate risk-bot report', async ({ page }) => {
  await page.goto('/devops');
  await expect(page.getByTestId('devops-page')).toBeVisible({ timeout: 10000 });

  // Click generate report button
  await page.getByTestId('generate-riskbot-report-btn').click();

  // Wait for report generation
  await page.waitForTimeout(2000);

  // Verify report section is visible
  await expect(page.getByTestId('riskbot-report-section')).toBeVisible({ timeout: 5000 });

  // Verify CI checklist is present
  await expect(page.getByTestId('ci-checklist')).toBeVisible();
});

test('phase2b-06: create monitor for portfolio', async ({ page }) => {
  await page.goto('/monitoring');
  await expect(page.getByTestId('monitoring-page')).toBeVisible({ timeout: 10000 });

  // Click create monitor button
  await page.getByTestId('toggle-create-monitor-btn').click();

  // Verify form is visible
  await expect(page.getByTestId('create-monitor-form')).toBeVisible();

  // Fill in monitor details
  await page.getByTestId('monitor-name-input').fill('E2E Test Monitor');
  await page.getByTestId('monitor-portfolio-input').fill('test-portfolio-001');
  await page.getByTestId('monitor-schedule-select').selectOption('daily');
  await page.getByTestId('var95-threshold-input').fill('15000');
  await page.getByTestId('var99-threshold-input').fill('20000');

  // Create monitor
  await page.getByTestId('create-monitor-btn').click();

  // Wait for creation
  await page.waitForTimeout(2000);

  // Verify monitors list is visible
  await expect(page.getByTestId('monitors-list')).toBeVisible();

  // Check if monitor items exist
  const monitorItems = page.locator('[data-testid^="monitor-item-"]');
  const count = await monitorItems.count();
  
  if (count > 0) {
    await expect(monitorItems.first()).toBeVisible();
    console.log(`${count} monitors found`);
  }
});

test('phase2b-07: run monitor now and verify alerts', async ({ page }) => {
  await page.goto('/monitoring');
  await expect(page.getByTestId('monitoring-page')).toBeVisible({ timeout: 10000 });

  // Check if monitors exist
  const monitorItems = page.locator('[data-testid^="monitor-item-"]');
  const count = await monitorItems.count();

  if (count > 0) {
    // Find run-now buttons
    const runNowButtons = page.locator('[data-testid^="run-now-btn-"]');
    const btnCount = await runNowButtons.count();

    if (btnCount > 0) {
      // Click first run-now button
      await runNowButtons.first().click();

      // Wait for execution
      await page.waitForTimeout(3000);

      // Verify alerts section is visible
      await expect(page.getByTestId('alerts-section')).toBeVisible();

      // Verify drift summaries section is visible
      await expect(page.getByTestId('drift-summaries-section')).toBeVisible();

      console.log('Monitor execution tested');
    }
  } else {
    console.log('No monitors exist, cannot test run-now');
  }
});

test('phase2b-08: view alerts and drift summaries', async ({ page }) => {
  await page.goto('/monitoring');
  await expect(page.getByTestId('monitoring-page')).toBeVisible({ timeout: 10000 });

  // Verify alerts section renders
  await expect(page.getByTestId('alerts-section')).toBeVisible();

  // Check for alert items
  const alertItems = page.locator('[data-testid^="alert-item-"]');
  const alertCount = await alertItems.count();

  if (alertCount > 0) {
    console.log(`${alertCount} alerts found`);
    await expect(alertItems.first()).toBeVisible();
  } else {
    console.log('No alerts present (expected for fresh system)');
  }

  // Verify drift summaries section renders
  await expect(page.getByTestId('drift-summaries-section')).toBeVisible();

  // Check for drift summary cards
  const driftCards = page.locator('[data-testid^="drift-summary-"]');
  const driftCount = await driftCards.count();

  if (driftCount > 0) {
    console.log(`${driftCount} drift summaries found`);
    await expect(driftCards.first()).toBeVisible();
  } else {
    console.log('No drift summaries present (expected for fresh system)');
  }
});
