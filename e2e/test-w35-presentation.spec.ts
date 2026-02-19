/**
 * test-w35-presentation.spec.ts
 * Wave 35 — Presentation Mode (guided demo rails)
 * v4.82-v4.85
 *
 * ALL selectors use data-testid ONLY.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";

test.describe("Wave 35 — Presentation Mode Toggle", () => {
  test("presentation-toggle exists in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("presentation-toggle")).toBeVisible();
  });

  test("clicking presentation-toggle enables presentation mode", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    // Step card should appear
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
  });

  test("presentation-step-title shows in step card", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-title")).toBeVisible({ timeout: 5000 });
    const title = await page.getByTestId("presentation-step-title").textContent();
    expect((title ?? "").length).toBeGreaterThan(0);
  });

  test("presentation-progress shows step counter", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-progress")).toBeVisible({ timeout: 5000 });
    const progress = await page.getByTestId("presentation-progress").textContent();
    expect(progress).toContain("Step 1");
  });

  test("presentation-next-btn advances step", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("presentation-next-btn").click();
    // Progress should now show Step 2
    const progress = await page.getByTestId("presentation-progress").textContent();
    expect(progress).toContain("Step 2");
  });

  test("rail select for microsoft story works", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("presentation-rail-select-microsoft").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-rail-select-microsoft").click();
    // Still on step 1 after switch
    const progress = await page.getByTestId("presentation-progress").textContent();
    expect(progress).toContain("Step 1");
  });

  test("presentation mode can be disabled again", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe("Wave 35 — Guided Rails", () => {
  test("gitlab rail steps are navigable (step 1)", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
    // Step 1 of gitlab rail: navigate to /mr-review
    await page.getByTestId("presentation-next-btn").click();
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
  });

  test("digitalocean rail is selectable", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 10000 });
    await page.getByTestId("presentation-toggle").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-toggle").click();
    await expect(page.getByTestId("presentation-step-card")).toBeVisible({ timeout: 5000 });
    await page.getByTestId("presentation-rail-select-digitalocean").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("presentation-rail-select-digitalocean").click();
    const title = await page.getByTestId("presentation-step-title").textContent();
    expect((title ?? "").length).toBeGreaterThan(0);
  });
});
