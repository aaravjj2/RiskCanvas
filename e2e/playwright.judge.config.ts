import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the Wave 6 judge demo recording.
 * Uses slowMo: 4000ms for dramatic effect in TOUR.webm.
 * Tests only: phase6-judge-demo.spec.ts
 */
export default defineConfig({
  testDir: ".",
  testMatch: /phase6-judge-demo\.spec\.ts/,
  retries: 0,
  workers: 1,
  timeout: 600000, // 10 minutes — demo tour can be long with slowMo

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../playwright-report-judge" }],
  ],

  use: {
    baseURL: "http://localhost:4174",
    headless: false,
    slowMo: 4000,  // 4s between actions — cinematic quality for judge review
    trace: "on",
    video: {
      mode: "on",
      size: { width: 1280, height: 720 },
    },
    screenshot: "on",
    viewport: { width: 1280, height: 720 },
  },

  outputDir: "../test-results-judge",

  // webServer is disabled — start manually:
  //   apps/api: uvicorn main:app --port 8090
  //   apps/web: npm run preview (port 4174)
});
