import { test, expect } from "@playwright/test";

test("wave25: DevSecOps - scan diff, get SBOM, export pack", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("nav-security").click();
  await expect(page.getByTestId("sec-page")).toBeVisible({ timeout: 10000 });

  // Scan for secrets
  await page.getByTestId("sec-scan-btn").click();
  await expect(page.getByTestId("sec-results-ready")).toBeVisible({ timeout: 10000 });

  // Get SBOM
  await page.getByTestId("sec-sbom-btn").click();
  await expect(page.getByTestId("sec-sbom-ready")).toBeVisible({ timeout: 10000 });

  // Export DevSecOps pack
  await page.getByTestId("sec-export-btn").click();
  await expect(page.getByTestId("sec-export-ready")).toBeVisible({ timeout: 10000 });
});
