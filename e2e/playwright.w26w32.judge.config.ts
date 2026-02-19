import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /wave26-32-judge-demo\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 120000,
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177",
    headless: true,
    video: "on",
    trace: "on",
    screenshot: "on",
  },
  outputDir: "../test-results",
});
