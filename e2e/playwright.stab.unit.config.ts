import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-stab-unit.spec.ts"],
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
  outputDir: "../test-results/stab-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/stab-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-stab-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
