/**
 * test-depth-e2e.spec.ts — Depth Wave behavioral E2E tests (v5.56.1–v5.60.0)
 *
 * Validates the 6 new depth wave capabilities:
 *   A. Run Outcomes — GET /runs/{id}/outcome determinism
 *   B. Eval Harness v3 — POST /eval/v3/run idempotency + schema
 *   C. Explainability — POST /explain/verdict stable explain_id
 *   D. Policy Gate v3 — POST /policy/v3/decision BLOCK/SHIP logic
 *   E. MCP Tools v2 — GET /mcp/v2/tools + POST /mcp/v2/tools/call
 *   F. DevOps Offline MR — POST /devops/mr/offline/review-and-open
 *   G. UI — /evals, /rooms, /devops, /microsoft pages render
 *
 * ALL selectors use data-testid ONLY. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const API = "http://localhost:8090";
const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4178";

// ═══════════════════════════════════════════════════════════════════════════════
// A. Run Outcomes
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow A — Run Outcomes", () => {
  test("GET /runs/{id}/outcome returns deterministic metrics", async ({ request }) => {
    const r = await request.get(`${API}/runs/demo-run-depth-001/outcome`);
    expect(r.ok()).toBe(true);
    const body = await r.json();
    const o = body.outcome;
    expect(o.run_id).toBe("demo-run-depth-001");
    expect(typeof o.pnl_total).toBe("number");
    expect(typeof o.var_95).toBe("number");
    expect(typeof o.var_99).toBe("number");
    expect(typeof o.max_drawdown_proxy).toBe("number");
    expect(typeof o.completeness_score).toBe("number");
    expect(o.pnl_total).toBeLessThanOrEqual(0);
  });

  test("GET /runs/{id}/outcome is idempotent — same id → same metrics", async ({ request }) => {
    const [r1, r2] = await Promise.all([
      request.get(`${API}/runs/demo-run-idempotent-xx/outcome`),
      request.get(`${API}/runs/demo-run-idempotent-xx/outcome`),
    ]);
    expect(r1.ok()).toBe(true);
    expect(r2.ok()).toBe(true);
    const o1 = (await r1.json()).outcome;
    const o2 = (await r2.json()).outcome;
    expect(o1.pnl_total).toBe(o2.pnl_total);
    expect(o1.var_95).toBe(o2.var_95);
    expect(o1.completeness_score).toBe(o2.completeness_score);
  });

  test("GET /runs/outcomes returns list", async ({ request }) => {
    const r = await request.get(`${API}/runs/outcomes?limit=5`);
    expect(r.ok()).toBe(true);
    const body = await r.json();
    expect(Array.isArray(body.outcomes)).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// B. Eval Harness v3
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow B — Eval Harness v3", () => {
  const RUN_IDS = ["demo-run-e2e-001", "demo-run-e2e-002"];

  test("POST /eval/v3/run returns eval with stable id", async ({ request }) => {
    const r = await request.post(`${API}/eval/v3/run`, {
      data: { run_ids: RUN_IDS },
    });
    expect(r.ok()).toBe(true);
    const body = await r.json();
    const ev = body.eval;
    expect(ev.eval_id).toMatch(/^eval3-/);
    expect(ev.harness_version).toBe("v3");
    expect(typeof ev.metrics.calibration_error).toBe("number");
    expect(typeof ev.metrics.drift_score).toBe("number");
    expect(typeof ev.metrics.stability_score).toBe("number");
  });

  test("POST /eval/v3/run is idempotent — same run_ids → same eval_id", async ({ request }) => {
    const [r1, r2] = await Promise.all([
      request.post(`${API}/eval/v3/run`, { data: { run_ids: RUN_IDS } }),
      request.post(`${API}/eval/v3/run`, { data: { run_ids: RUN_IDS } }),
    ]);
    expect(r1.ok()).toBe(true);
    expect(r2.ok()).toBe(true);
    const id1 = (await r1.json()).eval.eval_id;
    const id2 = (await r2.json()).eval.eval_id;
    expect(id1).toBe(id2);
  });

  test("POST /eval/v3/run order independent — sorted run_ids same eval_id", async ({ request }) => {
    const [r1, r2] = await Promise.all([
      request.post(`${API}/eval/v3/run`, { data: { run_ids: ["aaa", "zzz"] } }),
      request.post(`${API}/eval/v3/run`, { data: { run_ids: ["zzz", "aaa"] } }),
    ]);
    const id1 = (await r1.json()).eval.eval_id;
    const id2 = (await r2.json()).eval.eval_id;
    expect(id1).toBe(id2);
  });

  test("GET /eval/v3/{eval_id} retrieves stored eval", async ({ request }) => {
    const createR = await request.post(`${API}/eval/v3/run`, {
      data: { run_ids: ["get-test-run-001"] },
    });
    const { eval: ev } = await createR.json();
    const getR = await request.get(`${API}/eval/v3/${ev.eval_id}`);
    expect(getR.ok()).toBe(true);
    const body = await getR.json();
    expect(body.eval.eval_id).toBe(ev.eval_id);
  });

  test("Eval metrics pass thresholds in demo mode", async ({ request }) => {
    const r = await request.post(`${API}/eval/v3/run`, {
      data: { run_ids: ["thresh-check-001", "thresh-check-002"] },
    });
    const ev = (await r.json()).eval;
    expect(ev.metrics.calibration_error).toBeLessThanOrEqual(0.05);
    expect(ev.metrics.drift_score).toBeLessThanOrEqual(0.20);
    expect(ev.metrics.stability_score).toBeGreaterThanOrEqual(0.90);
    expect(ev.passed).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// C. Explainability
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow C — Explainability", () => {
  test("POST /explain/verdict returns stable explain_id", async ({ request }) => {
    const r = await request.post(`${API}/explain/verdict`, {
      data: {
        dataset_id: "ds-e2e-001",
        scenario_id: "sc-e2e-001",
        run_id: "run-e2e-001",
        review_id: "rev-e2e-001",
      },
    });
    expect(r.ok()).toBe(true);
    const body = await r.json();
    expect(body.explanation.explain_id).toMatch(/^expl-/);
    expect(Array.isArray(body.explanation.reasons)).toBe(true);
    expect(body.explanation.reasons.length).toBeGreaterThan(0);
  });

  test("POST /explain/verdict is idempotent — same inputs → same explain_id", async ({ request }) => {
    const payload = {
      dataset_id: "ds-idem-001",
      scenario_id: "sc-idem-001",
      run_id: "run-idem-001",
      review_id: "rev-idem-001",
    };
    const [r1, r2] = await Promise.all([
      request.post(`${API}/explain/verdict`, { data: payload }),
      request.post(`${API}/explain/verdict`, { data: payload }),
    ]);
    const id1 = (await r1.json()).explanation.explain_id;
    const id2 = (await r2.json()).explanation.explain_id;
    expect(id1).toBe(id2);
  });

  test("GET /explain/{id} retrieves stored explanation", async ({ request }) => {
    const createR = await request.post(`${API}/explain/verdict`, {
      data: { dataset_id: "ds-get-001", scenario_id: "sc-get-001" },
    });
    const { explanation } = await createR.json();
    const getR = await request.get(`${API}/explain/${explanation.explain_id}`);
    expect(getR.ok()).toBe(true);
    const body = await getR.json();
    expect(body.explanation.explain_id).toBe(explanation.explain_id);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// D. Policy Gate v3
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow D — Policy Gate v3", () => {
  test("POST /policy/v3/decision returns verdict and decision_id", async ({ request }) => {
    const r = await request.post(`${API}/policy/v3/decision`, {
      data: {
        subject_type: "dataset",
        subject_id: "ds-policy-e2e-001",
      },
    });
    expect(r.ok()).toBe(true);
    const body = await r.json();
    const d = body.decision;
    expect(d.decision_id).toMatch(/^pv3-/);
    expect(["SHIP", "CONDITIONAL", "BLOCK"]).toContain(d.verdict);
    expect(Array.isArray(d.reasons)).toBe(true);
  });

  test("POST /policy/v3/decision is deterministic — same inputs → same decision_id", async ({ request }) => {
    const payload = { subject_type: "scenario", subject_id: "sc-det-e2e-001" };
    const [r1, r2] = await Promise.all([
      request.post(`${API}/policy/v3/decision`, { data: payload }),
      request.post(`${API}/policy/v3/decision`, { data: payload }),
    ]);
    const d1 = (await r1.json()).decision;
    const d2 = (await r2.json()).decision;
    expect(d1.decision_id).toBe(d2.decision_id);
    expect(d1.verdict).toBe(d2.verdict);
  });

  test("GET /policy/v3/decision/{id} retrieves stored decision", async ({ request }) => {
    const createR = await request.post(`${API}/policy/v3/decision`, {
      data: { subject_type: "policy_check", subject_id: "pc-get-e2e-001" },
    });
    const { decision } = await createR.json();
    const getR = await request.get(`${API}/policy/v3/decision/${decision.decision_id}`);
    expect(getR.ok()).toBe(true);
    const body = await getR.json();
    expect(body.decision.decision_id).toBe(decision.decision_id);
    expect(body.decision.verdict).toBe(decision.verdict);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// E. MCP Tools v2
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow E — MCP Tools v2", () => {
  test("GET /mcp/v2/tools returns exactly 8 tools", async ({ request }) => {
    const r = await request.get(`${API}/mcp/v2/tools`);
    expect(r.ok()).toBe(true);
    const body = await r.json();
    expect(Array.isArray(body.tools)).toBe(true);
    expect(body.tools.length).toBe(8);
  });

  test("GET /mcp/v2/tools tool names are stable", async ({ request }) => {
    const r = await request.get(`${API}/mcp/v2/tools`);
    const { tools } = await r.json();
    const names = tools.map((t: any) => t.name);
    const expected = [
      "ingest_dataset", "create_scenario", "execute_run", "replay_run",
      "request_review", "approve_review", "export_packet", "run_eval",
    ];
    for (const name of expected) {
      expect(names).toContain(name);
    }
  });

  test("POST /mcp/v2/tools/call ingest_dataset returns deterministic result", async ({ request }) => {
    const r = await request.post(`${API}/mcp/v2/tools/call`, {
      data: {
        tool: "ingest_dataset",
        inputs: {
          name: "E2E MCP Dataset",
          kind: "portfolio",
          payload: { positions: [{ ticker: "AAPL", quantity: 100, cost_basis: 178.5 }] },
          created_by: "mcp-e2e@rc.io",
        },
        agent_id: "e2e-agent",
      },
    });
    expect(r.ok()).toBe(true);
    const body = await r.json();
    expect(body.result).toBeDefined();
    expect(body.tool).toBe("ingest_dataset");
  });

  test("GET /mcp/v2/audit returns audit log", async ({ request }) => {
    // First make a call to ensure log has entries
    await request.post(`${API}/mcp/v2/tools/call`, {
      data: {
        tool: "ingest_dataset",
        inputs: { name: "Audit Test", kind: "portfolio", payload: {}, created_by: "audit-agent" },
        agent_id: "audit-agent",
      },
    });
    const r = await request.get(`${API}/mcp/v2/audit`);
    expect(r.ok()).toBe(true);
    const body = await r.json();
    expect(Array.isArray(body.entries)).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// F. DevOps Offline MR Review
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow F — DevOps Offline MR Review", () => {
  const CLEAN_DIFF = "+def validate_portfolio():\n+    return True\n";
  const RISKY_DIFF = "+API_KEY = 'abc123'\n+password = 'hunter2'\n";

  test("POST /devops/mr/offline/review-and-open pipeline succeeds", async ({ request }) => {
    const r = await request.post(`${API}/devops/mr/offline/review-and-open`, {
      data: {
        diff: CLEAN_DIFF,
        mr_title: "Portfolio validator",
        mr_iid: "100",
        reviewer: "reviewer@rc.io",
      },
    });
    expect(r.ok()).toBe(true);
    const body = await r.json();
    const res = body.result;
    expect(res.subject_id).toBeTruthy();
    expect(["SHIP", "CONDITIONAL", "BLOCK"]).toContain(res.policy_verdict);
    expect(res.review.review_id).toBeTruthy();
  });

  test("Risky diff triggers high-severity findings and BLOCK verdict", async ({ request }) => {
    const r = await request.post(`${API}/devops/mr/offline/review-and-open`, {
      data: {
        diff: RISKY_DIFF,
        mr_title: "Risky PR",
        mr_iid: "200",
        reviewer: "reviewer@rc.io",
      },
    });
    expect(r.ok()).toBe(true);
    const res = (await r.json()).result;
    const highFindings = res.diff_scan.findings.filter((f: any) => f.severity === "high");
    expect(highFindings.length).toBeGreaterThan(0);
    expect(res.policy_verdict).toBe("BLOCK");
  });

  test("Clean diff passes scan (no high-severity findings)", async ({ request }) => {
    const r = await request.post(`${API}/devops/mr/offline/review-and-open`, {
      data: { diff: CLEAN_DIFF, mr_title: "Clean PR", mr_iid: "300", reviewer: "r@demo" },
    });
    const res = (await r.json()).result;
    expect(res.diff_scan.passed).toBe(true);
  });

  test("Pipeline is deterministic — same inputs → same subject_id", async ({ request }) => {
    const payload = { diff: CLEAN_DIFF, mr_title: "Same PR", mr_iid: "400", reviewer: "r@demo" };
    const [r1, r2] = await Promise.all([
      request.post(`${API}/devops/mr/offline/review-and-open`, { data: payload }),
      request.post(`${API}/devops/mr/offline/review-and-open`, { data: payload }),
    ]);
    const id1 = (await r1.json()).result.subject_id;
    const id2 = (await r2.json()).result.subject_id;
    expect(id1).toBe(id2);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// G. UI Pages — Depth Wave
// ═══════════════════════════════════════════════════════════════════════════════

test.describe("Flow G — Depth Wave UI Pages", () => {
  test("/evals page renders with expected testids", async ({ page }) => {
    await page.goto(`${BASE}/evals`);
    await expect(page.getByTestId("evals-page")).toBeVisible({ timeout: 20_000 });
  });

  test("/evals eval-run-btn is clickable and creates eval", async ({ page }) => {
    await page.goto(`${BASE}/evals`);
    await expect(page.getByTestId("evals-page")).toBeVisible({ timeout: 20_000 });
    const runBtn = page.getByTestId("eval-run-btn");
    await expect(runBtn).toBeVisible();
    await runBtn.click();
    // Wait for either table or metric card to appear
    await expect(
      page.getByTestId("evals-table-ready").or(page.getByTestId("eval-metric-calibration"))
    ).toBeVisible({ timeout: 15_000 });
  });

  test("/rooms page renders decision rooms with testids", async ({ page }) => {
    await page.goto(`${BASE}/rooms`);
    await expect(page.getByTestId("rooms-page")).toBeVisible({ timeout: 20_000 });
  });

  test("/devops offline-review tab is reachable", async ({ page }) => {
    await page.goto(`${BASE}/devops`);
    await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 20_000 });
    const offlineTab = page.getByTestId("devops-tab-offline");
    await expect(offlineTab).toBeVisible();
    await offlineTab.click();
    await expect(page.getByTestId("devops-panel-offline")).toBeVisible({ timeout: 10_000 });
  });

  test("/devops offline review-open button triggers review creation", async ({ page }) => {
    await page.goto(`${BASE}/devops`);
    await expect(page.getByTestId("devops-page")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("devops-tab-offline").click();
    await expect(page.getByTestId("devops-panel-offline")).toBeVisible();
    const reviewBtn = page.getByTestId("devops-review-open");
    await expect(reviewBtn).toBeVisible();
    await reviewBtn.click();
    // Wait for result to appear (verdict badge)
    await expect(page.getByTestId("devops-offline-verdict")).toBeVisible({ timeout: 20_000 });
  });

  test("/microsoft page renders with MCP v2 plan", async ({ page }) => {
    await page.goto(`${BASE}/microsoft`);
    await expect(page.getByTestId("microsoft-mode-page")).toBeVisible({ timeout: 20_000 });
    // MCP v2 run plan button should be present
    await expect(page.getByTestId("ms-run-plan")).toBeVisible({ timeout: 10_000 });
  });
});
