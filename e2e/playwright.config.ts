import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 240000, // 240s (4 minutes) per test - allows for media capture tests

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report" }],
  ],

  use: {
    baseURL: "http://localhost:4174",
    headless: false, // Run headed for MCP visibility
    trace: "on",
    video: "on",
    screenshot: "on",
  },

  outputDir: "../test-results",

  // Start servers before tests - DISABLED (starting manually)
  // webServer: [
  //   {
  //     command: "cd ../apps/api && set DEMO_MODE=true&& set E2E_MODE=true&& set PYTHONPATH=C:\\RiskCanvas\\RiskCanvas\\packages\\engine&& python -m uvicorn main:app --host 127.0.0.1 --port 8090",
  //     port: 8090,
  //     timeout: 120000,
  //     reuseExistingServer: !process.env.CI,
  //     env: {
  //       DEMO_MODE: "true",
  //       E2E_MODE: "true",
  //       PYTHONPATH: "C:\\RiskCanvas\\RiskCanvas\\packages\\engine",
  //     },
  //   },
  //   {
  //     command: "cd ../apps/web && npx vite preview --port 4174 --host 127.0.0.1",
  //     port: 4174,
  //     timeout: 120000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});
