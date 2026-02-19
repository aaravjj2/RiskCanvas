import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-w41-w48-unit.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/w41w48-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w41w48-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w41w48-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
