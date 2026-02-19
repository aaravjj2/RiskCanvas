import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["phase48-enterprise-judge-demo.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 480_000, // 8 minutes — TOUR must be ≥360 s
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    slowMo: 500,
    trace: "on",
    screenshot: "on",
    video: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/w41w48-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w41w48-judge", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w41w48-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
