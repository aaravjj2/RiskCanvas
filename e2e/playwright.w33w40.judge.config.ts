import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["phase39-ui-judge-demo.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 360_000, // 6 minutes – TOUR must be ≥300 s
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    slowMo: 500,
    trace: "on",
    screenshot: "on",
    video: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/w33w40-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w33w40-judge", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w33w40-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
