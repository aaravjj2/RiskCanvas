import { useState, useCallback } from 'react';
import {
  postScenarioValidate,
  postScenarioCreate,
  getScenarioList,
  postScenarioDiff,
  exportScenarioPack,
} from '../lib/api';

const DEMO_SCENARIO_A = JSON.stringify({
  name: "Tech Sell-off Q1",
  description: "Stress test tech portfolio",
  tags: ["stress", "tech"],
  spot_shocks: [
    { symbols: ["AAPL", "MSFT"], shock_type: "relative", shock_value: -0.10 }
  ],
  vol_shocks: [
    { symbols: [], shock_type: "relative", shock_value: 0.20 }
  ],
  rates_shocks: [],
  curve_node_shocks: [],
  parameters: { horizon: "1W" }
}, null, 2);

const DEMO_SCENARIO_B = JSON.stringify({
  name: "Rates Shock +50bps",
  description: "Parallel shift scenario",
  tags: ["rates"],
  spot_shocks: [],
  vol_shocks: [],
  rates_shocks: [
    { curve_id: "USD_SOFR", shock_type: "parallel", shock_bps: 50.0 }
  ],
  curve_node_shocks: [],
  parameters: {}
}, null, 2);

export default function ScenariosDSLPage() {
  const [scenarioJson, setScenarioJson] = useState(DEMO_SCENARIO_A);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [listReady, setListReady] = useState(false);
  const [diffResult, setDiffResult] = useState<any>(null);
  const [selectedForDiff, setSelectedForDiff] = useState<string[]>([]);
  const [packResult, setPackResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'author' | 'list' | 'diff' | 'pack'>('author');

  const handleValidate = useCallback(async () => {
    setError(null);
    try {
      const parsed = JSON.parse(scenarioJson);
      const result = await postScenarioValidate(parsed);
      setValidationResult(result);
    } catch (e) {
      setError('Invalid JSON or request failed');
    }
  }, [scenarioJson]);

  const handleSave = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const parsed = JSON.parse(scenarioJson);
      const result = await postScenarioCreate(parsed);
      if (result?.scenario_id) {
        setCreatedId(result.scenario_id);
      } else {
        setError('Save failed');
      }
    } catch (e) {
      setError('Invalid JSON or request failed');
    } finally {
      setLoading(false);
    }
  }, [scenarioJson]);

  const handleLoadList = useCallback(async () => {
    setLoading(true);
    const result = await getScenarioList();
    if (result?.scenarios) {
      setScenarios(result.scenarios);
      setListReady(true);
    }
    setLoading(false);
  }, []);

  const toggleDiffSelect = useCallback((id: string) => {
    setSelectedForDiff(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : prev.length < 2
          ? [...prev, id]
          : [prev[1], id]
    );
  }, []);

  const handleDiff = useCallback(async () => {
    if (selectedForDiff.length !== 2) return;
    const [a, b] = selectedForDiff;
    const result = await postScenarioDiff(a, b);
    setDiffResult(result);
  }, [selectedForDiff]);

  const handleExportPack = useCallback(async () => {
    if (selectedForDiff.length === 0) return;
    const result = await exportScenarioPack(selectedForDiff);
    setPackResult(result);
  }, [selectedForDiff]);

  return (
    <div data-testid="scenario-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Scenario DSL Studio</h1>
      <p className="text-gray-500 text-sm mb-6">
        Author, validate, store, and diff scenarios using the RiskCanvas Scenario DSL.
      </p>

      {/* Tab nav */}
      <div className="flex gap-1 mb-6 border-b">
        {(['author', 'list', 'diff', 'pack'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            data-testid={`scenario-tab-${t}`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Author tab */}
      {tab === 'author' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex gap-2 mb-2">
              <button
                onClick={() => setScenarioJson(DEMO_SCENARIO_A)}
                className="text-xs border px-3 py-1 rounded hover:bg-gray-50"
                data-testid="scenario-demo-a"
              >
                Demo Scenario A
              </button>
              <button
                onClick={() => setScenarioJson(DEMO_SCENARIO_B)}
                className="text-xs border px-3 py-1 rounded hover:bg-gray-50"
                data-testid="scenario-demo-b"
              >
                Demo Scenario B
              </button>
            </div>
            <textarea
              className="w-full border rounded p-3 font-mono text-xs min-h-56 focus:outline-blue-500"
              value={scenarioJson}
              onChange={e => setScenarioJson(e.target.value)}
              data-testid="scenario-json-editor"
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleValidate}
                className="border border-blue-600 text-blue-600 px-4 py-1.5 rounded text-sm hover:bg-blue-50"
                data-testid="scenario-validate-btn"
              >
                Validate
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                data-testid="scenario-save-btn"
              >
                {loading ? 'Saving...' : 'Save Scenario'}
              </button>
            </div>
            {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
          </div>

          {validationResult && (
            <div
              className={`border rounded-lg p-4 ${validationResult.valid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
              data-testid="scenario-validate-result"
            >
              <p className={`text-sm font-medium ${validationResult.valid ? 'text-green-700' : 'text-red-700'}`}>
                {validationResult.valid ? '✓ Valid scenario' : `✗ ${validationResult.error_count} validation error(s)`}
              </p>
              {validationResult.errors?.length > 0 && (
                <ul className="mt-2 text-xs text-red-600 space-y-1">
                  {validationResult.errors.map((e: string, i: number) => (
                    <li key={i}>• {e}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {createdId && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4" data-testid="scenario-created">
              <p className="text-sm text-blue-700">✓ Scenario saved</p>
              <p className="font-mono text-xs text-blue-600 mt-1">{createdId}</p>
            </div>
          )}
        </div>
      )}

      {/* List tab */}
      {tab === 'list' && (
        <div className="space-y-4">
          <button
            onClick={handleLoadList}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700"
            data-testid="scenario-load-list-btn"
          >
            {loading ? 'Loading...' : 'Load Scenarios'}
          </button>

          {listReady && (
            <div className="bg-white border rounded-lg overflow-hidden" data-testid="scenario-list-ready">
              <table className="w-full text-xs">
                <thead className="bg-gray-50">
                  <tr className="text-gray-500 text-left">
                    <th className="px-4 py-2">ID</th>
                    <th className="px-4 py-2">Name</th>
                    <th className="px-4 py-2">Tags</th>
                    <th className="px-4 py-2">Hash</th>
                    <th className="px-4 py-2">Select</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarios.map((s) => (
                    <tr key={s.scenario_id} className="border-t hover:bg-gray-50" data-testid={`scenario-row-${s.scenario_id.slice(0, 8)}`}>
                      <td className="px-4 py-2 font-mono">{s.scenario_id.slice(0, 8)}...</td>
                      <td className="px-4 py-2 font-medium">{s.name}</td>
                      <td className="px-4 py-2 text-gray-400">{s.tags?.join(', ') || '-'}</td>
                      <td className="px-4 py-2 font-mono text-gray-400">{s.output_hash}</td>
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={selectedForDiff.includes(s.scenario_id)}
                          onChange={() => toggleDiffSelect(s.scenario_id)}
                          data-testid={`scenario-select-${s.scenario_id.slice(0, 8)}`}
                        />
                      </td>
                    </tr>
                  ))}
                  {scenarios.length === 0 && (
                    <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">No scenarios. Create one in the Author tab.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Diff tab */}
      {tab === 'diff' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-3">
              Select 2 scenarios from the List tab, then diff them.
            </p>
            <div className="text-xs text-gray-400 mb-3">
              Selected: {selectedForDiff.length === 0 ? 'none' : selectedForDiff.map(s => s.slice(0, 8)).join(', ')}
            </div>
            <button
              onClick={handleDiff}
              disabled={selectedForDiff.length !== 2}
              className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              data-testid="scenario-diff-btn"
            >
              Diff Selected
            </button>
          </div>

          {diffResult && (
            <div className="bg-white border rounded-lg p-4" data-testid="scenario-diff-ready">
              <h3 className="text-sm font-semibold mb-3">
                Diff: {diffResult.a_name} → {diffResult.b_name}
              </h3>
              <p className="text-xs text-gray-500 mb-3">{diffResult.change_count} change(s)   hash: {diffResult.output_hash}</p>
              {diffResult.changes.length === 0 ? (
                <p className="text-xs text-green-600">No differences</p>
              ) : (
                <table className="w-full text-xs">
                  <thead className="text-gray-500">
                    <tr>
                      <th className="text-left pb-2">Field</th>
                      <th className="text-left pb-2">Type</th>
                      <th className="text-left pb-2">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {diffResult.changes.map((c: any, i: number) => (
                      <tr key={i} className="border-t" data-testid={`scenario-diff-row-${i}`}>
                        <td className="py-2 font-medium">{c.field}</td>
                        <td className="py-2 text-gray-400">{c.change_type}</td>
                        <td className="py-2 text-gray-600 font-mono text-xs">
                          {c.change_type === 'modified'
                            ? `${JSON.stringify(c.from)} → ${JSON.stringify(c.to)}`
                            : `+${c.added_count || 0} / -${c.removed_count || 0}`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      )}

      {/* Pack tab */}
      {tab === 'pack' && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <p className="text-sm text-gray-500 mb-3">
              Export selected scenarios as a deterministic pack.
            </p>
            <div className="text-xs text-gray-400 mb-3">
              Selected: {selectedForDiff.length === 0 ? 'none' : selectedForDiff.map(s => s.slice(0, 8)).join(', ')}
            </div>
            <button
              onClick={handleExportPack}
              disabled={selectedForDiff.length === 0}
              className="bg-green-600 text-white px-4 py-1.5 rounded text-sm hover:bg-green-700 disabled:opacity-50"
              data-testid="scenario-export-pack-btn"
            >
              Export Pack
            </button>
          </div>

          {packResult && (
            <div className="bg-white border rounded-lg p-4" data-testid="scenario-pack-ready">
              <h3 className="text-sm font-semibold mb-2">Pack Export</h3>
              <div className="text-xs space-y-1">
                <p>Scenarios: <span className="font-medium">{packResult.manifest?.scenario_count}</span></p>
                <p>Manifest Hash: <span className="font-mono">{packResult.manifest?.manifest_hash}</span></p>
                <p>Pack Hash: <span className="font-mono">{packResult.pack_hash}</span></p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
