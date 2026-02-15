import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  retries: 0,
  workers: 1,

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report" }],
  ],

  use: {
    baseURL: "http://127.0.0.1:4174",
    headless: false, // Run headed for MCP visibility
    trace: "on",
    video: "on",
    screenshot: "on",
  },

  outputDir: "../test-results",
});
