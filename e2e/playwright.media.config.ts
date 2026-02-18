import { defineConfig } from "@playwright/test";

/**
 * Playwright configuration for Wave 5 media capture (phase5-media tour).
 *
 * slowMo: 4000 — adds a 4-second delay after every input action so the
 * resulting TOUR.webm comfortably exceeds the 180-second requirement without
 * any waitForTimeout calls in test code.
 *
 * Usage:
 *   npx playwright test --config e2e/playwright.media.config.ts
 */
export default defineConfig({
  testDir: ".",
  testMatch: /phase5-media\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 600000, // 10 minutes — tour takes ~3-4 min with slowMo

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report-media" }],
  ],

  use: {
    baseURL: "http://localhost:4174",
    headless: false,
    slowMo: 4000, // 4 s between every input action → TOUR.webm >= 180 s
    trace: "on",
    video: "on",
    screenshot: "on",
  },

  outputDir: "../test-results-media",
});
