import { test, expect } from "@playwright/test";

test("wave23: GitLab MR compliance - list MRs, view diff, export", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-gitlab").click();
  await expect(page.getByTestId("gitlab-page")).toBeVisible({ timeout: 10000 });

  // MR list auto-loads on mount
  await expect(page.getByTestId("gitlab-mr-list-ready")).toBeVisible({ timeout: 10000 });

  // Click first MR row to load diff
  const firstRow = page.locator('[data-testid^="gitlab-mr-row-"]').first();
  await expect(firstRow).toBeVisible({ timeout: 10000 });
  await firstRow.click();
  await expect(page.getByTestId("gitlab-diff-ready")).toBeVisible({ timeout: 10000 });

  // Export compliance pack
  await page.getByTestId("gitlab-export-btn").click();
  await expect(page.getByTestId("gitlab-export-ready")).toBeVisible({ timeout: 10000 });
});
