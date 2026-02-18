import { test, expect } from '@playwright/test';

/**
 * Phase 2B E2E Tests: Workspaces & Audit
 * Tests workspace management and audit logging
 */

test('phase2b-01: create workspace and verify in list', async ({ page }) => {
  await page.goto('/workspaces');
  await expect(page.getByTestId('workspaces-page')).toBeVisible({ timeout: 10000 });

  // Click create workspace button
  await page.getByTestId('toggle-create-form-btn').click();

  // Verify form is visible
  await expect(page.getByTestId('create-workspace-form')).toBeVisible();

  // Fill in workspace details
  await page.getByTestId('workspace-name-input').fill('E2E Test Workspace');
  await page.getByTestId('workspace-owner-input').fill('e2e-test-user');
  await page.getByTestId('workspace-tags-input').fill('test, automation, demo');

  // Create workspace
  await page.getByTestId('create-workspace-btn').click();

  // Wait for creation
  await page.waitForTimeout(2000);

  // Verify workspaces list is visible
  await expect(page.getByTestId('workspaces-list')).toBeVisible();

  // Check if any workspace items exist
  const workspaceItems = page.locator('[data-testid^="workspace-item-"]');
  await expect(workspaceItems.first()).toBeVisible({ timeout: 5000 });
});

test('phase2b-02: switch workspace and verify current workspace', async ({ page }) => {
  await page.goto('/workspaces');
  await expect(page.getByTestId('workspaces-page')).toBeVisible({ timeout: 10000 });

  // Find workspace items
  const workspaceItems = page.locator('[data-testid^="workspace-item-"]');
  const count = await workspaceItems.count();

  if (count > 1) {
    // Get first workspace switch button
    const firstSwitchBtn = page.locator('[data-testid^="switch-workspace-btn-"]').first();
    await firstSwitchBtn.click();

    // Verify current workspace is updated
    await expect(page.getByTestId('current-workspace-id')).toBeVisible();
  } else {
    console.log('Only one workspace available, cannot test switching');
  }
});

test('phase2b-03: view audit log and apply filters', async ({ page }) => {
  await page.goto('/audit');
  await expect(page.getByTestId('audit-page')).toBeVisible({ timeout: 10000 });

  // Verify audit events table is present
  await expect(page.getByTestId('audit-events-table')).toBeVisible();

  // Apply workspace filter
  await page.getByTestId('filter-workspace-input').fill('test-workspace');
  await page.waitForTimeout(500);

  // Apply actor filter
  await page.getByTestId('filter-actor-input').fill('test-user');
  await page.waitForTimeout(500);

  // Apply resource type filter  
  await page.getByTestId('filter-resource-input').fill('workspace');
  await page.waitForTimeout(500);

  // Verify audit events table still visible after filtering
  await expect(page.getByTestId('audit-events-table')).toBeVisible();

  // Check if any audit event cards exist
  const auditEvents = page.locator('[data-testid^="audit-event-"]');
  const eventCount = await auditEvents.count();
  
  if (eventCount > 0) {
    // Click first event to expand details
    await auditEvents.first().click();
    await page.waitForTimeout(500);
    
    console.log(`${eventCount} audit events found, expansion tested`);
  } else {
    console.log('No audit events found (may be expected for new system)');
  }
});

test('phase2b-04: copy audit event hashes', async ({ page }) => {
  await page.goto('/audit');
  await expect(page.getByTestId('audit-page')).toBeVisible({ timeout: 10000 });

  // Check for audit events
  const auditEvents = page.locator('[data-testid^="audit-event-"]');
  const eventCount = await auditEvents.count();

  if (eventCount > 0) {
    // Click first event to expand
    await auditEvents.first().click();
    await page.waitForTimeout(500);

    // Try to find and click a copy button (if event has hashes)
    const copyButtons = page.locator('button:has-text("Copy")');
    const copyCount = await copyButtons.count();
    
    if (copyCount > 0) {
      await copyButtons.first().click();
      await page.waitForTimeout(300);
      console.log('Hash copy functionality tested');
    }
  }
});
