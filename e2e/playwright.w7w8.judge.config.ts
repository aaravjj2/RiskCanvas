import { defineConfig, devices } from "@playwright/test";
import path from "path";

/**
 * Wave 7+8 Judge Config
 * slowMo=4000 for screen recording, video always on
 * Generates TOUR artifacts under artifacts/proof/
 */
export default defineConfig({
  testDir: ".",
  testMatch: /phase8-judge-demo\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 600000, // 10 min per test — allows for TOUR recording

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report-w7w8" }],
  ],

  use: {
    baseURL: "http://localhost:4174",
    headless: false,
    slowMo: 4000, // 4s between each action for visibility
    trace: "on",
    video: "on",
    screenshot: "on",
    launchOptions: {
      args: ["--window-size=1920,1080"],
    },
    viewport: { width: 1920, height: 1080 },
  },

  outputDir: path.join(__dirname, "../test-results-w7w8"),
});
