import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-stab-e2e.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 120_000,
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/stab-e2e",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/stab-e2e", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-stab-e2e",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
