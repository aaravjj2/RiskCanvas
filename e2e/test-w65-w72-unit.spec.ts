/**
 * test-w65-w72-unit.spec.ts
 * Wave 65-72 — Evidence Graph, Decision Rooms, Agent Runbooks,
 *   Policy Decision Gate, Exports Room Snapshot, EvidenceBar, Judge v4
 * v5.54.0 → v5.61.0
 *
 * ALL selectors use data-testid ONLY.
 * No waitForTimeout. retries=0. workers=1.
 */
import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:4177";
const API = "http://localhost:8090";

// ── Wave 65: Evidence Graph API ─────────────────────────────────────────────

test.describe("Wave 65 — Evidence Graph API", () => {
  test("GET /evidence/graph returns 200", async ({ request }) => {
    const res = await request.get(`${API}/evidence/graph`);
    expect(res.ok()).toBe(true);
  });

  test("GET /evidence/graph has node_count and edge_count", async ({ request }) => {
    const body = await (await request.get(`${API}/evidence/graph`)).json();
    expect(body).toHaveProperty("node_count");
    expect(body).toHaveProperty("edge_count");
    expect(body.node_count).toBeGreaterThan(0);
  });

  test("GET /evidence/graph has graph_hash", async ({ request }) => {
    const body = await (await request.get(`${API}/evidence/graph`)).json();
    expect(body).toHaveProperty("graph_hash");
    expect(typeof body.graph_hash).toBe("string");
    expect(body.graph_hash.length).toBeGreaterThan(0);
  });

  test("GET /evidence/graph/summary returns 200 with summary_hash", async ({ request }) => {
    const res = await request.get(`${API}/evidence/graph/summary`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("summary_hash");
    expect(body).toHaveProperty("node_count");
  });

  test("GET /evidence/graph/summary has counts_by_type with dataset", async ({ request }) => {
    const body = await (await request.get(`${API}/evidence/graph/summary`)).json();
    expect(body).toHaveProperty("counts_by_type");
    expect(body.counts_by_type).toHaveProperty("dataset");
  });

  test("POST /evidence/graph/nodes adds node", async ({ request }) => {
    const res = await request.post(`${API}/evidence/graph/nodes`, {
      data: {
        node_id: "e2e-node-w65-001",
        node_type: "run",
        label: "E2E Test Node W65",
        tenant_id: "e2e-tenant",
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("node");
    expect(body.node.node_id).toBe("e2e-node-w65-001");
  });

  test("POST /evidence/graph/edges adds edge", async ({ request }) => {
    const res = await request.post(`${API}/evidence/graph/edges`, {
      data: { src: "ds-prov-001", dst: "run-001", edge_type: "uses" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("edge");
  });

  test("GET /evidence/graph/bfs returns connected nodes", async ({ request }) => {
    const res = await request.get(`${API}/evidence/graph/bfs?start_id=ds-prov-001&depth=2`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("nodes");
    expect(Array.isArray(body.nodes)).toBe(true);
  });
});

// ── Wave 65: Evidence Graph Frontend ───────────────────────────────────────

test.describe("Wave 65 — Evidence Graph Frontend", () => {
  test("evidence page renders at /evidence", async ({ page }) => {
    await page.goto(`${BASE}/evidence`);
    await expect(page.getByTestId("evidence-page")).toBeVisible({ timeout: 15_000 });
  });

  test("evidence-summary-ready is visible", async ({ page }) => {
    await page.goto(`${BASE}/evidence`);
    await expect(page.getByTestId("evidence-summary-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("evidence-node-count renders", async ({ page }) => {
    await page.goto(`${BASE}/evidence`);
    await expect(page.getByTestId("evidence-summary-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("evidence-node-count")).toBeVisible({ timeout: 10_000 });
  });
});

// ── Wave 66: Decision Rooms API ─────────────────────────────────────────────

test.describe("Wave 66 — Decision Rooms API", () => {
  test("GET /rooms returns 200 with rooms array", async ({ request }) => {
    const res = await request.get(`${API}/rooms`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("rooms");
    expect(Array.isArray(body.rooms)).toBe(true);
  });

  test("POST /rooms creates a new room", async ({ request }) => {
    const res = await request.post(`${API}/rooms`, {
      data: { name: "E2E Unit Test Room", subject_id: "scen-e2e" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("room");
    expect(body.room.name).toBe("E2E Unit Test Room");
    expect(body.room.status).toBe("OPEN");
  });

  test("GET /rooms/{id} returns room by id", async ({ request }) => {
    const res = await request.get(`${API}/rooms/room-demo-001`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("room");
    expect(body.room.room_id).toBe("room-demo-001");
  });

  test("POST /rooms/{id}/pin adds pinned entity", async ({ request }) => {
    // Create a fresh OPEN room to avoid issues with locked rooms from previous runs
    const create = await request.post(`${API}/rooms`, {
      data: { name: "Pin Test Room E2E W66", subject_id: "scen-pin" },
    });
    const freshRoom = (await create.json()).room;
    const res = await request.post(`${API}/rooms/${freshRoom.room_id}/pin`, {
      data: { entity_id: "e2e-entity-w66-001", entity_type: "run", pinned_by: "e2e" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("room_id");
    expect(body).toHaveProperty("pinned_entities");
  });

  test("POST /rooms/{id}/lock locks the room", async ({ request }) => {
    const create = await request.post(`${API}/rooms`, {
      data: { name: "Room to Lock E2E", subject_id: "scen-lock" },
    });
    const room = (await create.json()).room;
    const res = await request.post(`${API}/rooms/${room.room_id}/lock`, {
      data: { locked_by: "e2e-user" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.room.status).toBe("LOCKED");
  });

  test("GET /rooms/{id}/timeline returns timeline array", async ({ request }) => {
    const res = await request.get(`${API}/rooms/room-demo-001/timeline`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("room_id");
    const timelineKey = "timeline" in body ? "timeline" : "events";
    expect(Array.isArray(body[timelineKey])).toBe(true);
  });
});

// ── Wave 66: Decision Rooms Frontend ───────────────────────────────────────

test.describe("Wave 66 — Decision Rooms Frontend", () => {
  test("rooms page renders at /rooms", async ({ page }) => {
    await page.goto(`${BASE}/rooms`);
    await expect(page.getByTestId("rooms-page")).toBeVisible({ timeout: 15_000 });
  });

  test("rooms-ready is visible after data loads", async ({ page }) => {
    await page.goto(`${BASE}/rooms`);
    await expect(page.getByTestId("rooms-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("room-row-0 renders in table", async ({ page }) => {
    await page.goto(`${BASE}/rooms`);
    await expect(page.getByTestId("rooms-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("room-row-0")).toBeVisible({ timeout: 10_000 });
  });
});

// ── Wave 67: Agent Runbooks API ─────────────────────────────────────────────

test.describe("Wave 67 — Agent Runbooks API", () => {
  test("GET /runbooks returns runbooks array", async ({ request }) => {
    const res = await request.get(`${API}/runbooks?tenant_id=demo-tenant`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("runbooks");
    expect(body.runbooks.length).toBeGreaterThan(0);
  });

  test("POST /runbooks creates a runbook", async ({ request }) => {
    const res = await request.post(`${API}/runbooks`, {
      data: {
        name: "E2E API Runbook W67",
        description: "Created by e2e unit test",
        steps: [
          { step_type: "validate_dataset", params: { dataset_id: "ds-e2e" } },
          { step_type: "execute_run", params: { scenario_id: "scen-e2e", kind: "rate_shock", payload: {} } },
        ],
        tenant_id: "demo-tenant",
      },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("runbook");
    expect(body.runbook.name).toBe("E2E API Runbook W67");
  });

  test("GET /runbooks/{id} returns runbook with executions", async ({ request }) => {
    const res = await request.get(`${API}/runbooks/rb-demo-001`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("runbook");
    expect(body).toHaveProperty("executions");
    expect(body).toHaveProperty("execution_count");
  });

  test("POST /runbooks/{id}/execute returns completed execution", async ({ request }) => {
    const res = await request.post(`${API}/runbooks/rb-demo-001/execute`, {
      data: { executed_by: "e2e-unit" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.status).toBe("completed");
    expect(body.execution.status).toBe("completed");
  });

  test("execute result has outputs_hash of 16 chars", async ({ request }) => {
    const res = await request.post(`${API}/runbooks/rb-demo-001/execute`, {
      data: { executed_by: "e2e-hash" },
    });
    const body = await res.json();
    expect(body.execution.outputs_hash.length).toBe(16);
  });

  test("execute result step_results match step count", async ({ request }) => {
    const rb = (await (await request.get(`${API}/runbooks/rb-demo-001`)).json()).runbook;
    const res = await request.post(`${API}/runbooks/rb-demo-001/execute`, {
      data: { executed_by: "e2e-steps" },
    });
    const body = await res.json();
    expect(body.execution.step_results.length).toBe(rb.steps.length);
  });
});

// ── Wave 67: Agent Runbooks Frontend ───────────────────────────────────────

test.describe("Wave 67 — Agent Runbooks Frontend", () => {
  test("runbooks page renders at /runbooks", async ({ page }) => {
    await page.goto(`${BASE}/runbooks`);
    await expect(page.getByTestId("runbooks-page")).toBeVisible({ timeout: 15_000 });
  });

  test("runbooks-ready is visible after data loads", async ({ page }) => {
    await page.goto(`${BASE}/runbooks`);
    await expect(page.getByTestId("runbooks-ready")).toBeVisible({ timeout: 15_000 });
  });

  test("runbook-row-0 renders in list", async ({ page }) => {
    await page.goto(`${BASE}/runbooks`);
    await expect(page.getByTestId("runbooks-ready")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("runbook-row-0")).toBeVisible({ timeout: 10_000 });
  });
});

// ── Wave 68: Policy Decision Gate API ──────────────────────────────────────

test.describe("Wave 68 — Policy Decision Gate API", () => {
  test("POST /policy/decision-gate returns verdict", async ({ request }) => {
    const res = await request.post(`${API}/policy/decision-gate`, {
      data: { action: "room.lock", room_id: "room-demo-001" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("verdict");
    expect(["ALLOW", "BLOCK", "CONDITIONAL"]).toContain(body.verdict);
  });

  test("POST /policy/decision-gate has gate_hash of 16 chars", async ({ request }) => {
    const body = await (await request.post(`${API}/policy/decision-gate`, {
      data: { action: "room.lock", room_id: "room-demo-001" },
    })).json();
    expect(body.gate_hash.length).toBe(16);
  });

  test("POST /policy/decision-gate has reasons array", async ({ request }) => {
    const body = await (await request.post(`${API}/policy/decision-gate`, {
      data: { action: "room.lock", room_id: "room-demo-001" },
    })).json();
    expect(Array.isArray(body.reasons)).toBe(true);
    expect(body.reasons.length).toBeGreaterThan(0);
  });

  test("POST /policy/decision-gate/approve-review adds review", async ({ request }) => {
    const res = await request.post(`${API}/policy/decision-gate/approve-review?review_id=review-e2e-w68-001`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.status).toBe("APPROVED");
    expect(body.added).toBe(true);
  });

  test("unknown action defaults to ALLOW", async ({ request }) => {
    const body = await (await request.post(`${API}/policy/decision-gate`, {
      data: { action: "unknown.e2e.action", room_id: "room-any" },
    })).json();
    expect(body.verdict).toBe("ALLOW");
  });
});

// ── Wave 69: EvidenceBar Frontend ──────────────────────────────────────────

test.describe("Wave 69 — EvidenceBar Frontend", () => {
  test("evidence-bar is visible on /evidence", async ({ page }) => {
    await page.goto(`${BASE}/evidence`);
    await expect(page.getByTestId("evidence-bar")).toBeVisible({ timeout: 15_000 });
  });

  test("evidence-bar-graph-hash is visible", async ({ page }) => {
    await page.goto(`${BASE}/evidence`);
    await expect(page.getByTestId("evidence-bar")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("evidence-bar-graph-hash")).toBeVisible({ timeout: 10_000 });
  });
});

// ── Wave 70: Exports Room Snapshot API ──────────────────────────────────────

test.describe("Wave 70 — Exports Room Snapshot API", () => {
  test("POST /exports/room-snapshot returns generated snapshot", async ({ request }) => {
    const res = await request.post(`${API}/exports/room-snapshot`, {
      data: { room_id: "room-e2e-snap-001", tenant_id: "e2e-tenant" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.status).toBe("generated");
    expect(body).toHaveProperty("snapshot");
  });

  test("snapshot manifest_hash is 24 chars", async ({ request }) => {
    const res = await request.post(`${API}/exports/room-snapshot`, {
      data: { room_id: "room-e2e-hash-001" },
    });
    const body = await res.json();
    expect(body.snapshot.manifest_hash.length).toBe(24);
  });

  test("snapshot has required keys", async ({ request }) => {
    const res = await request.post(`${API}/exports/room-snapshot`, {
      data: { room_id: "room-e2e-keys-001" },
    });
    const snap = (await res.json()).snapshot;
    for (const key of ["snapshot_id", "room_id", "manifest_hash", "created_at"]) {
      expect(snap).toHaveProperty(key);
    }
  });

  test("GET /exports/room-snapshots returns list", async ({ request }) => {
    const res = await request.get(`${API}/exports/room-snapshots`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("snapshots");
    expect(body).toHaveProperty("count");
  });

  test("snapshot_id starts with 'snap-'", async ({ request }) => {
    const res = await request.post(`${API}/exports/room-snapshot`, {
      data: { room_id: "room-e2e-fmt-001" },
    });
    const body = await res.json();
    expect(body.snapshot.snapshot_id.startsWith("snap-")).toBe(true);
  });
});

// ── Wave 71: Judge Mode v4 API ──────────────────────────────────────────────

test.describe("Wave 71 — Judge Mode v4 API", () => {
  test("POST /judge/v4/generate returns grade and score", async ({ request }) => {
    const res = await request.post(`${API}/judge/v4/generate`, {
      data: { generated_by: "e2e-unit-w71" },
    });
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("grade");
    expect(body).toHaveProperty("final_score");
    expect(["A", "B", "C", "D", "F"]).toContain(body.grade);
    expect(body.final_score).toBeGreaterThan(0);
  });

  test("POST /judge/v4/generate has sections array", async ({ request }) => {
    const body = await (await request.post(`${API}/judge/v4/generate`, {
      data: { generated_by: "e2e" },
    })).json();
    expect(Array.isArray(body.sections)).toBe(true);
    expect(body.sections.length).toBeGreaterThan(0);
    expect(body.sections[0]).toHaveProperty("section");
    expect(body.sections[0]).toHaveProperty("score");
    expect(body.sections[0]).toHaveProperty("weight");
  });

  test("GET /judge/v4/packs returns packs list", async ({ request }) => {
    await request.post(`${API}/judge/v4/generate`, { data: { generated_by: "e2e" } });
    const res = await request.get(`${API}/judge/v4/packs`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body).toHaveProperty("packs");
    expect(body).toHaveProperty("count");
    expect(body.count).toBeGreaterThan(0);
  });

  test("GET /judge/v4/packs/{id}/summary returns grade", async ({ request }) => {
    const gen = await (await request.post(`${API}/judge/v4/generate`, {
      data: { generated_by: "e2e-summary" },
    })).json();
    const res = await request.get(`${API}/judge/v4/packs/${gen.pack_id}/summary`);
    expect(res.ok()).toBe(true);
    const body = await res.json();
    expect(body.pack).toHaveProperty("grade");
    expect(body.pack).toHaveProperty("final_score");
  });
});

// ── Wave 71: Judge Mode v4 Frontend ────────────────────────────────────────

test.describe("Wave 71 — Judge Mode v4 Frontend", () => {
  test("judge-mode-page renders at /judge-mode", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-mode-page")).toBeVisible({ timeout: 15_000 });
  });

  test("judge-v4-section is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-v4-section")).toBeVisible({ timeout: 15_000 });
  });

  test("judge-v4-generate-btn is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-v4-generate-btn")).toBeVisible({ timeout: 15_000 });
  });

  test("judge-launch-rail is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("judge-launch-rail")).toBeVisible({ timeout: 15_000 });
  });

  test("launch-azure button is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("launch-azure")).toBeVisible({ timeout: 15_000 });
  });

  test("launch-gitlab button is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("launch-gitlab")).toBeVisible({ timeout: 15_000 });
  });

  test("launch-digitalocean button is visible", async ({ page }) => {
    await page.goto(`${BASE}/judge-mode`);
    await expect(page.getByTestId("launch-digitalocean")).toBeVisible({ timeout: 15_000 });
  });

  test("nav has evidence-bar on all pages", async ({ page }) => {
    await page.goto(`${BASE}/rooms`);
    await expect(page.getByTestId("evidence-bar")).toBeVisible({ timeout: 15_000 });
  });
});
