import { defineConfig, devices } from "@playwright/test";

/**
 * Wave 9+10 Judge Demo Config
 * - slowMo: 4000ms (tuned for ≥180s TOUR.webm)
 * - video: on (produces TOUR.webm)
 * - retries: 0, workers: 1 (deterministic per CLAUDE.md)
 */
export default defineConfig({
  testDir: ".",
  testMatch: /phase10-judge-demo\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 600000, // 10 minutes – allows slow-mo + captures

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report-w9w10" }],
  ],

  use: {
    baseURL: "http://localhost:4174",
    headless: false,
    trace: "on",
    video: "on",
    screenshot: "on",
    slowMo: 4000, // 4s between actions → ~180s+ for 28-screenshot test
  },

  outputDir: "../test-results",
});
