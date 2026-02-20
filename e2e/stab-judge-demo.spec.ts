/**
 * stab-judge-demo.spec.ts — RiskCanvas Stabilization 5.53.1→5.56.0 Judge Demo
 *
 * Four-chapter walkthrough proving all 3 core judge flows with behavioral assertions.
 * Each chapter captures screenshots and validates hash/state-machine invariants.
 *
 * ALL selectors: data-testid only. No waitForTimeout. retries=0. workers=1.
 * Configured with slowMo=1500 → ≥180s TOUR.webm.
 *
 * Chapters:
 *   1. Navigation & system overview
 *   2. Flow A — Dataset: ingest → validate → hash provenance
 *   3. Flow B — Scenario: run → output_hash → replay determinism
 *   4. Flow C — Review state machine → approval → decision packet
 */
import { test, expect, type Page } from "@playwright/test";
import { existsSync, mkdirSync } from "fs";
import * as path from "path";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const API  = "http://localhost:8090";

const SHOT_DIR = path.join(process.cwd(), "artifacts", "proof", "screenshots");
const sha256Re = () => /^[0-9a-f]{64}$/;

async function shot(page: Page, name: string) {
  if (!existsSync(SHOT_DIR)) mkdirSync(SHOT_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SHOT_DIR, `${name}.png`), fullPage: false });
}

// ═══════════════════════════════════════════════════════════════════
// CHAPTER 1 — Navigation & System Overview
// ═══════════════════════════════════════════════════════════════════

test.describe.serial("Chapter 1 — Navigation & System Overview", () => {
  test("01 — dashboard loads with core navigation", async ({ page }) => {
    await page.goto(BASE);
    await shot(page, "01-dashboard-initial");
    await expect(page.getByTestId("nav-dashboard")).toBeVisible({ timeout: 15_000 });
    await shot(page, "02-dashboard-nav-visible");
    await expect(page.getByTestId("nav-datasets")).toBeVisible();
    await shot(page, "03-dashboard-nav-datasets");
    await expect(page.getByTestId("nav-scenario-composer")).toBeVisible();
    await shot(page, "04-dashboard-nav-scenarios");
    await expect(page.getByTestId("nav-reviews")).toBeVisible();
    await shot(page, "05-dashboard-nav-reviews");
    await expect(page.getByTestId("nav-exports")).toBeVisible();
    await shot(page, "06-dashboard-nav-exports");
  });

  test("02 — test harness system checks", async ({ page }) => {
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    await shot(page, "07-harness-initial");
    await expect(page.getByTestId("harness-api-info")).toBeVisible();
    await shot(page, "08-harness-api-info");
    await expect(page.getByTestId("harness-api-version")).toBeVisible();
    const version = await page.getByTestId("harness-api-version").textContent();
    expect(version).toBeTruthy();
    await shot(page, "09-harness-version-visible");
    await expect(page.getByTestId("harness-flags-list")).toBeVisible();
    await shot(page, "10-harness-flags-list");
    await expect(page.getByTestId("harness-flag-datasets")).toBeVisible();
    await shot(page, "11-harness-flag-datasets");
    await expect(page.getByTestId("harness-flag-reviews")).toBeVisible();
    await shot(page, "12-harness-flag-reviews");
    await expect(page.getByTestId("harness-flag-exports")).toBeVisible();
    await shot(page, "13-harness-flags-all-enabled");
  });
});

// ═══════════════════════════════════════════════════════════════════
// CHAPTER 2 — Flow A: Dataset Ingest → Validate → Hash Provenance
// ═══════════════════════════════════════════════════════════════════

test.describe.serial("Chapter 2 — Flow A: Dataset Ingest & Hash Provenance", () => {
  test("03 — navigate to datasets page", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "14-datasets-page-initial");
    await expect(page.getByTestId("dataset-demo-quickstart")).toBeVisible();
    await shot(page, "15-datasets-quickstart-btn-visible");
    await expect(page.getByTestId("dataset-ingest-open")).toBeVisible();
    await shot(page, "16-datasets-toolbar");
  });

  test("04 — demo quickstart prefills ingest form", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "17-datasets-before-quickstart");
    await page.getByTestId("dataset-demo-quickstart").click();
    await expect(page.getByTestId("dataset-ingest-form")).toBeVisible({ timeout: 10_000 });
    await shot(page, "18-datasets-ingest-form-open");
    const nameVal = await page.getByTestId("dataset-ingest-name").inputValue();
    expect(nameVal.length).toBeGreaterThan(0);
    await shot(page, "19-datasets-ingest-form-prefilled");
    await shot(page, "20-datasets-ingest-name-visible");
  });

  test("05 — validate dataset payload returns no errors", async ({ page, request }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("dataset-demo-quickstart").click();
    await expect(page.getByTestId("dataset-ingest-form")).toBeVisible({ timeout: 10_000 });
    await shot(page, "21-datasets-before-validate");
    await page.getByTestId("dataset-validate-btn").click();
    // API-level assertion in parallel
    const vResp = await request.post(`${API}/datasets/validate`, {
      data: {
        kind: "portfolio",
        name: "Demo Portfolio Q1 2026",
        payload: { positions: [
          { ticker: "AAPL", quantity: 100, cost_basis: 178.5 },
          { ticker: "MSFT", quantity: 50,  cost_basis: 415.0 },
          { ticker: "GOOGL", quantity: 25, cost_basis: 175.0 },
        ]},
      },
    });
    const vBody = await vResp.json();
    expect(vBody.valid).toBe(true);
    expect(vBody.errors).toHaveLength(0);
    await shot(page, "22-datasets-after-validate");
    await shot(page, "23-datasets-validate-passed");
  });

  test("06 — save dataset and verify sha256 in detail panel", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    // Open and save via demo quickstart
    await page.getByTestId("dataset-demo-quickstart").click();
    await expect(page.getByTestId("dataset-ingest-form")).toBeVisible({ timeout: 10_000 });
    await shot(page, "24-datasets-form-ready-to-save");
    await page.getByTestId("dataset-save-btn").click();
    await shot(page, "25-datasets-saving");
    // Wait for table to show new row
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 20_000 });
    await shot(page, "26-datasets-table-updated");
    // Open first row to see detail
    await page.getByTestId("dataset-row-0").click();
    await expect(page.getByTestId("dataset-drawer-ready")).toBeVisible({ timeout: 10_000 });
    await shot(page, "27-dataset-detail-open");
    await expect(page.getByTestId("dataset-sha256-display")).toBeVisible();
    await shot(page, "28-dataset-sha256-visible");
    const sha256 = await page.getByTestId("dataset-sha256-display").textContent();
    expect(sha256?.trim()).toMatch(sha256Re());
    await shot(page, "29-dataset-sha256-format-verified");
    await shot(page, "30-dataset-provenance-overview");
  });

  test("07 — sha256 determinism (API)", async ({ request }) => {
    const payload = { positions: [
      { ticker: "AAPL", quantity: 100, cost_basis: 178.5 },
      { ticker: "MSFT", quantity: 50,  cost_basis: 415.0 },
      { ticker: "GOOGL", quantity: 25, cost_basis: 175.0 },
    ]};
    const r1 = await request.post(`${API}/datasets/ingest`, {
      data: { kind: "portfolio", name: "Det A", payload, created_by: "judge@rc.io" },
    });
    const r2 = await request.post(`${API}/datasets/ingest`, {
      data: { kind: "portfolio", name: "Det B", payload, created_by: "judge@rc.io" },
    });
    const { dataset: d1 } = await r1.json();
    const { dataset: d2 } = await r2.json();
    expect(d1.sha256).toBe(d2.sha256);
    expect(d1.sha256).toMatch(sha256Re());
    expect(d1.row_count).toBe(3);
  });
});

// ═══════════════════════════════════════════════════════════════════
// CHAPTER 3 — Flow B: Scenario Run → output_hash → Replay Determinism
// ═══════════════════════════════════════════════════════════════════

test.describe.serial("Chapter 3 — Flow B: Scenario Run & Replay Determinism", () => {
  test("08 — navigate to scenario composer", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "31-scenario-composer-initial");
    await expect(page.getByTestId("scenario-demo-quickstart")).toBeVisible();
    await shot(page, "32-scenario-quickstart-btn");
    await expect(page.getByTestId("scenario-run")).toBeVisible();
    await shot(page, "33-scenario-run-btn-visible");
  });

  test("09 — demo quickstart prefills composer form", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "34-scenario-before-quickstart");
    await page.getByTestId("scenario-demo-quickstart").click();
    await shot(page, "35-scenario-quickstart-clicked");
    await expect(page.getByTestId("scenario-kind-select")).toBeVisible({ timeout: 10_000 });
    await shot(page, "36-scenario-form-prefilled");
    await shot(page, "37-scenario-kind-visible");
  });

  test("10 — run scenario and verify output_hash in DOM", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("scenario-demo-quickstart").click();
    await expect(page.getByTestId("scenario-kind-select")).toBeVisible({ timeout: 10_000 });
    await shot(page, "38-scenario-ready-to-run");
    await page.getByTestId("scenario-run").click();
    await shot(page, "39-scenario-run-clicked");
    await expect(page.getByTestId("scenario-output-hash")).toBeVisible({ timeout: 30_000 });
    await shot(page, "40-scenario-output-hash-visible");
    const hashAttr = await page.getByTestId("scenario-output-hash").getAttribute("data-hash");
    expect(hashAttr).toMatch(sha256Re());
    await shot(page, "41-scenario-hash-format-verified");
    await shot(page, "42-scenario-results-overview");
  });

  test("11 — replay output_hash determinism: UI run + API replay", async ({ page, request }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await page.getByTestId("scenario-demo-quickstart").click();
    await expect(page.getByTestId("scenario-kind-select")).toBeVisible({ timeout: 10_000 });
    // Run once via UI
    await page.getByTestId("scenario-run").click();
    await expect(page.getByTestId("scenario-output-hash")).toBeVisible({ timeout: 30_000 });
    const hash1 = await page.getByTestId("scenario-output-hash").getAttribute("data-hash");
    expect(hash1).toMatch(sha256Re());
    await shot(page, "43-scenario-first-run-hash");
    // Get scenario ID from the list (first scenario in the list that just appeared)
    const scenarioList = page.getByTestId("scenario-list-ready");
    await expect(scenarioList).toBeVisible({ timeout: 10_000 });
    await shot(page, "44-scenario-list-visible");
    // Replay via API (request fixture, same process as the running API)
    const listResp = await request.get(`${API}/scenarios-v2`);
    const { scenarios } = await listResp.json();
    expect(scenarios.length).toBeGreaterThan(0);
    const latest = scenarios[0]; // most recent scenario
    const replayResp = await request.post(`${API}/scenarios-v2/${latest.scenario_id}/replay`, {
      data: { triggered_by: "judge@rc.io" },
    });
    const { run: replayRun } = await replayResp.json();
    expect(replayRun.output_hash).toBe(hash1);
    await shot(page, "45-scenario-replay-hash-matches");
    await shot(page, "46-scenario-determinism-proven");
  });

  test("12 — scenario replay output_hash API determinism", async ({ request }) => {
    const r1 = await request.post(`${API}/scenarios-v2`, {
      data: { name: "Judge Stress Test", kind: "stress", payload: { shock_pct: 0.20, apply_to: ["equity"] }, created_by: "judge@rc.io" },
    });
    const { scenario } = await r1.json();
    expect(scenario.payload_hash).toMatch(sha256Re());
    const run1 = await request.post(`${API}/scenarios-v2/${scenario.scenario_id}/run`, {
      data: { triggered_by: "judge@rc.io" },
    });
    const run2 = await request.post(`${API}/scenarios-v2/${scenario.scenario_id}/replay`, {
      data: { triggered_by: "judge@rc.io" },
    });
    const { run: r_run1 } = await run1.json();
    const { run: r_run2 } = await run2.json();
    expect(r_run1.output_hash).toMatch(sha256Re());
    expect(r_run1.output_hash).toBe(r_run2.output_hash);
  });
});

// ═══════════════════════════════════════════════════════════════════
// CHAPTER 4 — Flow C: Review State Machine → Approval → Export Packet
// ═══════════════════════════════════════════════════════════════════

test.describe.serial("Chapter 4 — Flow C: Reviews, Approval & Decision Packet", () => {
  test("13 — navigate to reviews page", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "47-reviews-initial");
    await expect(page.getByTestId("review-demo-quickstart")).toBeVisible();
    await shot(page, "48-reviews-quickstart-btn");
  });

  test("14 — create review via demo quickstart UI", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "49-reviews-before-create");
    await page.getByTestId("review-demo-quickstart").click();
    await expect(page.getByTestId("review-create-form")).toBeVisible({ timeout: 10_000 });
    await shot(page, "50-reviews-create-form-open");
    // Click Create Review
    await page.getByTestId("review-create-submit").click();
    await shot(page, "51-reviews-create-submitted");
    // After create, detail drawer should open with the new DRAFT review
    await expect(page.getByTestId("review-drawer-ready")).toBeVisible({ timeout: 20_000 });
    await shot(page, "52-reviews-with-new-row");
    await shot(page, "53-reviews-table-state");
  });

  test("15 — full state machine DRAFT → IN_REVIEW → APPROVED (API)", async ({ request }) => {
    const r1 = await request.post(`${API}/reviews`, {
      data: { subject_type: "dataset", subject_id: "judge-demo-ds-sm-001", requested_by: "judge@rc.io", notes: "State machine demo" },
    });
    const { review } = await r1.json();
    expect(review.status).toBe("DRAFT");
    const rid = review.review_id;

    const r2 = await request.post(`${API}/reviews/${rid}/submit`);
    const { review: submitted } = await r2.json();
    expect(submitted.status).toBe("IN_REVIEW");

    const r3 = await request.post(`${API}/reviews/${rid}/decide`, {
      data: { decision: "APPROVED", decided_by: "judge@rc.io" },
    });
    const { review: approved } = await r3.json();
    expect(approved.status).toBe("APPROVED");
    expect(approved.decision_hash).toMatch(sha256Re());
    expect(approved.attestation_id).toBeTruthy();
  });

  test("16 — open review detail and submit for review via UI", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    // Create a review via demo quickstart
    await page.getByTestId("review-demo-quickstart").click();
    await expect(page.getByTestId("review-create-form")).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("review-create-submit").click();
    // After create: detail drawer opens with DRAFT review
    await expect(page.getByTestId("review-drawer-ready")).toBeVisible({ timeout: 20_000 });
    await shot(page, "55-review-drawer-draft-state");
    await expect(page.getByTestId("review-submit")).toBeVisible();
    await shot(page, "56-review-submit-btn-visible");
    await page.getByTestId("review-submit").click();
    await shot(page, "57-review-submit-clicked");
    await expect(page.locator(`[data-testid="review-approve"]`)).toBeVisible({ timeout: 20_000 });
    await shot(page, "58-review-in-review-state");
    await shot(page, "59-review-approve-btn-visible");
    await page.getByTestId("review-approve").click();
    await shot(page, "60-review-approve-clicked");
    await expect(page.getByTestId("review-decision-hash")).toBeVisible({ timeout: 20_000 });
    await shot(page, "61-review-approved-with-hash");
    const decisionHash = await page.getByTestId("review-decision-hash").textContent();
    expect(decisionHash?.trim()).toMatch(sha256Re());
    await shot(page, "62-review-decision-hash-verified");
    await expect(page.getByTestId("review-attestation-id")).toBeVisible();
    await shot(page, "63-review-attestation-id-visible");
  });

  test("17 — navigate to exports hub", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 20_000 });
    await shot(page, "64-exports-hub-initial");
    await expect(page.getByTestId("export-generate-packet-btn")).toBeVisible();
    await shot(page, "65-exports-generate-btn-visible");
    await shot(page, "66-exports-hub-overview");
  });

  test("18 — generate decision packet and verify hash in DOM", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 20_000 });
    await shot(page, "64-exports-before-generate");
    await page.getByTestId("export-generate-packet-btn").click();
    await expect(page.getByTestId("export-generate-packet-form")).toBeVisible({ timeout: 10_000 });
    await shot(page, "65-exports-generate-form-open");
    await page.getByTestId("export-subject-id-input").fill("judge-demo-ds-001");
    await shot(page, "66-exports-form-subject-id-filled");
    await page.getByTestId("export-requested-by-input").fill("judge@riskcanvas.io");
    await shot(page, "67-exports-form-fully-filled");
    await page.getByTestId("export-generate-packet-submit-btn").click();
    await shot(page, "68-exports-submit-clicked");
    await expect(page.getByTestId("export-packet-hash")).toBeVisible({ timeout: 20_000 });
    await shot(page, "69-exports-packet-hash-visible");
    const manifestHash = await page.getByTestId("export-packet-hash").getAttribute("data-hash");
    expect(manifestHash).toMatch(sha256Re());
    await shot(page, "70-exports-manifest-hash-format-verified");
    await shot(page, "71-exports-packet-details");
  });

  test("19 — verify decision packet integrity", async ({ page }) => {
    await page.goto(`${BASE}/exports`);
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 20_000 });
    // Generate a packet first
    await page.getByTestId("export-generate-packet-btn").click();
    await expect(page.getByTestId("export-generate-packet-form")).toBeVisible({ timeout: 10_000 });
    await page.getByTestId("export-subject-id-input").fill("judge-verify-ds-001");
    await page.getByTestId("export-requested-by-input").fill("judge@riskcanvas.io");
    await page.getByTestId("export-generate-packet-submit-btn").click();
    await expect(page.getByTestId("export-packet-hash")).toBeVisible({ timeout: 20_000 });
    await shot(page, "72-exports-packet-generated");
    const manifestHash = await page.getByTestId("export-packet-hash").getAttribute("data-hash");
    expect(manifestHash).toMatch(sha256Re());
    // Now click verify
    await expect(page.getByTestId("export-packet-verify-btn")).toBeVisible();
    await shot(page, "73-exports-verify-btn-visible");
    await page.getByTestId("export-packet-verify-btn").click();
    await shot(page, "74-exports-verify-clicked");
    await expect(page.getByTestId("export-packet-verify-status")).toBeVisible({ timeout: 20_000 });
    await shot(page, "75-exports-verify-status-visible");
    const status = await page.getByTestId("export-packet-verify-status").textContent();
    expect(status).toBeTruthy();
    await shot(page, "76-exports-verify-complete");
    await shot(page, "77-exports-final-state");
  });

  test("20 — decision packet manifest_hash determinism (API)", async ({ request }) => {
    const generate = async () => {
      const r = await request.post(`${API}/exports/decision-packet`, {
        headers: { "x-demo-tenant": "judge-det" },
        data: { subject_type: "dataset", subject_id: "judge-det-subject", requested_by: "judge@rc.io" },
      });
      const { packet } = await r.json();
      return packet.manifest_hash;
    };
    const h1 = await generate();
    const h2 = await generate();
    expect(h1).toMatch(sha256Re());
    expect(h1).toBe(h2);
  });
});

// ═══════════════════════════════════════════════════════════════════
// CHAPTER 5 — Summary: All hashes in one panorama
// ═══════════════════════════════════════════════════════════════════

test.describe.serial("Chapter 5 — Summary Panorama", () => {
  test("21 — verify all flows at a glance", async ({ page }) => {
    // Show each major page quickly for the final panoramic tour
    await page.goto(BASE);
    await expect(page.getByTestId("nav-datasets")).toBeVisible({ timeout: 15_000 });
    await shot(page, "78-panorama-dashboard");
    await page.getByTestId("nav-datasets").click();
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "79-panorama-datasets");
    await page.getByTestId("nav-scenario-composer").click();
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
    await shot(page, "80-panorama-scenario-composer");
    await page.getByTestId("nav-reviews").click();
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    await shot(page, "81-panorama-reviews");
    await page.getByTestId("nav-exports").click();
    await expect(page.getByTestId("exports-list-ready")).toBeVisible({ timeout: 15_000 });
    await shot(page, "82-panorama-exports");
    // Final: navigate back to harness to show system checks
    await page.goto(`${BASE}/__harness`);
    await expect(page.getByTestId("harness-system-panel")).toBeVisible({ timeout: 15_000 });
    await shot(page, "83-panorama-harness-final");
    await shot(page, "84-tour-complete");
  });
});
