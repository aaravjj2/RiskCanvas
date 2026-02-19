import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /test-(mr-review|incident-drills|release-readiness|workflow-studio|policies-v2|search-v2|judge-mode)\.spec\.ts$/,
  retries: 0,
  workers: 1,
  timeout: 60000,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
  },
  outputDir: "../test-results",
});
