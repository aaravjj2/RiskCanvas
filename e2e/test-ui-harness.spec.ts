import { test, expect } from "@playwright/test";

/**
 * test-ui-harness.spec.ts (v4.5.0)
 *
 * Validates the /__harness UI test harness page.
 * Replaces the removed Vitest suite with headed Playwright MCP checks.
 *
 * All selectors are data-testid only. No waitForTimeout. retries=0.
 */

test.beforeEach(async ({ page }) => {
  // Ensure demo mode is active so harness checks for demo headers work
  await page.context().addInitScript(() => {
    localStorage.setItem("RC_DEMO_MODE", "true");
  });
});

test("harness-1: harness-ready is visible and all-pass=true", async ({
  page,
}) => {
  await page.goto("/__harness");
  const ready = page.getByTestId("harness-ready");
  await expect(ready).toBeVisible();
  await expect(ready).toHaveAttribute("data-all-pass", "true");
});

test("harness-2: demo-headers-shape check passes", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  const row = page.getByTestId("harness-check-demo-headers-shape");
  await expect(row).toHaveAttribute("data-pass", "true");
  // expected hash must equal actual hash
  const expected = await row.getAttribute("data-expected-hash");
  const actual = await row.getAttribute("data-actual-hash");
  expect(actual).toBe(expected);
});

test("harness-3: auth-mode-demo check passes", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  const row = page.getByTestId("harness-check-auth-mode-demo");
  await expect(row).toHaveAttribute("data-pass", "true");
  const expected = await row.getAttribute("data-expected-hash");
  const actual = await row.getAttribute("data-actual-hash");
  expect(actual).toBe(expected);
});

test("harness-4: auth-headers-demo check passes", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  const row = page.getByTestId("harness-check-auth-headers-demo");
  await expect(row).toHaveAttribute("data-pass", "true");
});

test("harness-5: cmdk-command-count check passes (8 commands)", async ({
  page,
}) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  const row = page.getByTestId("harness-check-cmdk-command-count");
  await expect(row).toHaveAttribute("data-pass", "true");
  const expected = await row.getAttribute("data-expected-hash");
  const actual = await row.getAttribute("data-actual-hash");
  expect(actual).toBe(expected);
});

test("harness-6: cmdk-command-ids check passes (deterministic order)", async ({
  page,
}) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  const row = page.getByTestId("harness-check-cmdk-command-ids");
  await expect(row).toHaveAttribute("data-pass", "true");
});

test("harness-7: api mock portfolio checks pass", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  await expect(
    page.getByTestId("harness-check-api-demo-portfolio-len"),
  ).toHaveAttribute("data-pass", "true");
  await expect(
    page.getByTestId("harness-check-api-demo-portfolio-symbols"),
  ).toHaveAttribute("data-pass", "true");
});

test("harness-8: api mock determinism checks pass", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  await expect(
    page.getByTestId("harness-check-api-mock-determinism-passed"),
  ).toHaveAttribute("data-pass", "true");
  await expect(
    page.getByTestId("harness-check-api-mock-determinism-checks-len"),
  ).toHaveAttribute("data-pass", "true");
  await expect(
    page.getByTestId("harness-check-api-mock-analysis-request-id"),
  ).toHaveAttribute("data-pass", "true");
});

test("harness-9: SSE EventClient checks pass", async ({ page }) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  await expect(
    page.getByTestId("harness-check-sse-client-instantiate"),
  ).toHaveAttribute("data-pass", "true");
  await expect(
    page.getByTestId("harness-check-sse-client-add-handler"),
  ).toHaveAttribute("data-pass", "true");
  await expect(
    page.getByTestId("harness-check-sse-client-remove-handler"),
  ).toHaveAttribute("data-pass", "true");
});

test("harness-10: all checks present and no unexpected failures", async ({
  page,
}) => {
  await page.goto("/__harness");
  await expect(page.getByTestId("harness-ready")).toBeVisible();
  // Must be all-pass
  await expect(page.getByTestId("harness-ready")).toHaveAttribute(
    "data-all-pass",
    "true",
  );
  // All individual checks must be pass=true
  const allRows = page.locator("[data-testid^='harness-check-']");
  const count = await allRows.count();
  expect(count).toBeGreaterThanOrEqual(12);
  for (let i = 0; i < count; i++) {
    await expect(allRows.nth(i)).toHaveAttribute("data-pass", "true");
  }
});
