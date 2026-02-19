import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-w49-w56-unit.spec.ts"],
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
  outputDir: "../test-results/w49w56-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w49w56-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w49w56-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
