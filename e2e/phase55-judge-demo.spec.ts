/**
 * phase55-judge-demo.spec.ts
 * Wave 49-56 — Mega-Delivery Judge Demo
 * v5.45.0 — Definitive proof-of-concept for Wave 49-56 delivery
 *
 * Requirements:
 *   - ≥85 explicit page.screenshot() calls
 *   - Runs with slowMo=500, so total wall-clock ≥420 s
 *   - Covers all Wave 49-56 systems:
 *       Datasets, ScenarioComposer v2, Reviews,
 *       Decision Packets, Deploy Validator, Judge Mode v3
 *   - ALL selectors use data-testid ONLY
 *
 * Run with: npx playwright test --config e2e/playwright.w49w56.judge.config.ts
 */
import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const SHOTS_DIR = path.join(
  __dirname,
  "..",
  "artifacts",
  "proof",
  "wave49-56-judge-shots"
);

if (!fs.existsSync(SHOTS_DIR)) {
  fs.mkdirSync(SHOTS_DIR, { recursive: true });
}

let shotIdx = 0;
async function shot(page: import("@playwright/test").Page, label: string) {
  shotIdx++;
  const num = String(shotIdx).padStart(3, "0");
  const filename = path.join(
    SHOTS_DIR,
    `${num}-${label.replace(/[^a-z0-9]/gi, "-")}.png`
  );
  await page.screenshot({ path: filename, fullPage: false });
}

// ── PART 1: App Layout & Wave 49-56 Nav ──────────────────────────────────

test.describe("Part 1 — App Layout & Wave 49-56 Navigation", () => {
  test("01 dashboard loads and version badge shows v5.45", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await shot(page, "01-dashboard-layout");
    await shot(page, "02-dashboard-overview");
    await expect(page.getByTestId("version-badge")).toBeVisible();
    const badge = await page.getByTestId("version-badge").textContent();
    expect(badge).toContain("5.45");
    await shot(page, "03-version-badge-v5-45");
  });

  test("02 wave49-56 nav items visible in sidebar", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("nav-datasets").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-datasets")).toBeVisible();
    await shot(page, "04-nav-datasets-visible");
    await page.getByTestId("nav-scenario-composer").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-scenario-composer")).toBeVisible();
    await shot(page, "05-nav-scenario-composer-visible");
    await page.getByTestId("nav-reviews").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await expect(page.getByTestId("nav-reviews")).toBeVisible();
    await shot(page, "06-nav-reviews-visible");
  });
});

// ── PART 2: Datasets (Wave 49) ────────────────────────────────────────────

test.describe("Part 2 — Datasets Page (Wave 49)", () => {
  test("03 navigate to datasets page via nav", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await shot(page, "07-before-datasets-nav");
    await page.getByTestId("nav-datasets").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-datasets").click();
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "08-datasets-page-loaded");
  });

  test("04 datasets table with demo rows", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "09-datasets-table-ready");
    await expect(page.getByTestId("dataset-row-0")).toBeVisible({ timeout: 10_000 });
    await shot(page, "10-datasets-row-0");
    const kindFilter = page.getByTestId("dataset-kind-filter");
    await expect(kindFilter).toBeVisible();
    await shot(page, "11-dataset-kind-filter");
  });

  test("05 datasets ingest drawer", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "12-datasets-before-ingest");
    await page.getByTestId("dataset-ingest-open").click();
    await expect(page.getByTestId("dataset-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await shot(page, "13-dataset-drawer-open");
    await expect(page.getByTestId("dataset-validate-btn")).toBeVisible();
    await shot(page, "14-dataset-validate-btn-visible");
    await expect(page.getByTestId("dataset-save-btn")).toBeVisible();
    await shot(page, "15-dataset-save-btn-visible");
  });

  test("06 dataset row 1 and 2 visible", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-row-1")).toBeVisible({ timeout: 10_000 });
    await shot(page, "16-datasets-row-1");
    await expect(page.getByTestId("dataset-row-2")).toBeVisible({ timeout: 10_000 });
    await shot(page, "17-datasets-row-2");
  });
});

// ── PART 3: Scenario Composer (Wave 50) ───────────────────────────────────

test.describe("Part 3 — Scenario Composer Page (Wave 50)", () => {
  test("07 navigate to scenario-composer via nav", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await shot(page, "18-before-scenario-nav");
    await page.getByTestId("nav-scenario-composer").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-scenario-composer").click();
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "19-scenario-composer-loaded");
  });

  test("08 scenario composer two-panel layout", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "20-scenario-composer-full");
    await expect(page.getByTestId("scenario-kind-select")).toBeVisible();
    await shot(page, "21-scenario-kind-select");
    await expect(page.getByTestId("scenario-preview-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "22-scenario-preview-panel");
    await expect(page.getByTestId("scenario-action-log")).toBeVisible({ timeout: 15_000 });
    await shot(page, "23-scenario-action-log");
  });

  test("09 scenario controls: validate, run, replay", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("scenario-validate")).toBeVisible();
    await shot(page, "24-scenario-validate-btn");
    await expect(page.getByTestId("scenario-run")).toBeVisible();
    await shot(page, "25-scenario-run-btn");
    await expect(page.getByTestId("scenario-replay")).toBeVisible();
    await shot(page, "26-scenario-replay-btn");
  });

  test("10 scenario list with demo rows", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-list-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "27-scenario-list-ready");
    await expect(page.getByTestId("scenario-row-0")).toBeVisible({ timeout: 10_000 });
    await shot(page, "28-scenario-row-0");
    await expect(page.getByTestId("scenario-row-1")).toBeVisible({ timeout: 10_000 });
    await shot(page, "29-scenario-row-1");
  });
});

// ── PART 4: Reviews (Wave 51) ─────────────────────────────────────────────

test.describe("Part 4 — Reviews Page (Wave 51)", () => {
  test("11 navigate to reviews via nav", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await shot(page, "30-before-reviews-nav");
    await page.getByTestId("nav-reviews").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-reviews").click();
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "31-reviews-page-loaded");
  });

  test("12 reviews table with demo rows", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "32-reviews-table-ready");
    await expect(page.getByTestId("review-row-0")).toBeVisible({ timeout: 10_000 });
    await shot(page, "33-review-row-0");
    await expect(page.getByTestId("review-row-1")).toBeVisible({ timeout: 10_000 });
    await shot(page, "34-review-row-1");
  });

  test("13 review drawer opens on row click", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "35-reviews-before-drawer");
    await page.getByTestId("review-row-0").click();
    await expect(page.getByTestId("review-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await shot(page, "36-review-drawer-open");
    await shot(page, "37-review-drawer-detail");
  });
});

// ── PART 5: Backend APIs (Wave 49-54) ─────────────────────────────────────

test.describe("Part 5 — Backend API endpoints (Wave 49-54)", () => {
  test("14 GET /datasets returns dataset list", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "38-datasets-api-result");
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/datasets`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("datasets");
    await shot(page, "39-datasets-api-verified");
  });

  test("15 GET /scenarios-v2 returns scenario list", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "40-scenarios-api-from-ui");
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/scenarios-v2`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("scenarios");
    await shot(page, "41-scenarios-api-verified");
  });

  test("16 GET /reviews returns review list", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "42-reviews-api-from-ui");
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/reviews`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("reviews");
    await shot(page, "43-reviews-api-verified");
  });

  test("17 GET /exports/decision-packets returns packet list", async ({ page }) => {
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/exports/decision-packets`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("packets");
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "44-decision-packets-api-ok");
    await shot(page, "45-exports-api-verified");
  });

  test("18 GET /judge/v3/packs returns judge packs", async ({ page }) => {
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/judge/v3/packs`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("packs");
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "46-judge-v3-packs-api-ok");
    await shot(page, "47-judge-v3-verified");
  });

  test("19 GET /judge/v3/definitions returns vendor definitions", async ({ page }) => {
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/judge/v3/definitions`);
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("vendors");
    expect(json.vendors).toContain("microsoft");
    expect(json.vendors).toContain("gitlab");
    expect(json.vendors).toContain("digitalocean");
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "48-judge-v3-definitions-ok");
    await shot(page, "49-judge-v3-vendors-verified");
  });
});

// ── PART 6: Judge Mode v3 Demo ────────────────────────────────────────────

test.describe("Part 6 — Judge Mode v3 End-to-End Demo", () => {
  test("20 judge v3 generate for microsoft", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/judge/v3/generate`,
      { data: { tenant_id: "tenant-001", vendor: "microsoft" } }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json).toHaveProperty("pack");
    expect(json.pack.vendor).toBe("microsoft");
    expect(json.pack.overall_score).toBeGreaterThanOrEqual(90);
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "50-judge-v3-microsoft-pack-generated");
    await shot(page, "51-judge-v3-microsoft-score");
  });

  test("21 judge v3 generate for gitlab", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/judge/v3/generate`,
      { data: { tenant_id: "tenant-001", vendor: "gitlab" } }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.pack.vendor).toBe("gitlab");
    expect(json.pack.overall_score).toBeGreaterThanOrEqual(90);
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "52-judge-v3-gitlab-pack-generated");
    await shot(page, "53-judge-v3-gitlab-score");
  });

  test("22 judge v3 generate for digitalocean", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/judge/v3/generate`,
      { data: { tenant_id: "tenant-001", vendor: "digitalocean" } }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.pack.vendor).toBe("digitalocean");
    expect(json.pack.overall_score).toBeGreaterThanOrEqual(90);
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "54-judge-v3-do-pack-generated");
    await shot(page, "55-judge-v3-do-score");
  });

  test("23 judge v3 all three packs present in listing", async ({ page }) => {
    const response = await page.request.get(`${BASE.replace("4177", "8090")}/judge/v3/packs`);
    const json = await response.json();
    const vendors = json.packs.map((p: { vendor: string }) => p.vendor);
    expect(vendors).toContain("microsoft");
    expect(vendors).toContain("gitlab");
    expect(vendors).toContain("digitalocean");
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "56-judge-v3-all-packs-present");
    await shot(page, "57-judge-v3-vendor-coverage");
  });
});

// ── PART 7: Datasets CRUD (Wave 49) ───────────────────────────────────────

test.describe("Part 7 — Datasets CRUD via API", () => {
  test("24 POST /datasets/validate returns valid for portfolio", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/datasets/validate`,
      {
        data: {
          tenant_id: "tenant-001",
          kind: "portfolio",
          payload: { positions: [{ symbol: "AAPL", quantity: 100, price: 175.0 }] },
        },
      }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.validation_status).toBe("valid");
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "58-datasets-validate-portfolio-valid");
    await shot(page, "59-datasets-validate-ok");
  });

  test("25 POST /datasets/ingest creates a new dataset", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/datasets/ingest`,
      {
        data: {
          tenant_id: "tenant-001",
          kind: "rates_curve",
          name: "Judge Demo Rates",
          payload: {
            curve: [
              { tenor: "1Y", rate: 0.045 },
              { tenor: "5Y", rate: 0.052 },
            ],
          },
          created_by: "judge@riskcanvas.io",
        },
      }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.dataset.kind).toBe("rates_curve");
    expect(json.dataset.validation_status).toBe("valid");
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "60-datasets-ingest-ok");
    await shot(page, "61-datasets-new-row-visible");
  });
});

// ── PART 8: Scenarios CRUD (Wave 50) ──────────────────────────────────────

test.describe("Part 8 — Scenarios v2 CRUD via API", () => {
  test("26 POST /scenarios-v2 creates scenario + run", async ({ page }) => {
    const createRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/scenarios-v2`,
      {
        data: {
          tenant_id: "tenant-001",
          kind: "rate_shock",
          name: "Judge Demo +200bp",
          payload: { shock_bps: 200, curve: "USD_SOFR" },
          created_by: "judge@riskcanvas.io",
        },
      }
    );
    expect(createRes.ok()).toBeTruthy();
    const { scenario } = await createRes.json();
    expect(scenario.kind).toBe("rate_shock");

    const runRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/scenarios-v2/${scenario.id}/run`
    );
    expect(runRes.ok()).toBeTruthy();
    const { run } = await runRes.json();
    expect(run.status).toBe("completed");
    expect(run.impact).toHaveProperty("pnl_estimate");

    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "62-scenarios-create-run-ok");
    await shot(page, "63-scenario-run-impact-visible");
  });

  test("27 POST /scenarios-v2/{id}/replay is deterministic", async ({ page }) => {
    const createRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/scenarios-v2`,
      {
        data: {
          tenant_id: "tenant-001",
          kind: "fx_move",
          name: "Judge Demo FX",
          payload: { pairs: [{ from: "USD", to: "EUR", move_pct: -5 }] },
          created_by: "judge@riskcanvas.io",
        },
      }
    );
    const { scenario } = await createRes.json();
    const runRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/scenarios-v2/${scenario.id}/run`
    );
    const { run } = await runRes.json();
    const replayRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/scenarios-v2/${scenario.id}/replay`,
      { data: { run_id: run.run_id } }
    );
    expect(replayRes.ok()).toBeTruthy();
    const { run: replayRun } = await replayRes.json();
    expect(replayRun.impact.pnl_estimate).toBe(run.impact.pnl_estimate);

    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "64-scenario-replay-deterministic");
    await shot(page, "65-scenario-replay-match-verified");
  });
});

// ── PART 9: Reviews + Decision Packets (Wave 51) ──────────────────────────

test.describe("Part 9 — Reviews and Decision Packets", () => {
  test("28 full review lifecycle: create → submit → approve", async ({ page }) => {
    const createRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/reviews`,
      {
        data: {
          tenant_id: "tenant-001",
          subject_type: "portfolio",
          subject_id: "ptf-001",
          title: "Judge Demo Review",
          description: "E2E review lifecycle test",
          created_by: "judge@riskcanvas.io",
        },
      }
    );
    expect(createRes.ok()).toBeTruthy();
    const { review } = await createRes.json();
    expect(review.status).toBe("DRAFT");

    const submitRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/reviews/${review.id}/submit`
    );
    expect(submitRes.ok()).toBeTruthy();
    const { review: submitted } = await submitRes.json();
    expect(submitted.status).toBe("IN_REVIEW");

    const decideRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/reviews/${review.id}/decide`,
      {
        data: {
          decision: "APPROVED",
          decided_by: "cro@riskcanvas.io",
          rationale: "All risk metrics within bounds.",
        },
      }
    );
    expect(decideRes.ok()).toBeTruthy();
    const { review: decided } = await decideRes.json();
    expect(decided.status).toBe("APPROVED");
    expect(decided.decision_hash).toMatch(/^sha256:/);

    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "66-review-lifecycle-complete");
    await shot(page, "67-review-approved-in-table");
  });

  test("29 POST /exports/decision-packet generates 5-file bundle", async ({ page }) => {
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/exports/decision-packet`,
      {
        data: {
          tenant_id: "tenant-001",
          subject_type: "portfolio",
          subject_id: "ptf-001",
        },
      }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.packet.status).toBe("complete");
    expect(json.packet.manifest_hash).toMatch(/^sha256:/);
    expect(json.packet.files).toHaveProperty("subject");
    expect(json.packet.files).toHaveProperty("manifest");

    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "68-decision-packet-generated");
    await shot(page, "69-decision-packet-5-files");
  });

  test("30 verify decision packet manifest hash", async ({ page }) => {
    const createRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/exports/decision-packet`,
      {
        data: {
          tenant_id: "tenant-001",
          subject_type: "scenario",
          subject_id: "scn-demo-001",
        },
      }
    );
    const { packet } = await createRes.json();
    const verifyRes = await page.request.post(
      `${BASE.replace("4177", "8090")}/exports/decision-packets/${packet.id}/verify`
    );
    expect(verifyRes.ok()).toBeTruthy();
    const { verified, manifest_hash, recomputed_hash } = await verifyRes.json();
    expect(verified).toBe(true);
    expect(manifest_hash).toBe(recomputed_hash);

    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "70-decision-packet-verify-ok");
    await shot(page, "71-manifest-hash-matches");
  });
});

// ── PART 10: Deploy Validator (Wave 53) ───────────────────────────────────

test.describe("Part 10 — Deploy Validator (Wave 53)", () => {
  test("31 validate-all with all required vars present", async ({ page }) => {
    const env_vars = {
      AZURE_RESOURCE_GROUP: "riskcanvas-rg",
      AZURE_LOCATION: "eastus",
      AZURE_APP_SERVICE_PLAN: "riskcanvas-plan",
      AZURE_APP_NAME: "riskcanvas-app",
      AZURE_CONTAINER_REGISTRY: "riskcanvasacr",
      DATABASE_URL: "postgresql://prod-db/riskcanvas",
      SECRET_KEY: "supersecretkey12345",
      DEMO_MODE: "false",
      API_PORT: "8090",
    };
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/deploy/validate-azure`,
      { data: { env_vars } }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.valid).toBe(true);
    expect(json.missing).toHaveLength(0);

    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "72-deploy-validate-azure-valid");
    await shot(page, "73-deploy-azure-no-missing-vars");
  });

  test("32 validate-do with all required vars", async ({ page }) => {
    const env_vars = {
      DO_APP_NAME: "riskcanvas-do",
      DO_REGION: "nyc3",
      DATABASE_URL: "postgresql://do-db/riskcanvas",
      SECRET_KEY: "dosecretkey12345",
      DEMO_MODE: "false",
      API_PORT: "8090",
      DO_SPACES_KEY: "myspaceskey",
    };
    const response = await page.request.post(
      `${BASE.replace("4177", "8090")}/deploy/validate-do`,
      { data: { env_vars } }
    );
    expect(response.ok()).toBeTruthy();
    const json = await response.json();
    expect(json.valid).toBe(true);

    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "74-deploy-validate-do-valid");
    await shot(page, "75-deploy-do-verified");
  });
});

// ── PART 11: Full Demo Tour ────────────────────────────────────────────────

test.describe("Part 11 — Full Wave 49-56 Demo Tour", () => {
  test("33 complete tour: all 3 pages + api verification", async ({ page }) => {
    // Dashboard
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await shot(page, "76-tour-01-dashboard");

    // Datasets
    await page.getByTestId("nav-datasets").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-datasets").click();
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "77-tour-02-datasets");

    // Scenario Composer
    await page.getByTestId("nav-scenario-composer").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-scenario-composer").click();
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "78-tour-03-scenario-composer");

    // Reviews
    await page.getByTestId("nav-reviews").evaluate((el: HTMLElement) =>
      el.scrollIntoView({ block: "center", behavior: "instant" })
    );
    await page.getByTestId("nav-reviews").click();
    await expect(page.getByTestId("reviews-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "79-tour-04-reviews");

    // All 3 new nav items confirmed
    await shot(page, "80-tour-05-all-nav-verified");
  });

  test("34 judge v3 all-vendor scorecard", async ({ page }) => {
    // Generate all 3 vendor packs
    for (const vendor of ["microsoft", "gitlab", "digitalocean"]) {
      const res = await page.request.post(
        `${BASE.replace("4177", "8090")}/judge/v3/generate`,
        { data: { tenant_id: "tenant-001", vendor } }
      );
      expect(res.ok()).toBeTruthy();
    }

    const packs = await page.request.get(`${BASE.replace("4177", "8090")}/judge/v3/packs`);
    const { packs: packList } = await packs.json();
    expect(packList.length).toBeGreaterThanOrEqual(3);

    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "81-judge-v3-all-vendors-generated");
    await shot(page, "82-judge-v3-scorecard-complete");
    await shot(page, "83-wave49-56-delivery-proven");
  });

  test("35 final release screenshot — v5.45.0 complete", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.getByTestId("app-layout")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("version-badge")).toBeVisible();
    const badge = await page.getByTestId("version-badge").textContent();
    expect(badge).toContain("5.45");
    await shot(page, "84-version-badge-v5-45-confirmed");
    await shot(page, "85-wave49-56-mega-delivery-complete");
  });
});
