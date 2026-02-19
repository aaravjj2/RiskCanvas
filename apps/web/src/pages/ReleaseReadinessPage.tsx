import { useState, useCallback } from 'react';
import { releaseEvaluate, releaseExportPack } from '@/lib/api';

const DEMO_METRICS = {
  test_pass_rate: 99.5,
  code_coverage: 87.3,
  critical_vulnerabilities: 0,
  e2e_pass_rate: 100.0,
  build_latency_s: 95,
  approval_count: 2,
  docs_coverage_pct: 82.0,
  secret_scan_violations: 0,
};

export default function ReleaseReadinessPage() {
  const [result, setResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doEvaluate = useCallback(async () => {
    setLoading(true); setError(null); setResult(null); setExportResult(null);
    try {
      const data = await releaseEvaluate(DEMO_METRICS, { version: 'v4.73.0', branch: 'main', author: 'ci-bot' });
      if (data) setResult(data);
    } catch { setError('Evaluation failed'); }
    setLoading(false);
  }, []);

  const doExport = useCallback(async () => {
    if (!result) return;
    setLoading(true);
    const data = await releaseExportPack(result.assessment_id);
    if (data) setExportResult(data);
    setLoading(false);
  }, [result]);

  const verdictStyle = (v: string) =>
    v === 'SHIP' ? 'bg-green-100 text-green-700 border-green-300' :
    v === 'CONDITIONAL' ? 'bg-yellow-100 text-yellow-700 border-yellow-300' :
    'bg-red-100 text-red-700 border-red-300';

  const gateColor = (s: string) =>
    s === 'PASS' ? 'text-green-600' : s === 'WARN' ? 'text-yellow-600' : 'text-red-600';

  return (
    <div data-testid="readiness-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Release Readiness</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 28 · v4.58–v4.61</p>

      {error && <div data-testid="readiness-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Evaluate Release</h2>
        <div className="bg-gray-50 rounded p-4 mb-4 text-xs font-mono">
          <div className="font-semibold text-sm text-gray-700 mb-2">Demo Metrics (v4.73.0 · main)</div>
          {Object.entries(DEMO_METRICS).map(([k, v]) => (
            <div key={k} className="text-gray-600">{k}: {String(v)}</div>
          ))}
        </div>
        <div className="flex gap-2">
          <button data-testid="readiness-evaluate-btn" onClick={doEvaluate} disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
            Evaluate Readiness
          </button>
          <button data-testid="readiness-export-btn" onClick={doExport} disabled={loading || !result}
            className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">
            Export Release Memo
          </button>
        </div>
      </section>

      {result && (
        <div data-testid="readiness-result-ready" className="mb-6">
          <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-lg border mb-4 ${verdictStyle(result.verdict)}`}>
            <span className="text-2xl font-bold">{result.score}%</span>
            <span className="text-lg font-semibold">{result.verdict}</span>
            <span className="text-sm">{result.blocked_gates} blocked · {result.warned_gates} warned</span>
          </div>

          <div className="mb-4 bg-gray-50 rounded p-3 text-sm">
            <div className="font-semibold mb-1">{result.memo?.recommendation}</div>
          </div>

          <table className="w-full text-xs">
            <thead>
              <tr className="border-b">
                <th className="text-left py-1">Gate</th>
                <th className="text-right py-1">Value</th>
                <th className="text-right py-1">Threshold</th>
                <th className="text-right py-1">Status</th>
                <th className="text-right py-1">Score</th>
              </tr>
            </thead>
            <tbody>
              {result.gate_results?.map((g: any) => (
                <tr key={g.gate_id} data-testid={`gate-row-${g.gate_id}`} className="border-b border-gray-100">
                  <td className="py-1">{g.gate_name}</td>
                  <td className="py-1 text-right font-mono">{g.value}</td>
                  <td className="py-1 text-right text-gray-400">{g.threshold_pass}</td>
                  <td className={`py-1 text-right font-semibold ${gateColor(g.status)}`}>{g.status}</td>
                  <td className="py-1 text-right">{g.score_contribution}/{g.weight}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="font-mono text-xs text-gray-400 mt-2">
            output_hash: {result.output_hash?.slice(0, 16)}…
          </div>
        </div>
      )}

      {exportResult && (
        <div data-testid="readiness-export-ready" className="bg-gray-50 rounded p-3 text-xs font-mono">
          pack_hash: {exportResult.pack_hash?.slice(0, 16)}… · verdict: {exportResult.verdict} · files: {exportResult.file_count}
        </div>
      )}
    </div>
  );
}
