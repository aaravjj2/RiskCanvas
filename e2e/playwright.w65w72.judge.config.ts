import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["phase72-judge-demo.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 900_000,
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
    launchOptions: { slowMo: 500 },
    video: { mode: "on", size: { width: 1440, height: 900 } },
  },
  outputDir: "../test-results/w65w72-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w65w72-judge", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w65w72-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
