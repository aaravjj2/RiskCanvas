import { useState, useCallback, useEffect } from 'react';
import { incidentListScenarios, incidentRunDrill, incidentExportPack } from '@/lib/api';

export default function IncidentDrillsPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState('api_latency_spike');
  const [run, setRun] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadScenarios = useCallback(async () => {
    const data = await incidentListScenarios();
    if (data) setScenarios(data.scenarios ?? []);
  }, []);

  useEffect(() => { loadScenarios(); }, [loadScenarios]);

  const doRun = useCallback(async () => {
    setLoading(true); setError(null); setRun(null); setExportResult(null);
    try {
      const data = await incidentRunDrill(selectedScenario, {});
      if (data) setRun(data);
    } catch { setError('Drill run failed'); }
    setLoading(false);
  }, [selectedScenario]);

  const doExport = useCallback(async () => {
    if (!run) return;
    setLoading(true);
    const data = await incidentExportPack(run.run_id);
    if (data) setExportResult(data);
    setLoading(false);
  }, [run]);

  const severityColor = (s: string) =>
    s === 'CRITICAL' ? 'text-red-700 bg-red-100' : 'text-orange-700 bg-orange-100';

  const phaseColor = (p: string) =>
    p === 'inject' ? 'text-red-600' : p === 'detect' ? 'text-orange-600' :
    p === 'remediate' ? 'text-blue-600' : 'text-green-600';

  return (
    <div data-testid="incidents-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Incident Drills</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 27 · v4.54–v4.57</p>

      {error && <div data-testid="incidents-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Select Scenario</h2>
        <div className="flex gap-2 flex-wrap mb-3">
          {scenarios.map(s => (
            <button key={s.id} data-testid={`drill-scenario-${s.id}`}
              onClick={() => setSelectedScenario(s.id)}
              className={`px-3 py-1 rounded text-sm border ${selectedScenario === s.id ? 'bg-red-600 text-white border-red-600' : 'bg-white text-gray-700 border-gray-300'}`}>
              {s.name}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button data-testid="drill-run-btn" onClick={doRun} disabled={loading}
            className="px-3 py-1 bg-red-600 text-white rounded text-sm disabled:opacity-50">
            Run Drill
          </button>
          <button data-testid="drill-export-btn" onClick={doExport} disabled={loading || !run}
            className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">
            Export Pack
          </button>
        </div>
      </section>

      {run && (
        <div data-testid="drill-run-ready" className="mb-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-semibold">{run.scenario_name}</span>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${severityColor(run.severity)}`}>{run.severity}</span>
            <span className="text-xs text-green-600 font-semibold">{run.status.toUpperCase()}</span>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
            <div className="bg-gray-50 rounded p-3">
              <div className="text-xs text-gray-500">TTD (Time to Detect)</div>
              <div className="font-bold text-lg">{run.metrics?.ttd_s}s</div>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <div className="text-xs text-gray-500">TTM (Time to Mitigate)</div>
              <div className="font-bold text-lg">{run.metrics?.ttm_s}s</div>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <div className="text-xs text-gray-500">TTR (Total)</div>
              <div className="font-bold text-lg">{run.metrics?.ttr_s}s</div>
            </div>
          </div>

          <div className="bg-gray-50 rounded p-4">
            <h3 className="font-semibold text-sm mb-2">Timeline ({run.timeline?.length} steps)</h3>
            <div className="space-y-1">
              {run.timeline?.map((step: any, i: number) => (
                <div key={i} className="text-xs flex items-center gap-2">
                  <span className="font-mono text-gray-400 w-12">t+{step.t_offset_s}s</span>
                  <span className={`font-semibold w-20 ${phaseColor(step.phase)}`}>[{step.phase}]</span>
                  <span className="text-gray-700">{step.action || step.signal}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="font-mono text-xs text-gray-400 mt-2">
            outputs_hash: {run.outputs_hash?.slice(0, 16)}…
          </div>
        </div>
      )}

      {exportResult && (
        <div data-testid="drill-export-ready" className="mt-4 bg-gray-50 rounded p-3 text-xs font-mono">
          pack_hash: {exportResult.pack_hash?.slice(0, 16)}… · files: {exportResult.file_count}
        </div>
      )}

      {scenarios.length > 0 && (
        <section className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Available Scenarios</h2>
          <div className="grid grid-cols-2 gap-3">
            {scenarios.map((s: any) => (
              <div key={s.id} data-testid={`drill-card-${s.id}`} className="bg-gray-50 rounded p-3 text-sm">
                <div className="font-semibold">{s.name}</div>
                <div className="text-xs text-gray-500 mt-1">{s.description?.slice(0, 80)}…</div>
                <div className="flex gap-2 mt-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${severityColor(s.severity)}`}>{s.severity}</span>
                  <span className="text-xs text-gray-400">{s.category}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
