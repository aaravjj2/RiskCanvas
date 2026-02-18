import { test, expect } from "@playwright/test";

// act-1: nav-activity navigates to activity-page
test("act-1: nav-activity navigates to activity-page", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("nav-activity").click();
  await expect(page.getByTestId("activity-page")).toBeVisible();
});

// act-2: activity-feed-ready shows items
test("act-2: activity-feed-ready shows items", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  const items = page.getByTestId(/^activity-item-\d+$/);
  await expect(items.first()).toBeVisible();
});

// act-3: activity-item-0 has type badge
test("act-3: activity-item-0 has type badge", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  const item = page.getByTestId("activity-item-0");
  await expect(item).toBeVisible();
  await expect(item).toContainText(/run|report|audit|policy|eval|sre/i);
});

// act-4: filter by run.execute
test("act-4: filter by run.execute shows only run items", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await page.getByTestId("activity-filter-run-execute").click();
  const items = page.getByTestId(/^activity-item-\d+$/);
  const count = await items.count();
  // All visible items should be run.execute type
  for (let i = 0; i < count; i++) {
    await expect(items.nth(i)).toContainText(/run/i);
  }
});

// act-5: presence-ready shows users
test("act-5: presence-ready shows users", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("presence-ready")).toBeVisible();
  const users = page.getByTestId(/^presence-user-\d+$/);
  await expect(users.first()).toBeVisible();
});

// act-6: presence-user-0 has status attribute
test("act-6: presence-user-0 has data-status attribute", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("presence-ready")).toBeVisible();
  const user = page.getByTestId("presence-user-0");
  await expect(user).toBeVisible();
  const status = await user.getAttribute("data-status");
  expect(["online", "idle", "offline"]).toContain(status);
});

// act-7: activity-reset reloads feed
test("act-7: activity-reset reloads feed", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await page.getByTestId("activity-reset").click();
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  const items = page.getByTestId(/^activity-item-\d+$/);
  await expect(items.first()).toBeVisible();
});

// act-8: activity-refresh button works
test("act-8: activity-refresh button reloads feed", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
  await page.getByTestId("activity-refresh").click();
  await expect(page.getByTestId("activity-feed-ready")).toBeVisible();
});
