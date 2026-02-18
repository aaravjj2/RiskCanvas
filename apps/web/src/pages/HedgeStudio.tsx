import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  suggestHedges, evaluateHedge, compareRuns,
  getHedgeTemplates, suggestHedgesV2, compareHedgeV2, buildDecisionMemo, exportHedgeDecisionPack,
} from '@/lib/api';
import { useNavigate } from 'react-router-dom';

const TEMPLATE_IDS = ['protective_put', 'collar', 'delta_hedge', 'duration_hedge'];

const DEFAULT_BEFORE_METRICS = { var_95: 5000.0, var_99: 7500.0, delta_exposure: 45000.0 };

export default function HedgeStudio() {
  const [portfolioId, setPortfolioId] = useState('');
  const [runId, setRunId] = useState('');
  const [targetReduction, setTargetReduction] = useState(20);
  const [maxCost, setMaxCost] = useState(10000);
  const [instrumentTypes, setInstrumentTypes] = useState({
    put: true,
    call: false,
    future: false,
  });
  const [hedges, setHedges] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // v2 state
  const [v2Ready, setV2Ready] = useState(false);
  const [_v2Templates, setV2Templates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('protective_put');
  const [v2MaxCost, setV2MaxCost] = useState(10000);
  const [v2MaxContracts, setV2MaxContracts] = useState(20);
  const [v2PortfolioValue, setV2PortfolioValue] = useState(100000);
  const [v2Candidates, setV2Candidates] = useState<any[]>([]);
  const [v2CompareResult, setV2CompareResult] = useState<any>(null);
  const [v2Memo, setV2Memo] = useState<any>(null);
  const [v2HedgeResult, setV2HedgeResult] = useState<any>(null);

  const handleGenerateHedges = async () => {
    if (!portfolioId) {
      alert('Please enter a Portfolio ID');
      return;
    }

    setLoading(true);
    const result = await suggestHedges({
      portfolio_id: portfolioId,
      target_reduction_pct: targetReduction,
      max_cost: maxCost,
      allowed_instruments: Object.keys(instrumentTypes).filter((k) => instrumentTypes[k as keyof typeof instrumentTypes]),
    });

    if (result) {
      setHedges(result.candidates || []);
    }
    setLoading(false);
  };

  const handleApplyHedge = async (hedge: any) => {
    if (!portfolioId) {
      alert('Please enter a Portfolio ID');
      return;
    }

    setLoading(true);
    const result = await evaluateHedge({
      portfolio_id: portfolioId,
      hedge_instruments: [hedge],
    });

    if (result && result.hedged_run_id && runId) {
      const comparison = await compareRuns(runId, result.hedged_run_id);
      if (comparison) {
        navigate('/compare', {
          state: {
            comparison,
            run1: runId,
            run2: result.hedged_run_id,
          },
        });
      }
    } else if (result) {
      alert(`Hedge applied! Hedged Run ID: ${result.hedged_run_id}`);
    }
    setLoading(false);
  };

  // v2 handlers
  const handleInitV2 = async () => {
    setLoading(true);
    const t = await getHedgeTemplates();
    if (t) {
      setV2Templates(t.templates || []);
      setV2Ready(true);
    }
    setLoading(false);
  };

  const handleSuggestV2 = async () => {
    setLoading(true);
    const result = await suggestHedgesV2({
      portfolio_id: portfolioId || 'demo-portfolio',
      portfolio_value: v2PortfolioValue,
      template_id: selectedTemplate,
      objective: HEDGE_TEMPLATES_OBJECTIVES[selectedTemplate] || 'minimize_var',
      before_metrics: DEFAULT_BEFORE_METRICS,
      constraints: { max_cost: v2MaxCost, max_contracts: v2MaxContracts },
    });
    if (result) {
      setV2HedgeResult(result);
      setV2Candidates(result.candidates || []);
    }
    setLoading(false);
  };

  const handleCompareV2 = async () => {
    setLoading(true);
    const best = v2Candidates[0];
    if (!best) { setLoading(false); return; }
    const result = await compareHedgeV2({
      base_run_id: runId || 'demo-run-001',
      base_metrics: best.before_metrics,
      hedged_metrics: best.after_metrics,
    });
    if (result) setV2CompareResult(result);
    setLoading(false);
  };

  const handleBuildMemo = async () => {
    if (!v2HedgeResult || !v2CompareResult) return;
    setLoading(true);
    const result = await buildDecisionMemo({
      hedge_result: v2HedgeResult,
      compare_deltas: v2CompareResult,
      provenance_hashes: {
        hedge_output_hash: v2HedgeResult.output_hash,
      },
    });
    if (result) setV2Memo(result);
    setLoading(false);
  };

  const handleExportMd = async () => {
    if (!v2Memo) return;
    const blob = new Blob([v2Memo.memo_md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hedge-decision-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPack = async () => {
    if (!v2HedgeResult || !v2CompareResult) return;
    setLoading(true);
    const result = await exportHedgeDecisionPack({
      memo_request: {
        hedge_result: v2HedgeResult,
        compare_deltas: v2CompareResult,
        provenance_hashes: {},
      },
      include_candidates: true,
      include_compare: true,
    });
    if (result) {
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hedge-decision-pack-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
    setLoading(false);
  };

  return (
    <div data-testid="hedge-studio-page" className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Hedge Studio</h1>
        <p className="text-gray-600">Generate and apply hedge strategies to reduce portfolio risk</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <Card className="p-4 lg:col-span-1">
          <h2 className="text-lg font-semibold mb-4">Configuration</h2>

          <div className="space-y-4">
            <div>
              <Label htmlFor="portfolio-id">Portfolio ID</Label>
              <Input
                id="portfolio-id"
                data-testid="portfolio-id-input"
                placeholder="portfolio-abc123..."
                value={portfolioId}
                onChange={(e) => setPortfolioId(e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="run-id">Original Run ID (optional)</Label>
              <Input
                id="run-id"
                data-testid="run-id-input"
                placeholder="run-xyz789..."
                value={runId}
                onChange={(e) => setRunId(e.target.value)}
              />
              <p className="text-xs text-gray-500 mt-1">For before/after comparison</p>
            </div>

            <div>
              <Label htmlFor="target-reduction">
                Target VaR Reduction: {targetReduction}%
              </Label>
              <Slider
                id="target-reduction"
                data-testid="target-reduction-slider"
                min={5}
                max={50}
                step={5}
                value={[targetReduction]}
                onValueChange={([val]) => setTargetReduction(val)}
                className="mt-2"
              />
            </div>

            <div>
              <Label htmlFor="max-cost">Max Cost ($)</Label>
              <Input
                id="max-cost"
                data-testid="max-cost-input"
                type="number"
                value={maxCost}
                onChange={(e) => setMaxCost(Number(e.target.value))}
              />
            </div>

            <div>
              <Label>Instrument Types</Label>
              <div className="space-y-2 mt-2">
                {Object.keys(instrumentTypes).map((type) => (
                  <label key={type} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      data-testid={`instrument-${type}-checkbox`}
                      checked={instrumentTypes[type as keyof typeof instrumentTypes]}
                      onChange={(e) =>
                        setInstrumentTypes({
                          ...instrumentTypes,
                          [type]: e.target.checked,
                        })
                      }
                    />
                    <span className="capitalize">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <Button
              onClick={handleGenerateHedges}
              disabled={loading || !portfolioId}
              data-testid="generate-hedges-btn"
              className="w-full"
            >
              {loading ? 'Generating...' : 'Generate Hedges'}
            </Button>
          </div>
        </Card>

        {/* Results Panel */}
        <Card className="p-4 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Hedge Suggestions</h2>

          <div className="space-y-4" data-testid="hedges-list">
            {hedges.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>Configure parameters and click "Generate Hedges" to see suggestions</p>
              </div>
            ) : (
              hedges.map((hedge, idx) => (
                <Card
                  key={idx}
                  data-testid={`hedge-card-${idx}`}
                  className="p-4 border-2 hover:border-blue-500 transition"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">
                        {hedge.instrument_type?.toUpperCase()} on {hedge.underlying}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Strike: ${hedge.strike} | Expiry: {hedge.expiry} | Quantity: {hedge.quantity}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        Rank #{idx + 1}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-500">Cost</p>
                      <p className="font-semibold">
                        ${(hedge.cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">VaR Reduction</p>
                      <p className="font-semibold text-green-600">
                        ${(hedge.var_reduction || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Cost-Effectiveness</p>
                      <p className="font-semibold">
                        {(hedge.cost_effectiveness || 0).toFixed(2)}
                      </p>
                    </div>
                  </div>

                  <Button
                    onClick={() => handleApplyHedge(hedge)}
                    disabled={loading}
                    data-testid={`apply-hedge-btn-${idx}`}
                    className="w-full"
                  >
                    Apply This Hedge
                  </Button>
                </Card>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* ── Hedge Studio Pro (v4.8 / v4.9) ── */}
      <div className="mt-10">
        <h2 className="text-xl font-bold mb-2">Hedge Studio Pro <span className="text-sm font-normal text-blue-600 ml-2">v4.8+</span></h2>
        <p className="text-gray-500 text-sm mb-4">
          Optimizer v2 · Templates · Constraints · Compare · Decision Memo
        </p>

        {!v2Ready && (
          <Button onClick={handleInitV2} disabled={loading} data-testid="hedge-v2-init-btn">
            Initialize Pro Mode
          </Button>
        )}

        {v2Ready && (
          <div data-testid="hedge-v2-ready">
            {/* Template Selector */}
            <Card className="p-4 mb-4">
              <h3 className="font-semibold mb-3">Hedge Template</h3>
              <div className="flex gap-3 flex-wrap">
                {TEMPLATE_IDS.map(tid => (
                  <label key={tid} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="hedge-template"
                      value={tid}
                      data-testid={`hedge-template-${tid}`}
                      checked={selectedTemplate === tid}
                      onChange={() => setSelectedTemplate(tid)}
                    />
                    <span className="capitalize text-sm">{tid.replace(/_/g, ' ')}</span>
                  </label>
                ))}
              </div>
            </Card>

            {/* Constraints */}
            <Card className="p-4 mb-4" data-testid="hedge-constraints-ready">
              <h3 className="font-semibold mb-3">Constraints</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Portfolio Value ($)</Label>
                  <Input
                    type="number"
                    value={v2PortfolioValue}
                    onChange={e => setV2PortfolioValue(Number(e.target.value))}
                    data-testid="hedge-v2-portfolio-value"
                  />
                </div>
                <div>
                  <Label>Max Cost ($)</Label>
                  <Input
                    type="number"
                    value={v2MaxCost}
                    onChange={e => setV2MaxCost(Number(e.target.value))}
                    data-testid="hedge-v2-max-cost"
                  />
                </div>
                <div>
                  <Label>Max Contracts</Label>
                  <Input
                    type="number"
                    value={v2MaxContracts}
                    onChange={e => setV2MaxContracts(Number(e.target.value))}
                    data-testid="hedge-v2-max-contracts"
                  />
                </div>
              </div>
              <Button
                className="mt-4"
                onClick={handleSuggestV2}
                disabled={loading}
                data-testid="hedge-suggest-btn"
              >
                {loading ? 'Running...' : 'Run Optimizer v2'}
              </Button>
            </Card>

            {/* V2 Results */}
            {v2Candidates.length > 0 && (
              <Card className="p-4 mb-4">
                <h3 className="font-semibold mb-3">Top Candidates</h3>
                <div data-testid="hedge-results-table">
                  <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ background: '#f3f4f6' }}>
                        {['Rank', 'Instrument', 'Strike%', 'Contracts', 'Cost', 'Score'].map(h => (
                          <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e5e7eb' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {v2Candidates.slice(0, 5).map((c, i) => (
                        <tr key={c.candidate_id}>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>#{i + 1}</td>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{c.instrument}</td>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{(c.strike_pct * 100).toFixed(0)}%</td>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{c.contracts}</td>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>${c.total_cost.toFixed(2)}</td>
                          <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{c.score.toFixed(6)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Button
                  className="mt-4"
                  onClick={handleCompareV2}
                  disabled={loading || v2Candidates.length === 0}
                  data-testid="hedge-compare-btn"
                >
                  Compare Best Candidate
                </Button>
              </Card>
            )}

            {/* Compare Deltas */}
            {v2CompareResult && (
              <Card className="p-4 mb-4" data-testid="hedge-delta-ready">
                <h3 className="font-semibold mb-3">Before vs After Deltas</h3>
                <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ background: '#f3f4f6' }}>
                      {['Metric', 'Before', 'After', 'Delta', '% Change'].map(h => (
                        <th key={h} style={{ padding: '8px 10px', textAlign: 'left', border: '1px solid #e5e7eb' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(v2CompareResult.base_metrics || {}).map(metric => (
                      <tr key={metric}>
                        <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{metric}</td>
                        <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{v2CompareResult.base_metrics[metric]}</td>
                        <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{v2CompareResult.hedged_metrics[metric]}</td>
                        <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>{v2CompareResult.deltas[metric]?.toFixed(2)}</td>
                        <td style={{ padding: '6px 10px', border: '1px solid #e5e7eb' }}>
                          {v2CompareResult.pct_changes[metric] != null
                            ? `${(v2CompareResult.pct_changes[metric] * 100).toFixed(1)}%`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <Button
                  className="mt-4"
                  onClick={handleBuildMemo}
                  disabled={loading}
                  data-testid="hedge-build-memo-btn"
                >
                  Build Decision Memo
                </Button>
              </Card>
            )}

            {/* Decision Memo */}
            {v2Memo && (
              <Card className="p-4" data-testid="hedge-memo-ready">
                <h3 className="font-semibold mb-3">Decision Memo</h3>
                <div
                  style={{
                    background: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    borderRadius: 6,
                    padding: 12,
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    maxHeight: 320,
                    overflowY: 'auto',
                    marginBottom: 12,
                  }}
                >
                  {v2Memo.memo_md}
                </div>
                <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: 12 }}>
                  Memo Hash: <code>{v2Memo.memo_hash}</code>
                </p>
                <div className="flex gap-3">
                  <Button
                    onClick={handleExportMd}
                    data-testid="hedge-memo-export-md"
                    variant="outline"
                  >
                    Export Markdown
                  </Button>
                  <Button
                    onClick={handleExportPack}
                    disabled={loading}
                    data-testid="hedge-memo-export-pack"
                  >
                    Export Decision Pack
                  </Button>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const HEDGE_TEMPLATES_OBJECTIVES: Record<string, string> = {
  protective_put: 'minimize_var',
  collar: 'minimize_var',
  delta_hedge: 'minimize_delta',
  duration_hedge: 'minimize_duration',
};
