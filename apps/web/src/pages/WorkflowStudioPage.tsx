import { useState, useCallback, useEffect } from 'react';
import { wfGenerate, wfActivate, wfList, wfSimulate, wfRuns } from '@/lib/api';

const DEFAULT_STEPS = ['run_tests', 'security_scan', 'build_image', 'deploy_staging', 'e2e_tests', 'readiness_check', 'deploy_production'];

export default function WorkflowStudioPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [current, setCurrent] = useState<any>(null);
  const [simRun, setSimRun] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    const data = await wfList();
    if (data) setWorkflows(data.workflows ?? []);
  }, []);

  const loadRuns = useCallback(async () => {
    const data = await wfRuns();
    if (data) setRuns(data.runs ?? []);
  }, []);

  useEffect(() => { loadList(); loadRuns(); }, [loadList, loadRuns]);

  const doGenerate = useCallback(async () => {
    setLoading(true); setError(null); setCurrent(null); setSimRun(null);
    try {
      const data = await wfGenerate({
        name: 'release-pipeline',
        trigger: 'push',
        branches: ['main'],
        steps: DEFAULT_STEPS,
        description: 'Standard release pipeline for RiskCanvas',
      });
      if (data) { setCurrent(data); await loadList(); }
    } catch { setError('Generate failed'); }
    setLoading(false);
  }, [loadList]);

  const doActivate = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    const data = await wfActivate(current.workflow_id);
    if (data) { setCurrent(data); await loadList(); }
    setLoading(false);
  }, [current, loadList]);

  const doSimulate = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    const data = await wfSimulate(current.workflow_id);
    if (data) { setSimRun(data); await loadRuns(); }
    setLoading(false);
  }, [current, loadRuns]);

  const statusBadge = (s: string) =>
    s === 'active' ? 'bg-green-100 text-green-700' :
    s === 'draft' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600';

  return (
    <div data-testid="workflows-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Workflow Studio</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 29 · v4.62–v4.65 · DSL v2</p>

      {error && <div data-testid="wf-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Pipeline Builder</h2>
        <div className="bg-gray-50 rounded p-4 mb-4 text-xs font-mono">
          <div className="text-gray-600">name: release-pipeline</div>
          <div className="text-gray-600">trigger: push → main</div>
          <div className="text-gray-600">steps: {DEFAULT_STEPS.join(' → ')}</div>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button data-testid="wf-generate-btn" onClick={doGenerate} disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
            1. Generate Workflow
          </button>
          <button data-testid="wf-activate-btn" onClick={doActivate} disabled={loading || !current}
            className="px-3 py-1 bg-green-600 text-white rounded text-sm disabled:opacity-50">
            2. Activate
          </button>
          <button data-testid="wf-simulate-btn" onClick={doSimulate} disabled={loading || !current}
            className="px-3 py-1 bg-purple-600 text-white rounded text-sm disabled:opacity-50">
            3. Simulate
          </button>
        </div>
      </section>

      {current && (
        <div data-testid="wf-current-ready" className="mb-4 bg-gray-50 rounded p-4 text-sm">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-semibold">{current.name}</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusBadge(current.status)}`}>{current.status}</span>
            <span className="text-xs text-gray-400">{current.step_count} steps · {current.dsl_version}</span>
          </div>
          <div className="text-xs text-gray-500 font-mono">id: {current.workflow_id}</div>
        </div>
      )}

      {simRun && (
        <div data-testid="wf-sim-ready" className="mb-4 bg-purple-50 rounded p-4 text-sm">
          <div className="font-semibold mb-2">Simulation: {simRun.passed}/{simRun.step_count} passed</div>
          <div className="space-y-1">
            {simRun.steps?.map((s: any, i: number) => (
              <div key={i} className="text-xs flex gap-2">
                <span className="font-mono w-24 text-gray-400">t+{s.t_offset_s}s</span>
                <span className={`w-16 font-semibold ${s.status === 'passed' ? 'text-green-600' : 'text-red-600'}`}>{s.status}</span>
                <span className="text-gray-700">{s.step_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {workflows.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Workflows ({workflows.length})</h2>
          <table className="w-full text-xs">
            <thead><tr className="border-b"><th className="text-left py-1">Name</th><th className="text-left py-1">Status</th><th className="text-left py-1">Steps</th></tr></thead>
            <tbody>
              {workflows.map((w: any) => (
                <tr key={w.workflow_id} data-testid={`wf-row-${w.workflow_id?.slice(0, 8)}`} className="border-b border-gray-100">
                  <td className="py-1">{w.name}</td>
                  <td className="py-1"><span className={`px-1.5 py-0.5 rounded text-xs ${statusBadge(w.status)}`}>{w.status}</span></td>
                  <td className="py-1">{w.step_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {runs.length > 0 && (
        <section className="mt-4">
          <h2 className="text-lg font-semibold mb-2">Simulation Runs ({runs.length})</h2>
          <div className="text-xs text-gray-500">
            {runs.map((r: any, i: number) => (
              <div key={i} data-testid={`wf-run-${r.run_id?.slice(0, 8)}`} className="py-1 border-b border-gray-100">
                run {r.run_id?.slice(0, 8)} · {r.passed}/{r.step_count} passed · {r.workflow_name}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
