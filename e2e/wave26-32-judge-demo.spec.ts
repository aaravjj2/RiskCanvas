import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const API = "http://localhost:8090";

/**
 * Wave 26-32 Mega Judge Demo
 * Sweeps all 7 capability clusters, generates the judge pack, and verifies
 * the final verdict is PASS with all 7 waves scoring 100.
 */
test("Wave 26-32 mega judge demo — PASS verdict", async ({ page }) => {
  // 1. Dashboard loads
  await page.goto(BASE);
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: "../test-results/w26-32-01-dashboard.png", fullPage: true });

  // 2. Wave 26: MR Review
  await page.getByTestId("nav-mr-review").click();
  await expect(page.getByTestId("mr-review-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("mr-plan-btn").click();
  await page.waitForTimeout(1200);
  await page.getByTestId("mr-run-btn").click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../test-results/w26-32-02-mr-review.png", fullPage: true });

  // 3. Wave 27: Incident Drills
  await page.getByTestId("nav-incidents").click();
  await expect(page.getByTestId("incidents-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("drill-run-btn").click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: "../test-results/w26-32-03-incidents.png", fullPage: true });

  // 4. Wave 28: Release Readiness
  await page.getByTestId("nav-readiness").click();
  await expect(page.getByTestId("readiness-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("readiness-evaluate-btn").click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: "../test-results/w26-32-04-readiness.png", fullPage: true });

  // 5. Wave 29: Workflow Studio
  await page.getByTestId("nav-workflows").click();
  await expect(page.getByTestId("workflows-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("wf-generate-btn").click();
  await page.waitForTimeout(1200);
  await page.getByTestId("wf-activate-btn").click();
  await page.waitForTimeout(1000);
  await page.getByTestId("wf-simulate-btn").click();
  await page.waitForTimeout(1200);
  await page.screenshot({ path: "../test-results/w26-32-05-workflows.png", fullPage: true });

  // 6. Wave 30: Policy Registry V2
  await page.getByTestId("nav-policies-v2").click();
  await expect(page.getByTestId("policies-v2-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("pv2-create-btn").click();
  await page.waitForTimeout(1000);
  await page.getByTestId("pv2-publish-btn").click();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: "../test-results/w26-32-06-policies-v2.png", fullPage: true });

  // 7. Wave 31: Search V2
  await page.getByTestId("nav-search-v2").click();
  await expect(page.getByTestId("search-v2-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sv2-query-input").fill("security");
  await page.getByTestId("sv2-search-btn").click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "../test-results/w26-32-07-search-v2.png", fullPage: true });

  // 8. Wave 32: Judge Mode — generate pack + verify PASS
  await page.getByTestId("nav-judge-mode").click();
  await expect(page.getByTestId("judge-mode-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("judge-generate-btn").click();
  await page.waitForTimeout(3000);
  await page.screenshot({ path: "../test-results/w26-32-08-judge-pack.png", fullPage: true });

  // 9. Verify API directly returns PASS
  const resp = await page.request.post(`${API}/judge/w26-32/generate-pack`, {
    data: {},
    headers: { "Content-Type": "application/json" },
  });
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body.summary.verdict).toBe("PASS");
  expect(body.summary.waves_evaluated).toBe(7);
  expect(body.summary.total_score).toBeGreaterThanOrEqual(700);

  // 10. Final dashboard screenshot
  await page.getByTestId("nav-judge-mode").click();
  await expect(page.getByTestId("judge-mode-page")).toBeVisible();
  await page.screenshot({ path: "../test-results/w26-32-09-final.png", fullPage: true });
});
