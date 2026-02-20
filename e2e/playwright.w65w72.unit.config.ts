import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-w65-w72-unit.spec.ts"],
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
  outputDir: "../test-results/w65w72-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w65w72-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w65w72-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
