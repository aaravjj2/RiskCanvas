import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./",
  testMatch: [
    "test-w33-ui-foundation.spec.ts",
    "test-w34-exports.spec.ts",
    "test-w35-presentation.spec.ts",
    "test-w37-workbench.spec.ts",
    "test-w38-microux.spec.ts",
  ],
  retries: 0,
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:4177",
    headless: true,
    trace: "on",
    screenshot: "on",
    viewport: { width: 1440, height: 900 },
  },
  outputDir: "../test-results/w33w40-unit",
  reporter: [
    ["list"],
    ["html", { outputFolder: "../playwright-report/w33w40-unit", open: "never" }],
  ],
  projects: [
    {
      name: "chromium-w33w40-unit",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
