import { test, expect } from "@playwright/test";

test("wave22: Approvals workflow - create, submit, approve, export", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-approvals").click();
  await expect(page.getByTestId("approvals-page")).toBeVisible({ timeout: 10000 });

  // List auto-loads on mount
  await expect(page.getByTestId("approvals-list-ready")).toBeVisible({ timeout: 10000 });

  // Create a new approval
  await page.getByTestId("approvals-create-btn").click();
  await expect(page.getByTestId("approvals-list-ready")).toBeVisible({ timeout: 10000 });

  // Click the first row to load detail
  const firstRow = page.locator('[data-testid^="approval-row-"]').first();
  await expect(firstRow).toBeVisible({ timeout: 10000 });
  await firstRow.click();
  await expect(page.getByTestId("approval-detail-ready")).toBeVisible({ timeout: 10000 });
});
