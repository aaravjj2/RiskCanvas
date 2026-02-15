import { test, expect } from '@playwright/test';

/**
 * Comprehensive Tour Test (≥180s)
 * This test chains Phase 2A + 2B flows for the proof pack video
 * 
 * Flow: Dashboard → Library (save) → Run → History → Compare → 
 *       Reports → Hedge → Workspaces → Audit → DevOps → Monitoring
 */

test('phase2-tour: comprehensive end-to-end flow (≥180s)', async ({ page }) => {
  console.log('=== TOUR START: Phase 2A+2B Comprehensive Demo ===');

  // 1. Dashboard (baseline)
  console.log('[1/12] Dashboard');
  await page.goto('/');
  await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(3000);

  // 2. Portfolio Library - Load sample
  console.log('[2/12] Portfolio Library - Load Sample');
  await page.goto('/library');
  await expect(page.getByTestId('portfolio-library-page')).toBeVisible({ timeout: 10000 });
  await page.getByTestId('load-sample-btn').click();
  await expect(page.getByTestId('portfolio-editor')).toBeVisible();
  await page.waitForTimeout(2000);

  // 3. Portfolio Library - Save
  console.log('[3/12] Portfolio Library - Save Portfolio');
  await page.getByTestId('portfolio-name-input').fill('Tour Demo Portfolio');
  await page.getByTestId('save-portfolio-btn').click();
  await page.waitForTimeout(2000);

  // 4. Portfolio Library - Run Analysis
  console.log('[4/12] Portfolio Library - Run Analysis');
  await page.getByTestId('run-analysis-btn').click();
  await page.waitForTimeout(3000);

  // 5. Run History
  console.log('[5/12] Run History');
  await page.goto('/history');
  await expect(page.getByTestId('run-history-page')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('runs-table')).toBeVisible();
  await page.waitForTimeout(3000);

  // 6. Run History - Compare (if multiple runs exist)
  console.log('[6/12] Run History - Select & Compare');
  const runRows = page.locator('[data-testid^="run-row-"]');
  const runCount = await runRows.count();
  
  if (runCount >= 2) {
    await runRows.nth(0).click();
    await runRows.nth(1).click();
    await page.getByTestId('compare-runs-btn').click();
    await expect(page.getByTestId('compare-page')).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(3000);
  } else {
    console.log('[6/12] SKIP: Not enough runs for comparison');
    await page.waitForTimeout(2000);
  }

  // 7. Reports Hub
  console.log('[7/12] Reports Hub');
  await page.goto('/reports-hub');
  await expect(page.getByTestId('reports-hub-page')).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(3000);

  // 8. Hedge Studio
  console.log('[8/12] Hedge Studio');
  await page.goto('/hedge');
  await expect(page.getByTestId('hedge-studio-page')).toBeVisible({ timeout: 10000 });
  await page.getByTestId('portfolio-id-input').fill('tour-portfolio-001');
  await page.getByTestId('max-cost-input').fill('50000');
  await page.getByTestId('instrument-put-checkbox').check();
  await page.waitForTimeout(3000);

  // Generate hedges
  await page.getByTestId('generate-hedges-btn').click();
  await page.waitForTimeout(3000);

  // 9. Workspaces
  console.log('[9/12] Workspaces');
  await page.goto('/workspaces');
  await expect(page.getByTestId('workspaces-page')).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(2000);

  // Create workspace
  await page.getByTestId('toggle-create-form-btn').click();
  await expect(page.getByTestId('create-workspace-form')).toBeVisible();
  await page.getByTestId('workspace-name-input').fill('Tour Workspace');
  await page.getByTestId('workspace-owner-input').fill('tour-user');
  await page.getByTestId('workspace-tags-input').fill('demo, tour');
  await page.waitForTimeout(2000);
  await page.getByTestId('create-workspace-btn').click();
  await page.waitForTimeout(3000);

  // 10. Audit Log
  console.log('[10/12] Audit Log');
  await page.goto('/audit');
  await expect(page.getByTestId('audit-page')).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId('audit-events-table')).toBeVisible();
  await page.waitForTimeout(3000);

  // Expand first audit event if exists
  const auditEvents = page.locator('[data-testid^="audit-event-"]');
  const auditCount = await auditEvents.count();
  if (auditCount > 0) {
    await auditEvents.first().click();
    await page.waitForTimeout(2000);
  }

  // 11. DevOps Pack
  console.log('[11/12] DevOps Pack');
  await page.goto('/devops');
  await expect(page.getByTestId('devops-page')).toBeVisible({ timeout: 10000 });
  await page.getByTestId('generate-riskbot-report-btn').click();
  await page.waitForTimeout(3000);

  // Verify report section
  await expect(page.getByTestId('riskbot-report-section')).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(2000);

  // 12. Monitoring
  console.log('[12/12] Monitoring');
  await page.goto('/monitoring');
  await expect(page.getByTestId('monitoring-page')).toBeVisible({ timeout: 10000 });
  await page.waitForTimeout(2000);

  // Create monitor
  await page.getByTestId('toggle-create-monitor-btn').click();
  await expect(page.getByTestId('create-monitor-form')).toBeVisible();
  await page.getByTestId('monitor-name-input').fill('Tour Monitor');
  await page.getByTestId('monitor-portfolio-input').fill('tour-portfolio-001');
  await page.getByTestId('monitor-schedule-select').selectOption('daily');
  await page.getByTestId('var95-threshold-input').fill('10000');
  await page.getByTestId('var99-threshold-input').fill('15000');
  await page.waitForTimeout(2000);
  await page.getByTestId('create-monitor-btn').click();
  await page.waitForTimeout(3000);

  // Verify monitors list
  await expect(page.getByTestId('monitors-list')).toBeVisible();
  await page.waitForTimeout(2000);

  // Run monitor now if exists
  const monitorItems = page.locator('[data-testid^="monitor-item-"]');
  const monitorCount = await monitorItems.count();
  if (monitorCount > 0) {
    const runNowButtons = page.locator('[data-testid^="run-now-btn-"]');
    const btnCount = await runNowButtons.count();
    if (btnCount > 0) {
      await runNowButtons.first().click();
      await page.waitForTimeout(3000);
    }
  }

  // Verify alerts and drift sections
  await expect(page.getByTestId('alerts-section')).toBeVisible();
  await expect(page.getByTestId('drift-summaries-section')).toBeVisible();
  await page.waitForTimeout(3000);

  console.log('=== TOUR COMPLETE: All Phase 2A+2B features demonstrated ===');
  
  // Additional wait to ensure video captures final state
  await page.waitForTimeout(5000);
});
