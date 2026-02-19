import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["phase64-judge-demo.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 600_000,
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
    launchOptions: { slowMo: 500 },
  },
  outputDir: "../test-results/w57w64-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w57w64-judge", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w57w64-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
