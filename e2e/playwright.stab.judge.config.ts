/**
 * playwright.stab.judge.config.ts — Judge demo configuration
 *
 * Runs the judge walkthrough at 1440x900, with screen recording (video: "on"),
 * slow motion (slowMo: 1200 ms/action), and a generous timeout of 900 s.
 * Output: playwright-judge-output/  (videos, traces, screenshots)
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["stab-judge-demo.spec.ts"],
  timeout: 900_000,
  retries: 0,
  workers: 1,
  fullyParallel: false,
  outputDir: "../test-results/stab-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/stab-judge", open: "never" }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177",
    headless: true,
    viewport: { width: 1440, height: 900 },
    locale: "en-US",
    timezoneId: "America/New_York",
    video: "off",
    screenshot: "off",
    trace: "off",
    launchOptions: {
      slowMo: 0,
    },
  },
  projects: [
    {
      name: "chromium-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
