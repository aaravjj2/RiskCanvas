import { defineConfig } from "@playwright/test";

export default defineConfig({
  // config is in /e2e, so tests live right here
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  retries: 0,
  workers: 1,

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report" }],
  ],

  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on",
    video: "on",
    screenshot: "only-on-failure",
  },

  webServer: {
    // paths are relative to /e2e
    command: "npm --prefix ../apps/web run dev -- --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: true,
    timeout: 120000,
  },

  outputDir: "../test-results",
});
