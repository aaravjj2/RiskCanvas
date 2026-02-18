import { test, expect } from "@playwright/test";

/**
 * E2E – SRE Playbooks (Wave 10 v4.0)
 * retries: 0, workers: 1, ONLY data-testid selectors
 */

test("sre-1 – SRE page loads via nav-sre", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("nav-sre").click();
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
});

test("sre-2 – SRE page has generate button", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await expect(page.getByTestId("sre-generate")).toBeVisible();
});

test("sre-3 – generate empty playbook → playbook-ready visible", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
});

test("sre-4 – export MD button visible after generation", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("sre-export-md")).toBeVisible();
});

test("sre-5 – policy blocked param escalates to P0 triage", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sre-param-policy-blocked").check();
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  const playbook = await page.getByTestId("sre-playbook-ready").textContent();
  expect(playbook).toMatch(/P0|triage/i);
});

test("sre-6 – pipeline fatals param escalates to P0", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sre-param-fatals").fill("3");
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  const playbook = await page.getByTestId("sre-playbook-ready").textContent();
  expect(playbook).toMatch(/P0|triage/i);
});

test("sre-7 – steps list visible in playbook", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });
  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("sre-steps-list")).toBeVisible();
});

test("sre-8 – generate twice produces same playbook hash", async ({ page }) => {
  await page.goto("/sre");
  await expect(page.getByTestId("sre-page")).toBeVisible({ timeout: 10000 });

  await page.getByTestId("sre-generate").click();
  await expect(page.getByTestId("sre-playbook-ready")).toBeVisible({ timeout: 15000 });
  const hash1Text = await page.locator("[data-testid='sre-playbook-ready'] p").first().textContent();

  // Generate again
  await page.getByTestId("sre-generate").click();
  await page.waitForTimeout(1000);
  const hash2Text = await page.locator("[data-testid='sre-playbook-ready'] p").first().textContent();

  expect(hash1Text).toBe(hash2Text);
});
