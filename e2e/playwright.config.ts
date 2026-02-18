import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
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

  // Projects: uiunit runs the harness spec before the main suite.
  projects: [
    {
      name: "uiunit",
      testMatch: /test-ui-harness\.spec\.ts/,
    },
    {
      name: "main",
      testMatch: /(?<!test-ui-harness)\.spec\.ts$/,
      dependencies: ["uiunit"],
    },
  ],
});

