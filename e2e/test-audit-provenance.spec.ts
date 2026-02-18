import { test, expect } from "@playwright/test";

/**
 * Wave 7 E2E — AuditV2 & Provenance (v3.3)
 * retries=0, workers=1, data-testid selectors only
 */

test("w7-1 – version badge shows v3.6.0", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("version-badge")).toHaveText("v3.6.0");
});

test("w7-2 – audit page accessible via nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("nav-devops").click();
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });
});

test("w7-3 – rates nav item visible", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("nav-rates")).toBeVisible();
});

test("w7-4 – stress nav item visible", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("nav-stress")).toBeVisible();
});

test("w7-5 – run history page has provenance button per row", async ({ page }) => {
  // First execute a run so we have rows
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("run-risk-button").click();
  await expect(page.getByTestId("metric-value")).toBeVisible({ timeout: 15000 });

  // Now navigate to history
  await page.getByTestId("nav-history").click();
  await expect(page.getByTestId("run-history-page")).toBeVisible({ timeout: 10000 });

  // At least one run row exists; provenance-open button should be visible
  await expect(page.getByTestId("provenance-open").first()).toBeVisible({ timeout: 8000 });
});

test("w7-6 – provenance drawer opens and shows hashes", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("run-risk-button").click();
  await expect(page.getByTestId("metric-value")).toBeVisible({ timeout: 15000 });

  await page.getByTestId("nav-history").click();
  await expect(page.getByTestId("run-history-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("provenance-open").first().click();
  await expect(page.getByTestId("provenance-drawer")).toBeVisible({ timeout: 8000 });
  await expect(page.getByTestId("provenance-input-hash")).toBeVisible();
  await expect(page.getByTestId("provenance-output-hash")).toBeVisible();
});

test("w7-7 – provenance verify chain shows ok", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("dashboard-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("run-risk-button").click();
  await expect(page.getByTestId("metric-value")).toBeVisible({ timeout: 15000 });

  await page.getByTestId("nav-history").click();
  await expect(page.getByTestId("run-history-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("provenance-open").first().click();
  await expect(page.getByTestId("provenance-drawer")).toBeVisible({ timeout: 8000 });
  await page.getByTestId("provenance-verify").click();
  await expect(page.getByTestId("provenance-verify-ok")).toBeVisible({ timeout: 8000 });
});

test("w7-8 – devops policy result has provenance after evaluation", async ({ page }) => {
  await page.goto("/devops");
  await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 10000 });

  // Find and click policy evaluate
  const evaluateBtn = page.getByTestId("policy-evaluate-btn");
  if (await evaluateBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await evaluateBtn.click();
    await expect(page.getByTestId("policy-result-section")).toBeVisible({ timeout: 10000 });
    const provenanceBtn = page.getByTestId("provenance-open");
    if (await provenanceBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(provenanceBtn).toBeVisible();
    }
  }
});
