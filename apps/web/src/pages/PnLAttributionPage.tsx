import { useState, useCallback } from 'react';
import { postPnLAttribution, getPnLDriverPresets, exportPnLAttributionPack } from '../lib/api';

interface Contribution {
  factor: string;
  bucket: string;
  contribution: number;
  pct_of_total: number;
}

interface AttributionResult {
  base_run_id: string;
  compare_run_id: string;
  total_pnl: number;
  contributions: Contribution[];
  top_drivers: Contribution[];
  output_hash: string;
  audit_chain_head_hash: string;
}

const DEMO_BASE_RUN = 'run_base_001';
const DEMO_COMPARE_RUN = 'run_cmp_001';

export default function PnLAttributionPage() {
  const [baseRunId, setBaseRunId] = useState(DEMO_BASE_RUN);
  const [compareRunId, setCompareRunId] = useState(DEMO_COMPARE_RUN);
  const [result, setResult] = useState<AttributionResult | null>(null);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [exportMd, setExportMd] = useState<string | null>(null);
  const [presets, setPresets] = useState<any[]>([]);

  const compute = useCallback(async () => {
    if (!baseRunId.trim() || !compareRunId.trim()) return;
    setLoading(true);
    setError(null);
    setReady(false);
    try {
      const data = await postPnLAttribution({
        base_run_id: baseRunId.trim(),
        compare_run_id: compareRunId.trim(),
      });
      if (data) {
        setResult(data);
        setReady(true);
      } else {
        setError('Attribution computation failed');
      }
    } catch (e) {
      setError('Request failed');
    } finally {
      setLoading(false);
    }
  }, [baseRunId, compareRunId]);

  const loadPresets = useCallback(async () => {
    const data = await getPnLDriverPresets();
    if (data?.presets) setPresets(data.presets);
  }, []);

  const exportPack = useCallback(async (format: 'json' | 'md') => {
    if (!result) return;
    const data = await exportPnLAttributionPack({
      base_run_id: result.base_run_id,
      compare_run_id: result.compare_run_id,
      format,
    });
    if (data) {
      setExportResult(data);
      if (format === 'md' && data.content) setExportMd(data.content);
    }
  }, [result]);

  return (
    <div data-testid="pnl-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">PnL Attribution</h1>
      <p className="text-gray-500 mb-6 text-sm">
        Factor-bucketed PnL attribution between two runs.
      </p>

      {/* Input Form */}
      <div className="bg-white border rounded-lg p-4 mb-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Base Run ID</label>
            <input
              className="border rounded px-3 py-1.5 text-sm w-full"
              value={baseRunId}
              onChange={e => setBaseRunId(e.target.value)}
              data-testid="pnl-base-run-input"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Compare Run ID</label>
            <input
              className="border rounded px-3 py-1.5 text-sm w-full"
              value={compareRunId}
              onChange={e => setCompareRunId(e.target.value)}
              data-testid="pnl-compare-run-input"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={compute}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            data-testid="pnl-compute-btn"
          >
            {loading ? 'Computing…' : 'Compute Attribution'}
          </button>
          <button
            onClick={loadPresets}
            className="border px-4 py-1.5 rounded text-sm hover:bg-gray-50"
            data-testid="pnl-presets-btn"
          >
            Load Presets
          </button>
        </div>
        {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
      </div>

      {/* Presets */}
      {presets.length > 0 && (
        <div className="bg-gray-50 border rounded-lg p-4 mb-6" data-testid="pnl-presets-ready">
          <h2 className="text-sm font-semibold mb-2">Demo Presets</h2>
          <div className="space-y-1">
            {presets.map((p) => (
              <button
                key={p.id}
                className="block text-left text-xs text-blue-600 hover:underline"
                onClick={() => {
                  setBaseRunId(p.base_run_id);
                  setCompareRunId(p.compare_run_id);
                }}
                data-testid={`pnl-preset-${p.id}`}
              >
                {p.name} – {p.description}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {ready && result && (
        <div data-testid="pnl-ready" className="space-y-6">
          {/* Summary */}
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Summary</h2>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-xs text-gray-500">Total PnL</p>
                <p className={`text-lg font-bold ${result.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {result.total_pnl >= 0 ? '+' : ''}{result.total_pnl.toFixed(4)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Output Hash</p>
                <p className="font-mono text-xs text-gray-600">{result.output_hash}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Chain Head</p>
                <p className="font-mono text-xs text-gray-600">{result.audit_chain_head_hash}</p>
              </div>
            </div>
          </div>

          {/* Top Drivers */}
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Top Drivers</h2>
            <div className="grid grid-cols-3 gap-3">
              {result.top_drivers.map((d) => (
                <div
                  key={d.factor}
                  className="border rounded p-3"
                  data-testid={`pnl-driver-${d.factor}`}
                >
                  <p className="text-xs text-gray-500 uppercase">{d.factor}</p>
                  <p className={`text-base font-bold ${d.contribution >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {d.contribution >= 0 ? '+' : ''}{d.contribution.toFixed(4)}
                  </p>
                  <p className="text-xs text-gray-400">{d.pct_of_total.toFixed(1)}% of total</p>
                </div>
              ))}
            </div>
          </div>

          {/* Contributions Table */}
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Factor Contributions</h2>
            <table className="w-full text-xs" data-testid="pnl-contributions-table">
              <thead>
                <tr className="border-b text-gray-500">
                  <th className="text-left pb-2">Factor</th>
                  <th className="text-left pb-2">Bucket</th>
                  <th className="text-right pb-2">Contribution</th>
                  <th className="text-right pb-2">% of Total</th>
                </tr>
              </thead>
              <tbody>
                {result.contributions.map((c, _i) => (
                  <tr
                    key={c.factor}
                    className="border-b last:border-0 hover:bg-gray-50"
                    data-testid={`pnl-row-${c.factor}`}
                  >
                    <td className="py-2 font-medium">{c.factor}</td>
                    <td className="py-2 text-gray-500">{c.bucket}</td>
                    <td className={`py-2 text-right font-mono ${c.contribution >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {c.contribution >= 0 ? '+' : ''}{c.contribution.toFixed(6)}
                    </td>
                    <td className="py-2 text-right text-gray-500">{c.pct_of_total.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Export */}
          <div className="bg-white border rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Export</h2>
            <div className="flex gap-2">
              <button
                onClick={() => exportPack('md')}
                className="border border-blue-600 text-blue-600 px-4 py-1.5 rounded text-sm hover:bg-blue-50"
                data-testid="pnl-export-md"
              >
                Export MD
              </button>
              <button
                onClick={() => exportPack('json')}
                className="border border-gray-400 text-gray-600 px-4 py-1.5 rounded text-sm hover:bg-gray-50"
                data-testid="pnl-export-pack"
              >
                Export Pack (JSON)
              </button>
            </div>
            {exportResult && (
              <div className="mt-3 text-xs text-gray-500" data-testid="pnl-export-ready">
                Pack hash: <span className="font-mono">{exportResult.pack_hash}</span>
              </div>
            )}
            {exportMd && (
              <pre className="mt-3 bg-gray-50 border rounded p-3 text-xs overflow-auto max-h-48" data-testid="pnl-export-md-preview">
                {exportMd}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
