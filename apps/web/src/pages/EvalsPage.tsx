/**
 * EvalsPage.tsx (v5.57.0 — Depth Wave)
 * Route: /evals
 *
 * Evaluation Harness v3: calibration, drift, stability metrics.
 *
 * data-testids:
 *   evals-page, evals-tab, evals-table-ready, eval-row-{i},
 *   eval-run-btn, eval-metric-calibration, eval-metric-drift,
 *   eval-metric-stability, eval-drawer, eval-passed-badge,
 *   eval-detail-run-count
 */
import { useState, useCallback } from "react";
import PageShell from "@/components/ui/PageShell";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

interface Eval {
  eval_id: string;
  run_ids: string[];
  run_count: number;
  metrics: {
    calibration_error: number;
    drift_score: number;
    stability_score: number;
  };
  passed: boolean;
  evaluated_at: string;
  harness_version: string;
}

const METRIC_COLORS = {
  good: "text-green-400",
  warn: "text-yellow-400",
  bad:  "text-red-400",
};

function metricColor(key: "calibration_error" | "drift_score" | "stability_score", val: number): string {
  if (key === "calibration_error") return val <= 0.03 ? METRIC_COLORS.good : val <= 0.05 ? METRIC_COLORS.warn : METRIC_COLORS.bad;
  if (key === "drift_score")       return val <= 0.08 ? METRIC_COLORS.good : val <= 0.15 ? METRIC_COLORS.warn : METRIC_COLORS.bad;
  if (key === "stability_score")   return val >= 0.97 ? METRIC_COLORS.good : val >= 0.90 ? METRIC_COLORS.warn : METRIC_COLORS.bad;
  return METRIC_COLORS.warn;
}

// Demo run IDs used for quick eval creation
const DEMO_RUN_IDS = [
  "demo-run-0001",
  "demo-run-0002",
];

export default function EvalsPage() {
  const { addToast } = useToast();
  const [evals, setEvals] = useState<Eval[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Eval | null>(null);
  const [creating, setCreating] = useState(false);
  const [customRunIds, setCustomRunIds] = useState("");

  const loadEvals = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(API("/eval/v3"));
      if (!r.ok) throw new Error(`${r.status}`);
      const d = await r.json();
      setEvals(d.evals ?? []);
    } catch (e) {
      addToast(`Failed to load evals: ${e}`);
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const createEval = useCallback(async () => {
    setCreating(true);
    try {
      // Use custom run IDs if provided, else use demo IDs + first from scenario runs if available
      let runIds = customRunIds.trim()
        ? customRunIds.split(",").map(s => s.trim()).filter(Boolean)
        : DEMO_RUN_IDS;

      // Try to get real run IDs from scenario runs
      try {
        const sr = await fetch(API("/scenarios-v2?limit=5"));
        if (sr.ok) {
          const sd = await sr.json();
          const scenarios = sd.scenarios ?? [];
          for (const sc of scenarios.slice(0, 2)) {
            const rr = await fetch(API(`/scenarios-v2/${sc.scenario_id}/runs`));
            if (rr.ok) {
              const rd = await rr.json();
              const runs = rd.runs ?? [];
              if (runs.length > 0) runIds = [...new Set([...runIds, ...runs.slice(0, 2).map((r: any) => r.run_id)])];
            }
          }
        }
      } catch { /* use defaults */ }

      const r = await fetch(API("/eval/v3/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_ids: runIds }),
      });
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
      const data = await r.json();
      const ev = data.eval;
      setEvals(prev => {
        const exists = prev.find(e => e.eval_id === ev.eval_id);
        return exists ? prev : [ev, ...prev];
      });
      setSelected(ev);
      addToast("Eval created");
    } catch (e) {
      addToast(`Eval failed: ${e}`);
    } finally {
      setCreating(false);
    }
  }, [customRunIds, addToast]);

  // Load on mount
  useState(() => { loadEvals(); });

  return (
    <PageShell title="Evaluation Harness v3">
      <div data-testid="evals-page" className="p-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-white">Evaluation Harness v3</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Calibration · Drift · Stability — deterministic metrics for every run set
            </p>
          </div>
          <div className="flex gap-2">
            <button
              data-testid="evals-refresh-btn"
              onClick={loadEvals}
              disabled={loading}
              className="px-3 py-1.5 rounded border border-border text-sm text-muted-foreground hover:bg-muted disabled:opacity-50"
            >
              {loading ? "Loading…" : "Refresh"}
            </button>
            <button
              data-testid="eval-run-btn"
              onClick={createEval}
              disabled={creating}
              className="px-4 py-1.5 rounded bg-primary/80 hover:bg-primary text-white text-sm font-medium disabled:opacity-50"
            >
              {creating ? "Running…" : "Run Eval"}
            </button>
          </div>
        </div>

        {/* Custom run IDs input */}
        <div className="mb-4">
          <input
            data-testid="eval-run-ids-input"
            type="text"
            value={customRunIds}
            onChange={e => setCustomRunIds(e.target.value)}
            placeholder="Optional: comma-separated run IDs (defaults to demo runs)"
            className="w-full bg-muted/30 border border-border rounded px-3 py-1.5 text-sm text-white placeholder:text-muted-foreground"
          />
        </div>

        {/* Metric legend */}
        <div className="mb-4 flex gap-4 text-xs text-muted-foreground">
          <span><span className={METRIC_COLORS.good}>■</span> Good</span>
          <span><span className={METRIC_COLORS.warn}>■</span> Warn</span>
          <span><span className={METRIC_COLORS.bad}>■</span> Bad</span>
        </div>

        {/* Table */}
        <div data-testid="evals-tab" className="rounded-lg border border-border overflow-hidden">
          {loading && evals.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">Loading…</div>
          ) : evals.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground text-sm">
              No evals yet. Click "Run Eval" to create one.
            </div>
          ) : (
            <table data-testid="evals-table-ready" className="w-full text-sm">
              <thead className="bg-muted/20 text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Eval ID</th>
                  <th className="px-4 py-2 text-right font-medium">Runs</th>
                  <th className="px-4 py-2 text-right font-medium">Calibration ↓</th>
                  <th className="px-4 py-2 text-right font-medium">Drift ↓</th>
                  <th className="px-4 py-2 text-right font-medium">Stability ↑</th>
                  <th className="px-4 py-2 text-center font-medium">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {evals.map((ev, i) => (
                  <tr
                    key={ev.eval_id}
                    data-testid={`eval-row-${i}`}
                    className="hover:bg-muted/10 cursor-pointer transition-colors"
                    onClick={() => setSelected(ev)}
                  >
                    <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                      {ev.eval_id.slice(0, 28)}…
                    </td>
                    <td className="px-4 py-2 text-right text-white">{ev.run_count}</td>
                    <td className={`px-4 py-2 text-right font-mono ${metricColor("calibration_error", ev.metrics.calibration_error)}`}>
                      {ev.metrics.calibration_error.toFixed(4)}
                    </td>
                    <td className={`px-4 py-2 text-right font-mono ${metricColor("drift_score", ev.metrics.drift_score)}`}>
                      {ev.metrics.drift_score.toFixed(4)}
                    </td>
                    <td className={`px-4 py-2 text-right font-mono ${metricColor("stability_score", ev.metrics.stability_score)}`}>
                      {ev.metrics.stability_score.toFixed(4)}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ev.passed ? "bg-green-900/40 text-green-300" : "bg-red-900/40 text-red-300"}`}>
                        {ev.passed ? "PASS" : "FAIL"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Detail Drawer */}
        <RightDrawer
          open={!!selected}
          onClose={() => setSelected(null)}
          title="Eval Detail"
        >
          {selected && (
            <div data-testid="eval-drawer" className="space-y-4">
              <div className="text-xs font-mono text-muted-foreground break-all">
                {selected.eval_id}
              </div>

              <div data-testid="eval-detail-run-count" className="bg-muted/20 rounded p-3">
                <div className="text-xs text-muted-foreground mb-1">Run Count</div>
                <div className="text-2xl font-bold text-white">{selected.run_count}</div>
              </div>

              <div
                data-testid="eval-passed-badge"
                className={`text-center py-2 rounded font-medium ${selected.passed ? "bg-green-900/30 text-green-300" : "bg-red-900/30 text-red-300"}`}
              >
                {selected.passed ? "✓ ALL THRESHOLDS MET" : "✗ THRESHOLD VIOLATED"}
              </div>

              <div className="space-y-2">
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Metrics</div>

                <div className="bg-muted/20 rounded p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Calibration Error</div>
                      <div className="text-xs text-muted-foreground/60">↓ lower is better · max 0.05</div>
                    </div>
                    <div data-testid="eval-metric-calibration" className={`text-lg font-mono font-bold ${metricColor("calibration_error", selected.metrics.calibration_error)}`}>
                      {selected.metrics.calibration_error.toFixed(6)}
                    </div>
                  </div>
                </div>

                <div className="bg-muted/20 rounded p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Drift Score</div>
                      <div className="text-xs text-muted-foreground/60">↓ lower is better · max 0.20</div>
                    </div>
                    <div data-testid="eval-metric-drift" className={`text-lg font-mono font-bold ${metricColor("drift_score", selected.metrics.drift_score)}`}>
                      {selected.metrics.drift_score.toFixed(6)}
                    </div>
                  </div>
                </div>

                <div className="bg-muted/20 rounded p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Stability Score</div>
                      <div className="text-xs text-muted-foreground/60">↑ higher is better · min 0.90</div>
                    </div>
                    <div data-testid="eval-metric-stability" className={`text-lg font-mono font-bold ${metricColor("stability_score", selected.metrics.stability_score)}`}>
                      {selected.metrics.stability_score.toFixed(6)}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide">Run IDs</div>
                {selected.run_ids.map((rid, i) => (
                  <div key={i} className="text-xs font-mono text-muted-foreground bg-muted/20 rounded px-2 py-1">
                    {rid}
                  </div>
                ))}
              </div>

              <div className="text-xs text-muted-foreground">
                Harness: {selected.harness_version} · {selected.evaluated_at}
              </div>
            </div>
          )}
        </RightDrawer>
      </div>
    </PageShell>
  );
}
