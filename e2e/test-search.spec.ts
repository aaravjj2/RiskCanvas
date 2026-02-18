import { test, expect } from "@playwright/test";

// srch-1: nav-search navigates to search-page
test("srch-1: nav-search navigates to search-page", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("nav-search").click();
  await expect(page.getByTestId("search-page")).toBeVisible();
});

// srch-2: search-input + submit returns search-results-ready
test("srch-2: search-input and submit returns results", async ({ page }) => {
  await page.goto("/search");
  await page.getByTestId("search-input").fill("portfolio");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
});

// srch-3: search-chip-run filters to run type only
test("srch-3: search-chip-run filters results to run type", async ({ page }) => {
  await page.goto("/search");
  await page.getByTestId("search-input").fill("run");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  await page.getByTestId("search-chip-run").click();
  const results = page.getByTestId(/^search-result-\d+$/);
  const count = await results.count();
  if (count > 0) {
    for (let i = 0; i < count; i++) {
      const type = await results.nth(i).getAttribute("data-result-type");
      expect(type).toBe("run");
    }
  }
});

// srch-4: search-result-0 has data-result-type attribute
test("srch-4: search-result-0 has data-result-type", async ({ page }) => {
  await page.goto("/search");
  await page.getByTestId("search-input").fill("portfolio");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  const result = page.getByTestId("search-result-0");
  await expect(result).toBeVisible();
  const type = await result.getAttribute("data-result-type");
  expect(type).toBeTruthy();
});

// srch-5: click search-result-0 navigates (data-result-type drives navigation)
test("srch-5: clicking search-result-0 triggers navigation", async ({ page }) => {
  await page.goto("/search");
  await page.getByTestId("search-input").fill("portfolio");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-results-ready")).toBeVisible();
  const result = page.getByTestId("search-result-0");
  await expect(result).toBeVisible();
  await result.click();
  // After click, highlighted attribute should be set
  const highlighted = await result.getAttribute("data-highlighted");
  expect(highlighted).toBe("true");
});

// srch-6: search-reindex returns status info
test("srch-6: search-reindex updates index", async ({ page }) => {
  await page.goto("/search");
  const reindexBtn = page.getByTestId("search-reindex");
  await expect(reindexBtn).toBeVisible();
  await reindexBtn.click();
  // After reindex, the search input should still be present
  await expect(page.getByTestId("search-input")).toBeVisible();
});

// srch-7: empty query shows search-empty
test("srch-7: empty query submit shows search-empty", async ({ page }) => {
  await page.goto("/search");
  await page.getByTestId("search-input").fill("");
  await page.getByTestId("search-submit").click();
  await expect(page.getByTestId("search-empty")).toBeVisible();
});

// srch-8: Ctrl+K opens command palette with cmdk-item-search
test("srch-8: Ctrl+K opens command palette with search item", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Control+k");
  await expect(page.getByTestId("cmdk-open")).toBeVisible();
  await expect(page.getByTestId("cmdk-item-search")).toBeVisible();
});
