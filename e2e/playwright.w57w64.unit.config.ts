import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-w57-w64-unit.spec.ts"],
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
  outputDir: "../test-results/w57w64-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w57w64-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w57w64-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
