/**
 * playwright.depth.e2e.config.ts — Depth Wave E2E contract tests
 * v5.56.1 → v5.60.0
 *
 * Validates: run outcomes, eval harness v3, explainability,
 *            policy gate v3, MCP tools v2, offline MR review
 *
 * Run with: npx playwright test --config e2e/playwright.depth.e2e.config.ts
 */
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: ["test-depth-e2e.spec.ts"],
  retries: 0,
  workers: 1,
  timeout: 120_000,
  use: {
    baseURL: "http://localhost:4178",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/depth-e2e",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/depth-e2e", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-depth-e2e",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
