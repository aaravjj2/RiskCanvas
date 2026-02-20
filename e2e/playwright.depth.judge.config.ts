/**
 * playwright.depth.judge.config.ts — Depth Wave judge demo v5
 * v5.56.1 → v5.60.0
 *
 * Requirements:
 *   - video=on (TOUR.webm ≥ 240s)
 *   - trace=on, screenshot=on
   *   - slowMo=7500 (ensures TOUR duration ≥ 240s across 17 tests)
 *   - vite preview only (port 4178), NOT dev server
 *
 * Run with: npx playwright test --config e2e/playwright.depth.judge.config.ts
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["phase60-judge-demo-v5.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 1_200_000,
  use: {
    baseURL: "http://localhost:4178",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
    launchOptions: { slowMo: 7500 },
    video: { mode: "on", size: { width: 1440, height: 900 } },
  },
  outputDir: "../test-results/depth-judge",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/depth-judge", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-depth-judge",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
