import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /phase12-judge-demo\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 600000,
  use: {
    baseURL: "http://localhost:4174",
    headless: false,
    slowMo: 4000,
    video: "on",
    trace: "on",
    screenshot: "on",
  },
  outputDir: "../test-results",
});
