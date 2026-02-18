import { test, expect } from "@playwright/test";

/**
 * v3.0 – Microsoft Mode Wizard E2E
 * Tests the 3-step wizard: Provider Status → MCP Tools → Multi-Agent Run
 * Uses only data-testid selectors.
 * retries: 0, workers: 1
 */

test("microsoft – page loads with wizard step 1", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("wizard-step-1")).toBeVisible();
});

test("microsoft – provider status card visible on step 1", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("provider-status-card")).toBeVisible();
});

test("microsoft – step indicators present", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("wizard-step-indicator-0")).toBeVisible();
  await expect(page.getByTestId("wizard-step-indicator-1")).toBeVisible();
  await expect(page.getByTestId("wizard-step-indicator-2")).toBeVisible();
});

test("microsoft – next button advances to step 2", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  const nextBtn = page.getByTestId("wizard-next-btn");
  await expect(nextBtn).toBeVisible();
  await nextBtn.click();

  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
});

test("microsoft – step 2 shows mcp tools list", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("mcp-tools-list")).toBeVisible({ timeout: 10000 });
});

test("microsoft – step 2 mcp test call button exists", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("mcp-test-call-button")).toBeVisible();
});

test("microsoft – step 2 back button returns to step 1", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-back-btn").click();
  await expect(page.getByTestId("wizard-step-1")).toBeVisible();
});

test("microsoft – advance to step 3", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  // Step 1 → 2
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });

  // Step 2 → 3
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible({ timeout: 10000 });
});

test("microsoft – step 3 multi-agent run button exists", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible({ timeout: 10000 });

  await expect(page.getByTestId("multi-agent-run-btn")).toBeVisible();
});

test("microsoft – run multi-agent pipeline produces audit log", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("multi-agent-run-btn").click();

  // Wait for audit log
  await expect(page.getByTestId("audit-log-table")).toBeVisible({ timeout: 30000 });
});

test("microsoft – run multi-agent pipeline produces sre checks", async ({ page }) => {
  await page.goto("/microsoft");
  await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-2")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("wizard-next-btn").click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("multi-agent-run-btn").click();

  await expect(page.getByTestId("sre-checks-list")).toBeVisible({ timeout: 30000 });
});
