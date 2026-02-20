/**
 * RunbooksPage.tsx (v5.56.0 — Wave 67)
 * Route: /runbooks
 *
 * Agent Runbooks v1 — create, inspect, and execute deterministic agent workflows.
 *
 * data-testids:
 *   runbooks-page, runbooks-ready, runbook-row-{i}, runbook-create-btn,
 *   runbook-step-add-{type}, runbook-execute-btn, runbook-progress-ready,
 *   runbook-drawer, runbook-name-input, runbook-steps-list,
 *   runbook-result-hash, runbook-step-result-{i}
 */
import { useState, useEffect, useCallback } from "react";
import PageShell from "@/components/ui/PageShell";
import RightDrawer from "@/components/ui/RightDrawer";
import { useToast } from "@/components/ui/ToastCenter";

const API = (path: string) => `/api${path}`;

const STEP_TYPES = [
  "validate_dataset",
  "validate_scenario",
  "execute_run",
  "request_review",
  "export_packet",
  "generate_compliance_pack",
] as const;
type StepType = typeof STEP_TYPES[number];

interface RunbookStep {
  step_type: StepType;
  label: string;
  params: Record<string, string>;
}

interface Runbook {
  runbook_id: string;
  name: string;
  description: string;
  tenant_id: string;
  steps: RunbookStep[];
  step_count: number;
  created_at: string;
  updated_at: string;
}

interface StepResult {
  step_index: number;
  step_type: string;
  label: string;
  status: string;
  artifact_hash?: string;
  output?: Record<string, unknown>;
  attestation_id?: string;
  timestamp: string;
}

interface ExecuteResult {
  runbook_id: string;
  execution_id: string;
  status: string;
  step_count: number;
  completed_steps: number;
  step_results: StepResult[];
  run_hash: string;
  completed_at: string;
}

const STEP_LABELS: Record<StepType, string> = {
  validate_dataset:         "Validate Dataset",
  validate_scenario:        "Validate Scenario",
  execute_run:              "Execute Run",
  request_review:           "Request Review",
  export_packet:            "Export Packet",
  generate_compliance_pack: "Generate Compliance Pack",
};

const STEP_COLORS: Record<StepType, string> = {
  validate_dataset:         "text-blue-300",
  validate_scenario:        "text-purple-300",
  execute_run:              "text-green-300",
  request_review:           "text-pink-300",
  export_packet:            "text-orange-300",
  generate_compliance_pack: "text-teal-300",
};

const STATUS_ICONS: Record<string, string> = {
  COMPLETED: "✅",
  FAILED:    "❌",
  RUNNING:   "⏳",
  PENDING:   "⏸",
};

export default function RunbooksPage() {
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedRunbook, setSelectedRunbook] = useState<Runbook | null>(null);
  const [execResult, setExecResult] = useState<ExecuteResult | null>(null);
  const [executing, setExecuting] = useState(false);

  // Create form
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newSteps, setNewSteps] = useState<RunbookStep[]>([]);

  const { addToast } = useToast();
  const toast = (opts: { title: string; description?: string; variant?: string }) =>
    addToast(opts.description ? `${opts.title}: ${opts.description}` : opts.title,
      opts.variant === "destructive" ? "error" : opts.variant === "success" ? "success" : "info");

  const loadRunbooks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API("/runbooks"));
      if (!res.ok) throw new Error("Failed to load runbooks");
      const data = await res.json();
      setRunbooks(data.runbooks ?? []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRunbooks(); }, [loadRunbooks]);

  // ESC closes drawer
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedRunbook(null);
        setExecResult(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const execute = async () => {
    if (!selectedRunbook) return;
    setExecuting(true);
    setExecResult(null);
    try {
      const res = await fetch(API(`/runbooks/${selectedRunbook.runbook_id}/execute`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_id: "default" }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Execution failed");
      }
      const data = await res.json();
      // API returns { execution: {...}, status: "completed" } — extract execution
      const exec = data.execution ?? data;
      const result: ExecuteResult = {
        ...exec,
        execution_id: exec.execution_id ?? "",
        step_count: exec.step_results?.length ?? 0,
        completed_steps: (exec.step_results ?? []).filter((s: { status: string }) => s.status === "completed").length,
        run_hash: exec.outputs_hash ?? exec.run_hash ?? "",
        status: (exec.status ?? "completed").toUpperCase(),
        completed_at: exec.executed_at ?? exec.completed_at ?? "",
      };
      setExecResult(result);
      toast({ title: "Runbook executed", description: `run_hash: ${result.run_hash.slice(0, 12)}`, variant: "success" });
    } catch (e) {
      toast({ title: "Execute failed", description: String(e), variant: "destructive" });
    } finally {
      setExecuting(false);
    }
  };

  const addStep = (type: StepType) => {
    setNewSteps(prev => [...prev, { step_type: type, label: STEP_LABELS[type], params: {} }]);
  };

  const createRunbook = async () => {
    if (!newName.trim()) return;
    try {
      const res = await fetch(API("/runbooks"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim(), description: newDesc.trim(), steps: newSteps }),
      });
      if (!res.ok) throw new Error("Create failed");
      toast({ title: "Runbook created", variant: "success" });
      setCreating(false);
      setNewName(""); setNewDesc(""); setNewSteps([]);
      await loadRunbooks();
    } catch (e) {
      toast({ title: "Create failed", description: String(e), variant: "destructive" });
    }
  };

  return (
    <PageShell
      title="Agent Runbooks"
      subtitle="Wave 67 — v5.56.0"
      actions={
        <>
          <button
            onClick={loadRunbooks}
            className="px-3 py-1.5 text-xs rounded bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition"
            data-testid="runbooks-refresh-btn"
          >
            Refresh
          </button>
          <button
            onClick={() => setCreating(true)}
            className="px-3 py-1.5 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90 transition"
            data-testid="runbook-create-btn"
          >
            + New Runbook
          </button>
        </>
      }
    >
      <div className="space-y-4" data-testid="runbooks-page">
        {loading && (
          <div className="text-sm text-muted-foreground animate-pulse" data-testid="runbooks-loading">
            Loading runbooks…
          </div>
        )}
        {error && (
          <div className="rounded border border-red-700/50 bg-red-900/20 p-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Create form */}
        {creating && (
          <div className="rounded border border-border bg-card p-4 space-y-3" data-testid="runbook-create-form">
            <h3 className="text-sm font-semibold">New Runbook</h3>
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="Runbook name…"
              className="w-full text-sm bg-background border border-border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              data-testid="runbook-name-input"
              autoFocus
            />
            <input
              value={newDesc}
              onChange={e => setNewDesc(e.target.value)}
              placeholder="Description (optional)…"
              className="w-full text-sm bg-background border border-border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
              data-testid="runbook-desc-input"
            />

            <div>
              <p className="text-xs text-muted-foreground mb-2">Add steps:</p>
              <div className="flex flex-wrap gap-1">
                {STEP_TYPES.map(type => (
                  <button
                    key={type}
                    onClick={() => addStep(type)}
                    className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/70 border border-border transition"
                    data-testid={`runbook-step-add-${type}`}
                  >
                    + {STEP_LABELS[type]}
                  </button>
                ))}
              </div>
            </div>

            {newSteps.length > 0 && (
              <div className="space-y-1" data-testid="runbook-steps-list">
                {newSteps.map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-xs px-2 py-1 rounded bg-muted/30 border border-border/30"
                    data-testid={`runbook-new-step-${i}`}
                  >
                    <span className="text-muted-foreground font-mono">{i + 1}.</span>
                    <span className={STEP_COLORS[step.step_type]}>{step.label}</span>
                    <button
                      onClick={() => setNewSteps(prev => prev.filter((_, j) => j !== i))}
                      className="ml-auto text-muted-foreground hover:text-destructive"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={createRunbook}
                disabled={!newName.trim()}
                className="px-3 py-1.5 text-xs rounded bg-primary text-primary-foreground hover:bg-primary/90 transition disabled:opacity-40"
                data-testid="runbook-create-confirm-btn"
              >
                Create
              </button>
              <button
                onClick={() => { setCreating(false); setNewName(""); setNewDesc(""); setNewSteps([]); }}
                className="px-3 py-1.5 text-xs rounded bg-muted text-muted-foreground hover:bg-muted/70 transition"
                data-testid="runbook-create-cancel-btn"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Runbooks table */}
        {!loading && runbooks.length === 0 && (
          <div className="text-sm text-muted-foreground text-center py-12" data-testid="runbooks-empty">
            No runbooks yet. Create your first agent runbook.
          </div>
        )}

        {runbooks.length > 0 && (
          <div className="rounded border border-border bg-card overflow-hidden" data-testid="runbooks-ready">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-xs text-muted-foreground">
                  <th className="text-left px-4 py-2">Runbook</th>
                  <th className="text-left px-4 py-2">Steps</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-left px-4 py-2">Updated</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {runbooks.map((rb, i) => (
                  <tr
                    key={rb.runbook_id}
                    className="hover:bg-muted/20 transition cursor-pointer"
                    onClick={() => { setSelectedRunbook(rb); setExecResult(null); }}
                    data-testid={`runbook-row-${i}`}
                    tabIndex={0}
                    role="button"
                    onKeyDown={e => e.key === "Enter" && (() => { setSelectedRunbook(rb); setExecResult(null); })()}
                  >
                    <td className="px-4 py-2">
                      <div className="font-medium">{rb.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">{rb.runbook_id}</div>
                    </td>
                    <td className="px-4 py-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                        {rb.step_count} steps
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-xs truncate">
                      {rb.description}
                    </td>
                    <td className="px-4 py-2 text-xs text-muted-foreground font-mono">
                      {(rb.updated_at ?? rb.created_at)?.slice(0, 16) ?? "—"}
                    </td>
                    <td className="px-4 py-2">
                      <button
                        onClick={e => { e.stopPropagation(); setSelectedRunbook(rb); setExecResult(null); }}
                        className="text-xs text-primary hover:underline"
                        data-testid={`runbook-open-${rb.runbook_id}`}
                      >
                        Open →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Runbook Detail Drawer */}
      <RightDrawer
        open={selectedRunbook !== null}
        onClose={() => { setSelectedRunbook(null); setExecResult(null); }}
        title={selectedRunbook?.name ?? "Runbook"}
        headerActions={
          selectedRunbook && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
              {selectedRunbook.step_count} steps
            </span>
          )
        }
      >
        {selectedRunbook && (
          <div className="space-y-5 p-4" data-testid="runbook-drawer">
            {/* Meta */}
            <div>
              <span className="text-xs text-muted-foreground">ID</span>
              <p className="text-sm font-mono mt-0.5">{selectedRunbook.runbook_id}</p>
              {selectedRunbook.description && (
                <p className="text-sm text-muted-foreground mt-1">{selectedRunbook.description}</p>
              )}
            </div>

            {/* Steps list */}
            <div>
              <h3 className="text-sm font-semibold mb-2">
                Steps ({selectedRunbook.steps.length})
              </h3>
              <div className="space-y-1" data-testid="runbook-steps-list">
                {selectedRunbook.steps.map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-xs px-3 py-2 rounded bg-muted/20 border border-border/30"
                    data-testid={`runbook-step-${i}`}
                  >
                    <span className="text-muted-foreground font-mono w-5 text-center">{i + 1}</span>
                    <span className={STEP_COLORS[step.step_type]}>{step.label}</span>
                    <span className="text-muted-foreground ml-auto font-mono text-xs">
                      {step.step_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Execute action */}
            <div>
              <h3 className="text-sm font-semibold mb-2">Execute</h3>
              <button
                onClick={execute}
                disabled={executing}
                className="px-4 py-2 text-xs rounded bg-green-700/50 text-green-200 hover:bg-green-700/80 border border-green-700/50 transition disabled:opacity-40 flex items-center gap-2"
                data-testid="runbook-execute-btn"
              >
                {executing ? (
                  <>
                    <span className="inline-block h-3 w-3 rounded-full border-2 border-green-300/30 border-t-green-300 animate-spin" />
                    Executing…
                  </>
                ) : (
                  "▶ Execute Runbook"
                )}
              </button>
            </div>

            {/* Execution result */}
            {execResult && (
              <div className="space-y-3" data-testid="runbook-progress-ready">
                <div className="rounded border border-border bg-card p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold">Execution Result</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${execResult.status === "COMPLETED" ? "bg-green-900/40 text-green-300 border-green-700/40" : "bg-red-900/40 text-red-300 border-red-700/40"}`}>
                      {execResult.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div>
                      <span className="text-muted-foreground">Execution ID</span>
                      <p className="font-mono">{execResult.execution_id}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Steps</span>
                      <p>{execResult.completed_steps}/{execResult.step_count}</p>
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground">Run Hash</span>
                    <p className="text-xs font-mono break-all mt-0.5" data-testid="runbook-result-hash">
                      {execResult.run_hash}
                    </p>
                  </div>
                </div>

                {/* Step results */}
                <div className="space-y-1">
                  {(execResult.step_results ?? []).map((sr, i) => (
                    <div
                      key={i}
                      className="text-xs px-3 py-2 rounded bg-muted/20 border border-border/30"
                      data-testid={`runbook-step-result-${i}`}
                    >
                      <div className="flex items-center gap-2">
                        <span>{STATUS_ICONS[sr.status] ?? "•"}</span>
                        <span className={`${STEP_COLORS[sr.step_type as StepType] ?? "text-foreground"}`}>
                          {sr.label}
                        </span>
                        <span className="text-muted-foreground ml-auto">{sr.status}</span>
                      </div>
                      {sr.artifact_hash && (
                        <p className="text-muted-foreground font-mono mt-0.5">
                          hash: {sr.artifact_hash.slice(0, 16)}…
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </RightDrawer>
    </PageShell>
  );
}
