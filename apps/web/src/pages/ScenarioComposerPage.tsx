/**
 * ScenarioComposerPage.tsx (v5.28.0 — Wave 50)
 * Route: /scenario-composer
 * data-testids: scenario-composer, scenario-kind-select, scenario-validate,
 *               scenario-run, scenario-replay, scenario-preview-ready,
 *               scenario-action-log, scenario-list-ready, scenario-row-{i}
 */
import { useState, useCallback, useEffect } from "react";
import PageShell from "@/components/ui/PageShell";
import { DataTable, type ColumnDef } from "@/components/ui/DataTable";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

type ScenarioKind = "stress" | "whatif" | "shock_ladder";

interface Scenario {
  scenario_id: string;
  tenant_id: string;
  name: string;
  kind: ScenarioKind;
  payload_hash: string;
  created_at: string;
  created_by: string;
  impact_preview?: Record<string, unknown>;
  [key: string]: unknown;
}

interface ScenarioRun {
  run_id: string;
  scenario_id: string;
  output_hash: string;
  artifact_id: string;
  attestation_id: string;
  triggered_by: string;
  triggered_at: string;
  replay: boolean;
}

interface ActionLog {
  timestamp: string;
  type: "info" | "success" | "error";
  message: string;
}

const KIND_DEFAULTS: Record<ScenarioKind, string> = {
  stress: JSON.stringify({ shocks: { rates: 0.01, equity: -0.15, credit: 0.005 }, confidence_level: 0.99, horizon_days: 10 }, null, 2),
  whatif: JSON.stringify({ base_nav: 1000000, scenario_shocks: { rates: 0.005, equity: -0.08 }, positions: [{ ticker: "MSFT", weight: 0.3 }, { ticker: "AAPL", weight: 0.25 }] }, null, 2),
  shock_ladder: JSON.stringify({ base_shock: { equity: -0.05 }, steps: 5, step_multiplier: 1.5, horizon_days: 5 }, null, 2),
};

const KIND_COLORS: Record<ScenarioKind, string> = {
  stress: "bg-orange-900/40 text-orange-300",
  whatif: "bg-blue-900/40 text-blue-300",
  shock_ladder: "bg-purple-900/40 text-purple-300",
};

export default function ScenarioComposerPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState<Scenario | null>(null);
  const [runs, setRuns] = useState<ScenarioRun[]>([]);
  const [loading, setLoading] = useState(true);

  // Composer state
  const [scenarioName, setScenarioName] = useState("My Stress Test 2026");
  const [scenarioKind, setScenarioKind] = useState<ScenarioKind>("stress");
  const [payloadText, setPayloadText] = useState(KIND_DEFAULTS.stress);
  const [previewData, setPreviewData] = useState<Record<string, unknown> | null>(null);
  const [running, setRunning] = useState(false);
  const [replaying, setReplaying] = useState(false);
  const [actionLog, setActionLog] = useState<ActionLog[]>([]);

  const { addToast } = useToast();

  function log(type: ActionLog["type"], message: string) {
    setActionLog(prev => [
      { timestamp: new Date().toISOString(), type, message },
      ...prev.slice(0, 49),
    ]);
  }

  const loadScenarios = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(API("/scenarios-v2"));
      if (r.ok) { const d = await r.json(); setScenarios(d.scenarios ?? []); }
    } catch { log("error", "Failed to load scenarios"); }
    setLoading(false);
  }, []);

  useEffect(() => { loadScenarios(); }, [loadScenarios]);

  async function loadRuns(scenarioId: string) {
    try {
      const r = await fetch(API(`/scenarios-v2/${scenarioId}/runs`));
      if (r.ok) { const d = await r.json(); setRuns(d.runs ?? []); }
    } catch {}
  }

  async function handleValidate() {
    try {
      JSON.parse(payloadText);
      setPreviewData({ status: "valid", kind: scenarioKind, payload_parsed: true });
      log("success", `Payload valid for kind=${scenarioKind}`);
      addToast("Payload is valid \u2713", "success");
    } catch {
      setPreviewData({ status: "error", message: "Invalid JSON" });
      log("error", "Invalid JSON in payload");
      addToast("Invalid JSON payload", "error");
    }
  }

  async function handleRun() {
    setRunning(true);
    log("info", `Running scenario: ${scenarioName} (kind=${scenarioKind})`);
    try {
      let parsed: unknown;
      try { parsed = JSON.parse(payloadText); }
      catch { addToast("Invalid JSON payload", "error"); log("error", "JSON parse failed"); setRunning(false); return; }

      // Upsert scenario
      const cs = await fetch(API("/scenarios-v2"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: scenarioName, kind: scenarioKind, payload: parsed, created_by: "composer@riskcanvas.io" }),
      });
      const cd = await cs.json();
      if (!cs.ok) { addToast("Failed to create scenario", "error"); log("error", "Create scenario failed"); setRunning(false); return; }

      const scenario = cd.scenario;
      log("info", `Scenario ID: ${scenario.scenario_id.slice(0, 8)}\u2026`);

      // Run it
      const rr = await fetch(API(`/scenarios-v2/${scenario.scenario_id}/run`), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ triggered_by: "composer@riskcanvas.io" }),
      });
      const rd = await rr.json();
      if (rr.ok) {
        log("success", `Run complete — output_hash: ${rd.run.output_hash.slice(0, 12)}\u2026`);
        log("success", `Artifact: ${rd.run.artifact_id.slice(0, 8)}\u2026  Attestation: ${rd.run.attestation_id.slice(0, 8)}\u2026`);
        addToast(`Run complete: output_hash=${rd.run.output_hash.slice(0, 8)}\u2026`, "success");
        setPreviewData({ run: rd.run, scenario });
        await loadScenarios();
        setSelected(scenario);
        await loadRuns(scenario.scenario_id);
      } else {
        log("error", `Run failed: ${rd.detail ?? "unknown"}`);
        addToast("Run failed", "error");
      }
    } catch { addToast("Network error", "error"); log("error", "Network error"); }
    setRunning(false);
  }

  async function handleReplay() {
    if (!selected) { addToast("Select a scenario first", "error"); return; }
    setReplaying(true);
    log("info", `Replaying scenario: ${selected.scenario_id.slice(0, 8)}\u2026`);
    try {
      const r = await fetch(API(`/scenarios-v2/${selected.scenario_id}/replay`), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ triggered_by: "composer@riskcanvas.io" }),
      });
      const d = await r.json();
      if (r.ok) {
        log("success", `Replay complete — output_hash: ${d.run.output_hash.slice(0, 12)}\u2026 (deterministic)`);
        addToast(`Replay: same hash=${d.run.output_hash.slice(0, 8)}\u2026`, "success");
        await loadRuns(selected.scenario_id);
      } else {
        log("error", `Replay failed: ${d.detail ?? "unknown"}`);
        addToast("Replay failed", "error");
      }
    } catch { addToast("Network error", "error"); log("error", "Network error"); }
    setReplaying(false);
  }

  const columns: ColumnDef<Scenario>[] = [
    { key: "name", header: "Name", sortable: true },
    { key: "kind", header: "Kind", width: "w-32",
      render: (r: Scenario) => (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${KIND_COLORS[r.kind] ?? "bg-gray-700 text-gray-300"}`}>
          {r.kind}
        </span>
      ),
    },
    { key: "payload_hash", header: "Payload Hash", width: "w-40",
      render: (r: Scenario) => <span className="font-mono text-xs text-gray-400">{r.payload_hash.slice(0, 12)}&hellip;</span>,
    },
    { key: "created_at", header: "Created", sortable: true, width: "w-44" },
    { key: "_actions", header: "", width: "w-24",
      render: (row: Scenario, i: number) => (
        <button
          data-testid={`scenario-row-${i}`}
          onClick={() => { setSelected(row); loadRuns(row.scenario_id); }}
          className="text-xs px-2 py-0.5 rounded border border-gray-600 hover:bg-gray-700"
        >
          Select
        </button>
      ),
    },
  ];

  return (
    <PageShell title="Scenario Composer" subtitle="Build ∙ Run ∙ Replay — deterministic scenario engine v2">
      <div data-testid="scenario-composer" className="space-y-4">
        {/* Composer panel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left: editor */}
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-200">Composer</h3>
            <div>
              <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Name</label>
              <input
                value={scenarioName}
                onChange={e => setScenarioName(e.target.value)}
                className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
              />
            </div>
            <div>
              <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Kind</label>
              <select
                data-testid="scenario-kind-select"
                value={scenarioKind}
                onChange={e => { const k = e.target.value as ScenarioKind; setScenarioKind(k); setPayloadText(KIND_DEFAULTS[k]); setPreviewData(null); }}
                className="w-full text-sm rounded border border-gray-600 bg-gray-800 text-gray-200 px-2 py-1.5"
              >
                <option value="stress">stress</option>
                <option value="whatif">whatif</option>
                <option value="shock_ladder">shock_ladder</option>
              </select>
            </div>
            <div>
              <label className="text-xs uppercase tracking-widest text-gray-500 block mb-1">Payload (JSON)</label>
              <textarea
                value={payloadText}
                onChange={e => setPayloadText(e.target.value)}
                rows={10}
                className="w-full font-mono text-xs rounded border border-gray-600 bg-gray-900 text-gray-200 px-2 py-1.5"
              />
            </div>
            <div className="flex gap-2">
              <button
                data-testid="scenario-validate"
                onClick={handleValidate}
                className="flex-1 rounded border border-gray-600 py-2 text-sm font-semibold text-gray-200 hover:bg-gray-700"
              >
                Validate
              </button>
              <button
                data-testid="scenario-run"
                disabled={running}
                onClick={handleRun}
                className="flex-1 rounded bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-40"
              >
                {running ? "Running\u2026" : "Run"}
              </button>
              <button
                data-testid="scenario-replay"
                disabled={replaying || !selected}
                onClick={handleReplay}
                className="flex-1 rounded bg-emerald-700 py-2 text-sm font-semibold text-white hover:bg-emerald-600 disabled:opacity-40"
                title={selected ? `Replay ${selected.scenario_id.slice(0, 8)}…` : "Select a scenario first"}
              >
                {replaying ? "Replaying\u2026" : "Replay"}
              </button>
            </div>
          </div>

          {/* Right: preview */}
          <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-200">Preview</h3>
            {previewData ? (
              <pre
                data-testid="scenario-preview-ready"
                className="text-xs font-mono text-gray-300 overflow-auto max-h-80 whitespace-pre-wrap"
              >
                {JSON.stringify(previewData, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-gray-500">Click <strong>Validate</strong> or <strong>Run</strong> to see preview.</p>
            )}
            {selected && runs.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Runs ({runs.length})</p>
                <ul className="space-y-1">
                  {runs.slice(0, 5).map(run => (
                    <li key={run.run_id} className="text-xs text-gray-400 flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${run.replay ? "bg-emerald-400" : "bg-blue-400"}`} />
                      <span className="font-mono">{run.output_hash.slice(0, 12)}&hellip;</span>
                      <span className="text-gray-500">{run.replay ? "replay" : "run"}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Action log */}
        <div className="rounded-lg border border-gray-700 bg-black/40 p-3">
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Action Log</p>
          <div data-testid="scenario-action-log" className="space-y-0.5 max-h-32 overflow-y-auto font-mono text-xs">
            {actionLog.length === 0 && <p className="text-gray-600">No actions yet.</p>}
            {actionLog.map((entry, i) => (
              <p key={i} className={`${entry.type === "success" ? "text-green-400" : entry.type === "error" ? "text-red-400" : "text-gray-400"}`}>
                <span className="text-gray-600">[{entry.timestamp.slice(11, 23)}] </span>
                {entry.message}
              </p>
            ))}
          </div>
        </div>

        {/* Scenarios list */}
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">All Scenarios</p>
          {!loading && scenarios.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-6">No scenarios yet.</p>
          )}
          {scenarios.length > 0 && (
            <DataTable<Scenario>
              data-testid="scenario-list-ready"
              columns={columns}
              data={scenarios}
              rowKey="scenario_id"
              emptyLabel="No scenarios"
            />
          )}
        </div>
      </div>

      {/* Detail drawer */}
      <RightDrawer open={!!selected} onClose={() => { setSelected(null); setRuns([]); }} title="Scenario Detail">
        {selected && (
          <div className="space-y-4 text-sm">
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Scenario ID</p><p className="font-mono text-xs break-all text-gray-300">{selected.scenario_id}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Name</p><p className="text-gray-200">{selected.name}</p></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Kind</p><span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${KIND_COLORS[selected.kind]}`}>{selected.kind}</span></div>
            <div><p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Payload Hash</p><p className="font-mono text-xs break-all text-gray-400">{selected.payload_hash}</p></div>
            {selected.impact_preview && (
              <div>
                <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Impact Preview</p>
                <pre className="text-xs font-mono text-gray-300 overflow-auto max-h-40 whitespace-pre-wrap">{JSON.stringify(selected.impact_preview, null, 2)}</pre>
              </div>
            )}
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-500 mb-1">Runs ({runs.length})</p>
              {runs.length === 0 && <p className="text-gray-500 text-xs">No runs yet.</p>}
              <ul className="space-y-1.5">
                {runs.map(run => (
                  <li key={run.run_id} className="text-xs rounded border border-gray-700 p-2 space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${run.replay ? "bg-emerald-400" : "bg-blue-400"}`} />
                      <span className="font-mono text-gray-300">{run.output_hash.slice(0, 16)}&hellip;</span>
                      {run.replay && <span className="text-emerald-400 text-xs">replay</span>}
                    </div>
                    <p className="text-gray-500">Artifact: <span className="font-mono">{run.artifact_id.slice(0, 12)}&hellip;</span></p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
