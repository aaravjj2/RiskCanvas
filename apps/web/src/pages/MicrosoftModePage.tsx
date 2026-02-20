import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useState, useEffect } from "react";
import { CheckCircle, XCircle, Loader2, ChevronRight, ChevronLeft, Bot, Wrench, Shield, Play, Hash } from "lucide-react";

// v5.59.0 MCP v2 types
interface McpV2Step {
  step: number;
  tool: string;
  description: string;
  status: "pending" | "running" | "done" | "error";
  result_hash?: string;
  result?: any;
}

const MCP_V2_PLAN: McpV2Step[] = [
  { step: 1, tool: "ingest_dataset",  description: "Ingest portfolio dataset (AAPL/MSFT)", status: "pending" },
  { step: 2, tool: "create_scenario", description: "Create stress scenario (equity shock)",  status: "pending" },
  { step: 3, tool: "execute_run",     description: "Execute scenario run, get output_hash",  status: "pending" },
  { step: 4, tool: "replay_run",      description: "Replay run, verify hash matches",         status: "pending" },
  { step: 5, tool: "request_review",  description: "Open review in DRAFT state",             status: "pending" },
  { step: 6, tool: "approve_review",  description: "Approve review (submit + decide)",        status: "pending" },
  { step: 7, tool: "export_packet",   description: "Export decision packet w/ manifest_hash", status: "pending" },
  { step: 8, tool: "run_eval",        description: "Run calibration/drift/stability eval",    status: "pending" },
];

interface MCPTool {
  name: string;
  description: string;
  input_schema: any;
}

interface ProviderInfo {
  mode: "mock" | "foundry";
  connected: boolean;
}

interface AuditEntry {
  step: number;
  from_agent: string;
  to_agent: string;
  input_hash: string;
  output_hash: string;
  timestamp: string;
}

interface SRECheck {
  name: string;
  passed: boolean;
  detail: string;
}

interface AgentPlanStep {
  agent: string;
  description: string;
  status: string;
}

interface AgentRunResult {
  run_id: string;
  status: string;
  decision: string;
  portfolio_name: string;
  total_value: number;
  total_pnl: number;
  summary: string;
  recommendations: string[];
  audit_log: AuditEntry[];
  sre_checks: SRECheck[];
  model_used: string;
  timestamp: string;
}

const API = "http://localhost:8090";

const WIZARD_STEPS = ["Provider Status", "MCP Tools", "Multi-Agent Run"];

const DEMO_PORTFOLIO = {
  positions: [
    { symbol: "AAPL", qty: 100, price: 150.0, asset_class: "equity" },
    { symbol: "MSFT", qty: 50, price: 300.0, asset_class: "equity" },
    { symbol: "GOOGL", qty: 25, price: 2800.0, asset_class: "equity" },
  ],
};

export default function MicrosoftModePage() {
  const [step, setStep] = useState(0);

  // v5.59.0 MCP v2 state
  const [mcpV2Steps, setMcpV2Steps] = useState<McpV2Step[]>(MCP_V2_PLAN.map(s => ({ ...s })));
  const [mcpV2Running, setMcpV2Running] = useState(false);
  const [mcpV2AuditLog, setMcpV2AuditLog] = useState<any[]>([]);
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [reviewId,  setReviewId]  = useState<string | null>(null);
  const [runId,     setRunId]     = useState<string | null>(null);

  // Step 1 state
  const [providerInfo, setProviderInfo] = useState<ProviderInfo>({ mode: "mock", connected: false });
  const [providerLoading, setProviderLoading] = useState(true);

  // Step 2 state
  const [mcpTools, setMcpTools] = useState<MCPTool[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testRunning, setTestRunning] = useState(false);

  // Step 3 state
  const [agentPlan, setAgentPlan] = useState<AgentPlanStep[]>([]);
  const [agentResult, setAgentResult] = useState<AgentRunResult | null>(null);
  const [agentRunning, setAgentRunning] = useState(false);

  useEffect(() => {
    loadProvider();
  }, []);

  const loadProvider = async () => {
    try {
      const res = await fetch(`${API}/mcp/health`);
      if (res.ok) {
        const h = await res.json();
        setProviderInfo({ mode: h.mode ?? "mock", connected: h.status === "healthy" });
      }
    } catch {
      setProviderInfo({ mode: "mock", connected: false });
    } finally {
      setProviderLoading(false);
    }
  };

  const loadTools = async () => {
    setToolsLoading(true);
    try {
      const res = await fetch(`${API}/mcp/tools`);
      if (res.ok) setMcpTools(await res.json());
    } catch {/**/} finally {
      setToolsLoading(false);
    }
  };

  const loadPlan = async () => {
    try {
      const res = await fetch(`${API}/orchestrator/plan`);
      if (res.ok) {
        const plan = await res.json();
        setAgentPlan(plan.steps ?? []);
      }
    } catch {/**/}
  };

  const runMcpV2Plan = async () => {
    setMcpV2Running(true);
    setMcpV2AuditLog([]);
    const steps = MCP_V2_PLAN.map(s => ({ ...s }));
    setMcpV2Steps(steps);

    let _scenarioId = scenarioId;
    let _subjectId  = subjectId;
    let _reviewId   = reviewId;
    let _runId      = runId;

    const callTool = async (tool: string, params: any) => {
      const res = await fetch("/api/mcp/v2/tools/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool, params }),
      });
      if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
      return res.json();
    };

    const updateStep = (idx: number, update: Partial<McpV2Step>) => {
      setMcpV2Steps(prev => {
        const next = [...prev];
        next[idx] = { ...next[idx], ...update };
        return next;
      });
    };

    try {
      // Step 1: ingest
      updateStep(0, { status: "running" });
      const r1 = await callTool("ingest_dataset", { name: "MS Mode Dataset", kind: "portfolio", created_by: "ms@demo" });
      _subjectId = r1.result?.dataset?.dataset_id;
      setSubjectId(_subjectId);
      updateStep(0, { status: "done", result_hash: r1.audit_entry?.result_hash, result: r1.result });
      setMcpV2AuditLog(prev => [...prev, r1.audit_entry]);

      // Step 2: create scenario
      updateStep(1, { status: "running" });
      const r2 = await callTool("create_scenario", { name: "MS Stress", kind: "stress", created_by: "ms@demo" });
      _scenarioId = r2.result?.scenario?.scenario_id;
      setScenarioId(_scenarioId);
      updateStep(1, { status: "done", result_hash: r2.audit_entry?.result_hash, result: r2.result });
      setMcpV2AuditLog(prev => [...prev, r2.audit_entry]);

      // Step 3: execute run
      updateStep(2, { status: "running" });
      const r3 = await callTool("execute_run", { scenario_id: _scenarioId, triggered_by: "ms@demo" });
      _runId = r3.result?.run?.run_id;
      setRunId(_runId);
      updateStep(2, { status: "done", result_hash: r3.audit_entry?.result_hash, result: r3.result });
      setMcpV2AuditLog(prev => [...prev, r3.audit_entry]);

      // Step 4: replay run
      updateStep(3, { status: "running" });
      const r4 = await callTool("replay_run", { scenario_id: _scenarioId, triggered_by: "ms@demo" });
      updateStep(3, { status: "done", result_hash: r4.audit_entry?.result_hash, result: r4.result });
      setMcpV2AuditLog(prev => [...prev, r4.audit_entry]);

      // Step 5: request review
      updateStep(4, { status: "running" });
      const r5 = await callTool("request_review", { subject_type: "dataset", subject_id: _subjectId ?? "demo-ds", created_by: "ms@demo", notes: "MS Mode review" });
      _reviewId = r5.result?.review?.review_id;
      setReviewId(_reviewId);
      updateStep(4, { status: "done", result_hash: r5.audit_entry?.result_hash, result: r5.result });
      setMcpV2AuditLog(prev => [...prev, r5.audit_entry]);

      // Step 6: approve review
      updateStep(5, { status: "running" });
      const r6 = await callTool("approve_review", { review_id: _reviewId, submitted_by: "ms@demo", decided_by: "ms@demo", decision: "APPROVE", rationale: "MS auto-approval" });
      updateStep(5, { status: "done", result_hash: r6.audit_entry?.result_hash, result: r6.result });
      setMcpV2AuditLog(prev => [...prev, r6.audit_entry]);

      // Step 7: export packet
      updateStep(6, { status: "running" });
      const r7 = await callTool("export_packet", { subject_type: "dataset", subject_id: _subjectId ?? "demo-ds", requested_by: "ms@demo" });
      updateStep(6, { status: "done", result_hash: r7.audit_entry?.result_hash, result: r7.result });
      setMcpV2AuditLog(prev => [...prev, r7.audit_entry]);

      // Step 8: run eval
      updateStep(7, { status: "running" });
      const r8 = await callTool("run_eval", { run_ids: [_runId ?? "demo-run"] });
      updateStep(7, { status: "done", result_hash: r8.audit_entry?.result_hash, result: r8.result });
      setMcpV2AuditLog(prev => [...prev, r8.audit_entry]);

    } catch (e) {
      const failIdx = mcpV2Steps.findIndex(s => s.status === "running");
      if (failIdx >= 0) updateStep(failIdx, { status: "error" });
    } finally {
      setMcpV2Running(false);
    }
  };

  const goNext = async () => {
    if (step === 0) await loadTools();
    else if (step === 1) await loadPlan();
    setStep(s => s + 1);
  };

  const goBack = () => setStep(s => s - 1);

  const runTestCall = async () => {
    setTestResult(null);
    setTestRunning(true);
    try {
      const res = await fetch(`${API}/mcp/tools/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-demo-user": "demo-user", "x-demo-role": "admin" },
        body: JSON.stringify({
          tool_name: "portfolio_analyze",
          arguments: { portfolio: [{ symbol: "AAPL", quantity: 10, price: 150.0 }], var_method: "parametric" },
        }),
      });
      if (res.ok) {
        const r = await res.json();
        setTestResult(r.success ? "SUCCESS" : `FAILED: ${r.error}`);
      } else {
        setTestResult(`HTTP ${res.status}`);
      }
    } catch (e) {
      setTestResult(`ERROR: ${e}`);
    } finally {
      setTestRunning(false);
    }
  };

  const runAgentPipeline = async () => {
    setAgentRunning(true);
    setAgentResult(null);
    try {
      const res = await fetch(`${API}/orchestrator/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ portfolio: DEMO_PORTFOLIO }),
      });
      if (res.ok) setAgentResult(await res.json());
    } catch {/**/} finally {
      setAgentRunning(false);
    }
  };

  return (
    <div data-testid="microsoft-mode-page" className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Microsoft Mode</h1>
        <p className="text-muted-foreground">Azure AI Foundry + Multi-Agent Framework</p>
      </div>

      {/* Stepper */}
      <div className="flex items-center gap-2">
        {WIZARD_STEPS.map((label, i) => (
          <div key={i} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                i === step
                  ? "bg-primary text-primary-foreground"
                  : i < step
                  ? "bg-green-500 text-white"
                  : "bg-muted text-muted-foreground"
              }`}
              data-testid={`wizard-step-indicator-${i}`}
            >
              {i < step ? <CheckCircle className="h-3 w-3" /> : <span>{i + 1}</span>}
              {label}
            </div>
            {i < WIZARD_STEPS.length - 1 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Provider Status */}
      {step === 0 && (
        <div data-testid="wizard-step-1" className="space-y-4">
          <Card data-testid="provider-status-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" /> Provider Status
              </CardTitle>
              <CardDescription>LLM / Azure AI Foundry connection check</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {providerLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <>
                  <div className="flex items-center gap-3">
                    {providerInfo.connected ? (
                      <CheckCircle className="h-6 w-6 text-green-500" />
                    ) : (
                      <XCircle className="h-6 w-6 text-yellow-500" />
                    )}
                    <div>
                      <p className="font-medium">{providerInfo.connected ? "Connected" : "Demo / Offline"}</p>
                      <p className="text-sm text-muted-foreground">Mode: {providerInfo.mode}</p>
                    </div>
                    <Badge variant={providerInfo.mode === "foundry" ? "default" : "secondary"} data-testid="provider-mode-badge">
                      {providerInfo.mode === "foundry" ? "Azure Foundry" : "Mock Provider"}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {providerInfo.mode === "foundry"
                      ? "Azure AI Foundry is active. Real inference will be used."
                      : "Running in DEMO mode - all inference is offline and deterministic."}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 2: MCP Tools */}
      {step === 1 && (
        <div data-testid="wizard-step-2" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" /> MCP Tools
              </CardTitle>
              <CardDescription>Model Context Protocol tools available</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {toolsLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <>
                  <ul data-testid="mcp-tools-list" className="space-y-2">
                    {mcpTools.map(tool => (
                      <li key={tool.name} className="border rounded-md p-3">
                        <p className="font-medium text-sm">{tool.name}</p>
                        <p className="text-xs text-muted-foreground">{tool.description}</p>
                      </li>
                    ))}
                    {mcpTools.length === 0 && (
                      <li className="text-sm text-muted-foreground">No tools loaded.</li>
                    )}
                  </ul>
                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={runTestCall}
                      disabled={testRunning}
                      data-testid="mcp-test-call-button"
                    >
                      {testRunning ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      Test portfolio_analyze
                    </Button>
                    {testResult && (
                      <Badge variant={testResult.startsWith("SUCCESS") ? "default" : "destructive"} data-testid="mcp-test-result">
                        {testResult}
                      </Badge>
                    )}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 3: Multi-Agent Run */}
      {step === 2 && (
        <div data-testid="wizard-step-3" className="space-y-4">
          {agentPlan.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Agent Execution Plan</CardTitle>
              </CardHeader>
              <CardContent>
                <ol data-testid="agent-plan-steps" className="space-y-1">
                  {agentPlan.map((s, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="w-5 h-5 rounded-full bg-muted flex items-center justify-center text-xs">{i + 1}</span>
                      <span className="font-medium">{s.agent}</span>
                      <span className="text-muted-foreground">- {s.description}</span>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}

          <Button onClick={runAgentPipeline} disabled={agentRunning} data-testid="multi-agent-run-btn">
            {agentRunning ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Bot className="h-4 w-4 mr-2" />}
            Run Multi-Agent Pipeline
          </Button>

          {agentResult && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    Result
                    <Badge>{agentResult.decision}</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p>{agentResult.summary}</p>
                  <p className="text-xs text-muted-foreground">run_id: {agentResult.run_id} | model: {agentResult.model_used}</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="text-base">Audit Log</CardTitle></CardHeader>
                <CardContent>
                  <table data-testid="audit-log-table" className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-1 pr-3">Step</th>
                        <th className="text-left py-1 pr-3">From</th>
                        <th className="text-left py-1 pr-3">To</th>
                        <th className="text-left py-1">Input Hash</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agentResult.audit_log.map(entry => (
                        <tr key={entry.step} className="border-b hover:bg-muted/30">
                          <td className="py-1 pr-3">{entry.step}</td>
                          <td className="py-1 pr-3">{entry.from_agent}</td>
                          <td className="py-1 pr-3">{entry.to_agent}</td>
                          <td className="py-1 font-mono">{entry.input_hash}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="h-4 w-4" /> SRE Checks
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul data-testid="sre-checks-list" className="space-y-1">
                    {agentResult.sre_checks.map(c => (
                      <li key={c.name} className="flex items-center gap-2 text-sm">
                        {c.passed ? <CheckCircle className="h-4 w-4 text-green-500" /> : <XCircle className="h-4 w-4 text-red-500" />}
                        <span className="font-mono text-xs">{c.name}</span>
                        <span className="text-muted-foreground">{c.detail}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* Wizard navigation */}
      <div className="flex items-center gap-3 pt-2">
        {step > 0 && (
          <Button variant="outline" onClick={goBack} data-testid="wizard-back-btn">
            <ChevronLeft className="h-4 w-4 mr-1" /> Back
          </Button>
        )}
        {step < WIZARD_STEPS.length - 1 && (
          <Button onClick={goNext} data-testid="wizard-next-btn">
            Next <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>

      {/* ── MCP v2 8-step Agent Plan (v5.59.0) ─────────────────────────── */}
      <div className="border border-border rounded-lg p-5 space-y-4 bg-card/40">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">MCP v2 Agent Runbook</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              8-step deterministic plan: ingest → run → eval → review → export
            </p>
          </div>
          <button
            data-testid="ms-run-plan"
            onClick={runMcpV2Plan}
            disabled={mcpV2Running}
            className="flex items-center gap-2 px-4 py-2 rounded bg-blue-600/80 hover:bg-blue-600 text-white text-sm font-medium disabled:opacity-50"
          >
            {mcpV2Running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {mcpV2Running ? "Running…" : "Run the 8-step agent plan"}
          </button>
        </div>

        {/* Steps grid */}
        <div className="space-y-1.5">
          {mcpV2Steps.map((s, i) => (
            <div
              key={s.step}
              data-testid={`ms-step-${i}`}
              className={`flex items-center gap-3 px-3 py-2 rounded border text-sm transition-colors ${
                s.status === "done"    ? "border-green-700/30 bg-green-900/10" :
                s.status === "running" ? "border-blue-700/30 bg-blue-900/10 animate-pulse" :
                s.status === "error"   ? "border-red-700/30 bg-red-900/10" :
                "border-border/30 bg-muted/10"
              }`}
            >
              <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold flex-shrink-0 ${
                s.status === "done"    ? "bg-green-700 text-white" :
                s.status === "running" ? "bg-blue-700 text-white" :
                s.status === "error"   ? "bg-red-700 text-white" :
                "bg-muted/50 text-muted-foreground"
              }`}>
                {s.status === "done" ? "✓" : s.status === "error" ? "✗" : s.step}
              </span>
              <span className="font-mono text-xs text-primary flex-shrink-0 w-28">{s.tool}</span>
              <span className="text-muted-foreground text-xs flex-1">{s.description}</span>
              {s.result_hash && (
                <span className="font-mono text-xs text-muted-foreground/60 flex items-center gap-1">
                  <Hash className="h-3 w-3" />{s.result_hash}
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Audit log */}
        {mcpV2AuditLog.length > 0 && (
          <div>
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Audit Log ({mcpV2AuditLog.length} entries)
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-muted-foreground border-b border-border/30">
                  <th className="text-left py-1 pr-3 font-medium">#</th>
                  <th className="text-left py-1 pr-3 font-medium">Tool</th>
                  <th className="text-left py-1 pr-3 font-medium">Params Hash</th>
                  <th className="text-left py-1 font-medium">Result Hash</th>
                </tr>
              </thead>
              <tbody>
                {mcpV2AuditLog.map((entry, i) => (
                  <tr
                    key={i}
                    data-testid={`ms-audit-row-${i}`}
                    className="border-b border-border/20 hover:bg-muted/10"
                  >
                    <td className="py-1 pr-3 text-muted-foreground">{entry.step}</td>
                    <td className="py-1 pr-3 font-mono text-primary">{entry.tool}</td>
                    <td className="py-1 pr-3 font-mono text-muted-foreground">{entry.params_hash}</td>
                    <td className="py-1 font-mono text-muted-foreground">{entry.result_hash}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
