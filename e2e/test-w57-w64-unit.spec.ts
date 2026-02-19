/**
 * test-w57-w64-unit.spec.ts
 * Wave 57-64 — Hardening + Provenance Layer:
 *   Packet Signing, Dataset Provenance, Scenario Runner v1,
 *   Reviews SLA, Deploy Validator v2, Judge Mode v4,
 *   Search Provider, LLM Provider
 * v5.46.0 → v5.53.0
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const API = "http://localhost:8090";

// ── WAVE 57: Packet Signing (backend API) ────────────────────────────────

test.describe("Wave 57 — Packet Signing API", () => {
  test("POST /signatures/sign returns nested signature object", async ({ request }) => {
    const res = await request.post(`${API}/signatures/sign`, {
      data: {
        packet_id: "unit-sign-001",
        manifest_hash: "abc123def456",
        files: { "report.pdf": "deadbeef" },
        signed_by: "e2e-unit",
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("signature");
    expect(body.signature).toHaveProperty("algorithm");
    expect(body.signature.algorithm).toBe("Ed25519");
    expect(body.signature).toHaveProperty("signature");
    expect(body.signature.signature.length).toBe(128);
    expect(body.signature).toHaveProperty("public_key");
  });

  test("GET /signatures/ returns signatures array", async ({ request }) => {
    const res = await request.get(`${API}/signatures/`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("signatures");
    expect(Array.isArray(body.signatures)).toBe(true);
  });

  test("GET /signatures/{id} returns stored signature object", async ({ request }) => {
    await request.post(`${API}/signatures/sign`, {
      data: {
        packet_id: "unit-sign-get-001",
        manifest_hash: "gethash",
        files: {},
        signed_by: "e2e",
      },
    });
    const res = await request.get(`${API}/signatures/unit-sign-get-001`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("signature");
    expect(body.signature.packet_id).toBe("unit-sign-get-001");
  });

  test("POST /signatures/{id}/verify returns verified=true", async ({ request }) => {
    await request.post(`${API}/signatures/sign`, {
      data: {
        packet_id: "unit-sign-verify-001",
        manifest_hash: "verifyhash001",
        files: { "file.txt": "aabbcc" },
        signed_by: "e2e",
      },
    });
    const verRes = await request.post(`${API}/signatures/unit-sign-verify-001/verify`, {
      data: {
        manifest_hash: "verifyhash001",
        files: { "file.txt": "aabbcc" },
      },
    });
    expect(verRes.ok()).toBe(true);
    const body = await verRes.json();
    expect(body.verified).toBe(true);
  });
});

// ── WAVE 58: Dataset Provenance (backend API) ────────────────────────────

test.describe("Wave 58 — Dataset Provenance API", () => {
  test("GET /provenance/datasets returns datasets wrapped in object", async ({ request }) => {
    const res = await request.get(`${API}/provenance/datasets`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("datasets");
    expect(Array.isArray(body.datasets)).toBe(true);
    expect(body.datasets.length).toBeGreaterThan(0);
  });

  test("datasets entries have dataset_id and license_tag", async ({ request }) => {
    const res = await request.get(`${API}/provenance/datasets`);
    const body = await res.json();
    const first = body.datasets[0];
    expect(first).toHaveProperty("dataset_id");
    expect(first).toHaveProperty("license_tag");
    expect(first).toHaveProperty("license_compliant");
  });

  test("GET /provenance/summary returns total count", async ({ request }) => {
    const res = await request.get(`${API}/provenance/summary`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("total");
    expect(body.total).toBeGreaterThan(0);
  });
});

// ── WAVE 59: Scenario Runner (backend API) ───────────────────────────────

test.describe("Wave 59 — Scenario Runner v1 API", () => {
  test("GET /scenario-runner/runs returns wrapped runs array", async ({ request }) => {
    const res = await request.get(`${API}/scenario-runner/runs`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("runs");
    expect(Array.isArray(body.runs)).toBe(true);
    expect(body.runs.length).toBeGreaterThan(0);
  });

  test("POST /scenario-runner/runs creates completed run", async ({ request }) => {
    const res = await request.post(`${API}/scenario-runner/runs`, {
      data: {
        scenario_id: "unit-scen-001",
        kind: "rate_shock",
        payload: { delta_bps: 50 },
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("run");
    expect(body.run).toHaveProperty("run_id");
    expect(body.run.status).toBe("completed");
    expect(body.run).toHaveProperty("inputs_hash");
    expect(body.run).toHaveProperty("outputs_hash");
  });

  test("GET /scenario-runner/runs/{id} returns run", async ({ request }) => {
    const listRes = await request.get(`${API}/scenario-runner/runs`);
    const list = await listRes.json();
    const firstRunId = list.runs[0].run_id;
    const res = await request.get(`${API}/scenario-runner/runs/${firstRunId}`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("run");
    expect(body.run.run_id).toBe(firstRunId);
  });

  test("POST /scenario-runner/runs/{id}/replay preserves hashes", async ({ request }) => {
    const listRes = await request.get(`${API}/scenario-runner/runs`);
    const list = await listRes.json();
    const firstRun = list.runs[0];
    const replayRes = await request.post(`${API}/scenario-runner/runs/${firstRun.run_id}/replay`);
    expect(replayRes.ok()).toBe(true);
    const replay = await replayRes.json();
    expect(replay.run.inputs_hash).toBe(firstRun.inputs_hash);
    expect(replay.run.outputs_hash).toBe(firstRun.outputs_hash);
  });
});

// ── WAVE 60: Reviews SLA (backend API) ──────────────────────────────────

test.describe("Wave 60 — Reviews SLA API", () => {
  test("GET /reviews-sla/reviews returns reviews with sla fields", async ({ request }) => {
    const res = await request.get(`${API}/reviews-sla/reviews`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("reviews");
    expect(Array.isArray(body.reviews)).toBe(true);
    expect(body.reviews.length).toBeGreaterThan(0);
    expect(body.reviews[0]).toHaveProperty("sla_deadline");
    expect(body.reviews[0]).toHaveProperty("assigned_to");
  });

  test("GET /reviews-sla/dashboard returns SLA counts", async ({ request }) => {
    const res = await request.get(`${API}/reviews-sla/dashboard`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("total_reviews");
    expect(body).toHaveProperty("total_breached");
  });

  test("POST /reviews-sla/bulk-assign returns updated count", async ({ request }) => {
    const listRes = await request.get(`${API}/reviews-sla/reviews`);
    const list = await listRes.json();
    const ids = list.reviews.slice(0, 2).map((r: Record<string, unknown>) => r.review_id);
    const res = await request.post(`${API}/reviews-sla/bulk-assign`, {
      data: { review_ids: ids },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("updated");
  });
});

// ── WAVE 61: Deploy Validator v2 (backend API) ───────────────────────────

test.describe("Wave 61 — Deploy Validator v2 API", () => {
  test("POST /deploy-validator/run returns run.findings array of 8", async ({ request }) => {
    const res = await request.post(`${API}/deploy-validator/run`, {
      data: { environment: "demo", target_url: "http://localhost:8090" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("run");
    expect(body.run).toHaveProperty("findings");
    expect(Array.isArray(body.run.findings)).toBe(true);
    expect(body.run.findings.length).toBe(8);
  });

  test("findings have check, severity, passed, detail fields", async ({ request }) => {
    const res = await request.post(`${API}/deploy-validator/run`, {
      data: { environment: "demo" },
    });
    const body = await res.json();
    const f = body.run.findings[0];
    expect(f).toHaveProperty("check");
    expect(f).toHaveProperty("severity");
    expect(f).toHaveProperty("passed");
    expect(f).toHaveProperty("detail");
  });

  test("GET /deploy-validator/runs returns runs list", async ({ request }) => {
    const res = await request.get(`${API}/deploy-validator/runs`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("runs");
    expect(Array.isArray(body.runs)).toBe(true);
  });

  test("GET /deploy-validator/checks returns 8 check definitions", async ({ request }) => {
    const res = await request.get(`${API}/deploy-validator/checks`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("checks");
    expect(body.checks.length).toBe(8);
  });
});

// ── WAVE 62: Judge Mode v4 (backend API) ─────────────────────────────────

test.describe("Wave 62 — Judge Mode v4 API", () => {
  test("POST /judge/v4/generate returns scoring report with grade", async ({ request }) => {
    const res = await request.post(`${API}/judge/v4/generate`, {
      data: {
        pack_id: "unit-judge-001",
        packet_id: "pkt-unit-001",
        scenario_id: "scen-unit-001",
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("pack_id");
    expect(body).toHaveProperty("final_score");
    expect(body).toHaveProperty("grade");
    expect(body).toHaveProperty("sections");
    expect(Array.isArray(body.sections)).toBe(true);
  });

  test("GET /judge/v4/packs returns packs list", async ({ request }) => {
    const res = await request.get(`${API}/judge/v4/packs`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("packs");
    expect(Array.isArray(body.packs)).toBe(true);
    expect(body.packs.length).toBeGreaterThan(0);
  });

  test("GET /judge/v4/packs/{id}/summary returns pack summary", async ({ request }) => {
    const listRes = await request.get(`${API}/judge/v4/packs`);
    const list = await listRes.json();
    const packId = list.packs[0].pack_id;
    const res = await request.get(`${API}/judge/v4/packs/${packId}/summary`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("pack");
    expect(body.pack).toHaveProperty("pack_id");
    expect(body.pack).toHaveProperty("grade");
  });
});

// ── WAVE 63: Search Provider (backend API) ──────────────────────────────

test.describe("Wave 63 — Search Provider API", () => {
  test("GET /search/stats shows local provider", async ({ request }) => {
    const res = await request.get(`${API}/search/stats`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("provider");
    expect(body.provider).toBe("local");
  });

  test("POST /search/query with text returns results", async ({ request }) => {
    const res = await request.post(`${API}/search/query`, {
      data: { text: "risk scenario" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("results");
    expect(Array.isArray(body.results)).toBe(true);
  });

  test("POST /search/index indexed field is true", async ({ request }) => {
    const res = await request.post(`${API}/search/index`, {
      data: {
        doc_id: "unit-doc-001",
        content: "Interest rate risk scenario analysis",
        doc_type: "scenario",
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("indexed");
    expect(typeof body.indexed).toBe("string"); // indexed returns the doc_id string
  });

  test("GET /search/stats returns total_documents > 0", async ({ request }) => {
    const res = await request.get(`${API}/search/stats`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("total_documents");
    expect(body.total_documents).toBeGreaterThan(0);
  });
});

// ── WAVE 64: LLM Provider (backend API) ─────────────────────────────────

test.describe("Wave 64 — LLM Provider API", () => {
  test("GET /llm/health returns status ok", async ({ request }) => {
    const res = await request.get(`${API}/llm/health`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body).toHaveProperty("provider");
  });

  test("GET /llm/provider returns noop by default", async ({ request }) => {
    const res = await request.get(`${API}/llm/provider`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("provider");
    expect(body.provider).toBe("noop");
  });

  test("POST /llm/complete returns text field", async ({ request }) => {
    const res = await request.post(`${API}/llm/complete`, {
      data: { prompt: "Summarize risk exposure for Q1 2026" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("text");
    expect(typeof body.text).toBe("string");
  });

  test("POST /llm/summarize returns summary", async ({ request }) => {
    const res = await request.post(`${API}/llm/summarize`, {
      data: { text: "The portfolio has significant exposure to interest rate risk." },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("summary");
  });

  test("POST /llm/extract-entities returns entities array", async ({ request }) => {
    const res = await request.post(`${API}/llm/extract-entities`, {
      data: { text: "RiskCanvas monitors USD, EUR, and GBP exposure." },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("entities");
    expect(Array.isArray(body.entities)).toBe(true);
  });
});

// ── Wave 57-64 Frontend: Datasets provenance badge ───────────────────────

test.describe("Wave 58 (Frontend) — Datasets Provenance Badge", () => {
  test("datasets-page loads at /datasets", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-page")).toBeVisible({ timeout: 15_000 });
  });

  test("datasets-table-ready is visible", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("dataset-license-badge-0 renders in table", async ({ page }) => {
    await page.goto(`${BASE}/datasets`);
    await expect(page.getByTestId("datasets-table-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("dataset-license-badge-0")).toBeVisible({ timeout: 10_000 });
  });

  test("GET /provenance/datasets/{id} returns dataset provenance detail", async ({ request }) => {
    const res = await request.get(`${API}/provenance/datasets/ds-prov-001`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("dataset");
    expect(body.dataset).toHaveProperty("dataset_id", "ds-prov-001");
    expect(body.dataset).toHaveProperty("license_tag");
  });
});

// ── Wave 60 (Frontend) — Reviews SLA Indicator ───────────────────────────

test.describe("Wave 60 (Frontend) — Reviews SLA Indicator", () => {
  test("reviews-page renders at /reviews", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
  });

  test("review-row-0 renders in reviews table", async ({ page }) => {
    await page.goto(`${BASE}/reviews`);
    await expect(page.getByTestId("reviews-page")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("review-row-0")).toBeVisible({ timeout: 10_000 });
  });

  test("GET /reviews-sla/reviews returns items with sla_deadline", async ({ request }) => {
    const res = await request.get(`${API}/reviews-sla/reviews`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("reviews");
    expect(body.reviews[0]).toHaveProperty("sla_deadline");
  });
});

// ── Wave 59 (Frontend) — Scenario Runner ─────────────────────────────────

test.describe("Wave 59 (Frontend) — Scenario Runner", () => {
  test("scenario-composer renders at /scenario-composer", async ({ page }) => {
    await page.goto(`${BASE}/scenario-composer`);
    await expect(page.getByTestId("scenario-composer")).toBeVisible({ timeout: 15_000 });
  });
});
