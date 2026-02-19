import { useState, useCallback } from 'react';
import { postConstructionSolve, postConstructionCompare, exportConstructionPack } from '../lib/api';

const DEMO_WEIGHTS: Record<string, number> = {
  AAPL: 0.20,
  MSFT: 0.20,
  GOOGL: 0.15,
  AMZN: 0.15,
  TSLA: 0.10,
  JPM: 0.10,
  XOM: 0.10,
};

const DEMO_CONSTRAINTS = {
  var_cap: 0.05,
  max_weight_per_symbol: 0.25,
  turnover_cap: 0.30,
  sector_caps: { Technology: 0.60, Finance: 0.30 },
};

export default function ConstructionStudioPage() {
  const [weightsJson, setWeightsJson] = useState(JSON.stringify(DEMO_WEIGHTS, null, 2));
  const [constraintsJson, setConstraintsJson] = useState(JSON.stringify(DEMO_CONSTRAINTS, null, 2));
  const [objective, setObjective] = useState<'minimize_risk' | 'balanced'>('minimize_risk');
  const [solveResult, setSolveResult] = useState<any>(null);
  const [ready, setReady] = useState(false);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [packResult, setPackResult] = useState<any>(null);
  const [memoContent, setMemoContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'solve' | 'compare' | 'memo'>('solve');

  const handleSolve = useCallback(async () => {
    setError(null);
    setLoading(true);
    setReady(false);
    try {
      const weights = JSON.parse(weightsJson);
      const constraints = JSON.parse(constraintsJson);
      const result = await postConstructionSolve({ current_weights: weights, constraints, objective });
      if (result?.target_weights) {
        setSolveResult(result);
        setReady(true);
      } else {
        setError('Solve failed');
      }
    } catch (e) {
      setError('Invalid JSON or request failed');
    } finally {
      setLoading(false);
    }
  }, [weightsJson, constraintsJson, objective]);

  const handleCompare = useCallback(async () => {
    if (!solveResult) return;
    setLoading(true);
    // Compare the "before" (using current weights as "before" solve) with the solve result
    const beforeResult = {
      before_metrics: solveResult.before_metrics,
      after_metrics: solveResult.before_metrics, // before = before
      output_hash: solveResult.input_hash || 'before',
      trade_count: 0,
      cost_estimate: 0,
    };
    const result = await postConstructionCompare(beforeResult, solveResult);
    setCompareResult(result);
    setLoading(false);
  }, [solveResult]);

  const handleExportPack = useCallback(async () => {
    if (!solveResult) return;
    setLoading(true);
    const result = await exportConstructionPack(solveResult);
    if (result) {
      setPackResult(result);
      if (result.memo?.content_md) setMemoContent(result.memo.content_md);
    }
    setLoading(false);
  }, [solveResult]);

  return (
    <div data-testid="construct-page" className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Portfolio Construction Studio</h1>
      <p className="text-gray-500 text-sm mb-6">
        Constraint-based deterministic portfolio construction solver.
      </p>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {(['solve', 'compare', 'memo'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            data-testid={`construct-tab-${t}`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Solve tab */}
      {tab === 'solve' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-2">Current Weights</h3>
              <textarea
                className="w-full border rounded p-2 font-mono text-xs min-h-40"
                value={weightsJson}
                onChange={e => setWeightsJson(e.target.value)}
                data-testid="construct-weights-input"
              />
            </div>
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-2">Constraints</h3>
              <textarea
                className="w-full border rounded p-2 font-mono text-xs min-h-40"
                value={constraintsJson}
                onChange={e => setConstraintsJson(e.target.value)}
                data-testid="construct-constraints-input"
              />
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-4 flex-wrap">
              <div>
                <label className="text-xs font-medium text-gray-600 mr-2">Objective:</label>
                <select
                  value={objective}
                  onChange={e => setObjective(e.target.value as any)}
                  className="border rounded px-2 py-1 text-sm"
                  data-testid="construct-objective-select"
                >
                  <option value="minimize_risk">Minimize Risk</option>
                  <option value="balanced">Balanced</option>
                </select>
              </div>
              <button
                onClick={handleSolve}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                data-testid="construct-solve-btn"
              >
                {loading ? 'Solving...' : 'Solve'}
              </button>
            </div>
            {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
          </div>

          {ready && solveResult && (
            <div data-testid="construct-ready" className="space-y-4">
              {/* Metrics */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="text-sm font-semibold mb-3">Risk Metrics</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Before</p>
                    <div className="bg-gray-50 rounded p-3 text-xs space-y-1">
                      <p>VaR: <span className="font-mono">{solveResult.before_metrics?.var?.toFixed(6)}</span></p>
                      <p>Max Weight: <span className="font-mono">{solveResult.before_metrics?.max_weight?.toFixed(4)}</span></p>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">After</p>
                    <div className="bg-blue-50 rounded p-3 text-xs space-y-1">
                      <p>VaR: <span className="font-mono text-green-700">{solveResult.after_metrics?.var?.toFixed(6)}</span></p>
                      <p>Max Weight: <span className="font-mono">{solveResult.after_metrics?.max_weight?.toFixed(4)}</span></p>
                      <p>Turnover: <span className="font-mono">{solveResult.after_metrics?.turnover?.toFixed(4)}</span></p>
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-xs text-gray-400">
                  <span>Output Hash: </span>
                  <span className="font-mono">{solveResult.output_hash}</span>
                </div>
              </div>

              {/* Trades table */}
              <div className="bg-white border rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b">
                  <h3 className="text-sm font-semibold">
                    Proposed Trades ({solveResult.trade_count})
                    <span className="text-xs font-normal text-gray-400 ml-2">Cost: {solveResult.cost_estimate?.toFixed(6)}</span>
                  </h3>
                </div>
                <div data-testid="construct-results">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 text-gray-500">
                      <tr>
                        <th className="text-left px-4 py-2">Symbol</th>
                        <th className="text-left px-4 py-2">Sector</th>
                        <th className="text-left px-4 py-2">Direction</th>
                        <th className="text-right px-4 py-2">Current</th>
                        <th className="text-right px-4 py-2">Target</th>
                        <th className="text-right px-4 py-2">Delta</th>
                        <th className="text-right px-4 py-2">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {solveResult.trades?.map((t: any, _i: number) => (
                        <tr
                          key={t.symbol}
                          className="border-t hover:bg-gray-50"
                          data-testid={`construct-trade-row-${t.symbol}`}
                        >
                          <td className="px-4 py-2 font-medium">{t.symbol}</td>
                          <td className="px-4 py-2 text-gray-400">{t.sector}</td>
                          <td className={`px-4 py-2 font-medium ${t.direction === 'BUY' ? 'text-green-600' : 'text-red-600'}`}>
                            {t.direction}
                          </td>
                          <td className="px-4 py-2 text-right font-mono">{t.current_weight?.toFixed(4)}</td>
                          <td className="px-4 py-2 text-right font-mono">{t.target_weight?.toFixed(4)}</td>
                          <td className={`px-4 py-2 text-right font-mono ${t.delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {t.delta >= 0 ? '+' : ''}{t.delta?.toFixed(4)}
                          </td>
                          <td className="px-4 py-2 text-right font-mono text-gray-400">{t.cost_estimate?.toFixed(6)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleExportPack}
                  disabled={loading}
                  className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700 disabled:opacity-50"
                  data-testid="construct-export-btn"
                >
                  Export Decision Pack
                </button>
                <button
                  onClick={() => setTab('compare')}
                  className="border border-blue-600 text-blue-600 px-4 py-1.5 rounded text-sm hover:bg-blue-50"
                  data-testid="construct-compare-btn"
                >
                  View Compare
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compare tab */}
      {tab === 'compare' && (
        <div className="space-y-4">
          {!solveResult ? (
            <div className="text-center text-gray-400 py-8">Run Solve first.</div>
          ) : (
            <div className="bg-white border rounded-lg p-4">
              <button
                onClick={handleCompare}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50 mb-4"
                data-testid="construct-run-compare-btn"
              >
                Compare Before/After
              </button>

              {compareResult && (
                <div data-testid="construct-compare-ready">
                  <h3 className="text-sm font-semibold mb-3">Metric Changes</h3>
                  {compareResult.metric_changes?.length === 0 ? (
                    <p className="text-xs text-gray-400">No metric changes.</p>
                  ) : (
                    <table className="w-full text-xs">
                      <thead className="text-gray-500">
                        <tr>
                          <th className="text-left pb-2">Metric</th>
                          <th className="text-right pb-2">Before</th>
                          <th className="text-right pb-2">After</th>
                          <th className="text-right pb-2">Change</th>
                        </tr>
                      </thead>
                      <tbody>
                        {compareResult.metric_changes?.map((c: any, i: number) => (
                          <tr key={i} className="border-t" data-testid={`construct-delta-row-${c.metric}`}>
                            <td className="py-2">{c.metric}</td>
                            <td className="py-2 text-right font-mono">{c.before}</td>
                            <td className="py-2 text-right font-mono">{c.after}</td>
                            <td className={`py-2 text-right font-mono ${(c.change || 0) < 0 ? 'text-green-600' : (c.change || 0) > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                              {c.change != null ? (c.change >= 0 ? '+' : '') + c.change?.toFixed(6) : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <p className="text-xs text-gray-400 mt-3">Hash: {compareResult.output_hash}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Memo tab */}
      {tab === 'memo' && (
        <div className="space-y-4">
          {packResult ? (
            <div className="space-y-4" data-testid="construct-memo-ready">
              <div className="bg-white border rounded-lg p-4">
                <h3 className="text-sm font-semibold mb-3">Decision Pack</h3>
                <div className="text-xs space-y-1">
                  <p>Manifest Hash: <span className="font-mono">{packResult.manifest?.manifest_hash}</span></p>
                  <p>Pack Hash: <span className="font-mono">{packResult.pack_hash}</span></p>
                  <p>Memo Hash: <span className="font-mono">{packResult.memo?.memo_hash}</span></p>
                </div>
              </div>
              {memoContent && (
                <div className="bg-white border rounded-lg p-4">
                  <h3 className="text-sm font-semibold mb-3">Decision Memo</h3>
                  <pre className="text-xs bg-gray-50 border rounded p-3 overflow-auto max-h-80" data-testid="construct-memo-content">
                    {memoContent}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 border rounded-lg p-6 text-center text-gray-400 text-sm">
              Export a decision pack from the Solve tab to view the memo.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
