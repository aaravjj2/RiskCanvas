import { test, expect, Page } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const SHOTS_DIR = path.join(__dirname, "..", "test-results", "screenshots-w19w25-mega");

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS_DIR, `${name}.png`), fullPage: true });
}

test(
  "phase25-mega-judge-demo: Waves 19-25 full mega tour (v4.26-v4.49)",
  { tag: "@judge" },
  async ({ page }) => {
    // STEP 1: Dashboard & version badge
    await page.goto("/");
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await shot(page, "01-dashboard");
    await expect(page.getByTestId("version-badge")).toContainText("v4.49");
    await shot(page, "02-version-badge-v4-49");

    // STEP 2: FX Risk (Wave 19 — v4.26-v4.29)
    await page.getByTestId("nav-fx").click();
    await expect(page.getByTestId("fx-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "03-fx-page");

    await page.getByTestId("fx-spot-btn").click();
    await expect(page.getByTestId("fx-spot-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "04-fx-spot-ready");

    await page.getByTestId("fx-exposure-btn").click();
    await expect(page.getByTestId("fx-exposure-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "05-fx-exposure-ready");

    await page.getByTestId("fx-shock-btn").click();
    await expect(page.getByTestId("fx-shock-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "06-fx-shock-ready");

    await page.getByTestId("fx-export-btn").click();
    await expect(page.getByTestId("fx-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "07-fx-export-ready");

    // STEP 3: Credit Risk (Wave 20 — v4.30-v4.33)
    await page.getByTestId("nav-credit").click();
    await expect(page.getByTestId("credit-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "08-credit-page");

    await page.getByTestId("credit-curves-btn").click();
    await expect(page.getByTestId("credit-curve-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "09-credit-curves-ready");

    await page.getByTestId("credit-risk-btn").click();
    await expect(page.getByTestId("credit-risk-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "10-credit-risk-ready");

    await page.getByTestId("credit-export-btn").click();
    await expect(page.getByTestId("credit-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "11-credit-export-ready");

    // STEP 4: Liquidity (Wave 21 — v4.34-v4.37)
    await page.getByTestId("nav-liquidity").click();
    await expect(page.getByTestId("liq-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "12-liq-page");

    await page.getByTestId("liq-haircut-btn").click();
    await expect(page.getByTestId("liq-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "13-liq-haircut-ready");

    await page.getByTestId("liq-tcost-btn").click();
    await expect(page.getByTestId("liq-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "14-liq-tcost-ready");

    await page.getByTestId("liq-export-btn").click();
    await expect(page.getByTestId("liq-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "15-liq-export-ready");

    // STEP 5: Approvals (Wave 22 — v4.38-v4.41)
    await page.getByTestId("nav-approvals").click();
    await expect(page.getByTestId("approvals-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "16-approvals-page");

    await expect(page.getByTestId("approvals-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "17-approvals-list");

    // Create a new approval
    await page.getByTestId("approvals-create-btn").click();
    await expect(page.getByTestId("approvals-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "18-approvals-created");

    // Click the DRAFT row to see detail
    const draftRow = page.locator('[data-testid^="approval-row-"]').first();
    await expect(draftRow).toBeVisible({ timeout: 10000 });
    await draftRow.click();
    await expect(page.getByTestId("approval-detail-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "19-approval-detail");

    // Submit and approve
    const submitBtn = page.getByTestId("approval-submit-btn");
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      await expect(page.getByTestId("approval-detail-ready")).toBeVisible({ timeout: 10000 });
      await shot(page, "20-approval-submitted");
      const approveBtn = page.getByTestId("approval-approve-btn");
      if (await approveBtn.isVisible()) {
        await approveBtn.click();
        await expect(page.getByTestId("approval-detail-ready")).toBeVisible({ timeout: 10000 });
        await shot(page, "21-approval-approved");
      }
    }

    // STEP 6: GitLab MR Compliance (Wave 23 — v4.42-v4.45)
    await page.getByTestId("nav-gitlab").click();
    await expect(page.getByTestId("gitlab-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "22-gitlab-page");

    await expect(page.getByTestId("gitlab-mr-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "23-gitlab-mr-list");

    const mrRow = page.locator('[data-testid^="gitlab-mr-row-"]').first();
    await expect(mrRow).toBeVisible({ timeout: 10000 });
    await mrRow.click();
    await expect(page.getByTestId("gitlab-diff-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "24-gitlab-diff-ready");

    await page.getByTestId("gitlab-export-btn").click();
    await expect(page.getByTestId("gitlab-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "25-gitlab-export-ready");

    // STEP 7: CI Intelligence (Wave 24 — v4.46-v4.47)
    await page.getByTestId("nav-ci").click();
    await expect(page.getByTestId("ci-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "26-ci-page");

    await expect(page.getByTestId("ci-list-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "27-ci-list");

    const pipelineRow = page.locator('[data-testid^="ci-pipeline-row-"]').first();
    await expect(pipelineRow).toBeVisible({ timeout: 10000 });
    await pipelineRow.click();
    await expect(page.getByTestId("ci-analysis-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "28-ci-analysis-ready");

    await page.getByTestId("ci-generate-btn").click();
    await expect(page.getByTestId("ci-template-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "29-ci-template-ready");

    await page.getByTestId("ci-export-btn").click();
    await expect(page.getByTestId("ci-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "30-ci-export-ready");

    // STEP 8: DevSecOps (Wave 25 — v4.48-v4.49)
    await page.getByTestId("nav-security").click();
    await expect(page.getByTestId("sec-page")).toBeVisible({ timeout: 10000 });
    await shot(page, "31-sec-page");

    await page.getByTestId("sec-scan-btn").click();
    await expect(page.getByTestId("sec-results-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "32-sec-scan-results");

    await page.getByTestId("sec-sbom-btn").click();
    await expect(page.getByTestId("sec-sbom-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "33-sec-sbom-ready");

    await page.getByTestId("sec-export-btn").click();
    await expect(page.getByTestId("sec-export-ready")).toBeVisible({ timeout: 10000 });
    await shot(page, "34-sec-export-ready");

    // Final: confirm version badge
    await page.goto("/");
    await expect(page.getByTestId("version-badge")).toContainText("v4.49");
    await shot(page, "35-final-version-v4-49");
  }
);
