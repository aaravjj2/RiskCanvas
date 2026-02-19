import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { listStressPresets, getStressPreset, applyStressPreset, compareRunsV2 } from '@/lib/api';
import { executeRun } from '@/lib/api';

const DEMO_PORTFOLIO = {
  assets: [
    { asset_id: 'AAPL', asset_type: 'stock', quantity: 100, current_price: 175.0 },
    {
      asset_id: 'BOND_10Y',
      asset_type: 'bond',
      face_value: 10000,
      coupon_rate: 0.045,
      yield_to_maturity: 0.05,
      years_to_maturity: 10,
    },
    {
      asset_id: 'AAPL_OPT',
      asset_type: 'option',
      quantity: 10,
      price: 8.5,
      strike: 180,
      maturity: 0.5,
      volatility: 0.25,
      risk_free_rate: 0.05,
      option_type: 'call',
    },
  ],
};

interface Preset {
  id: string;
  label: string;
  description: string;
  preset_hash: string;
}

interface StressedResult {
  presetId: string;
  presetLabel: string;
  runResult: any;
  stressedPortfolio: any;
}

export default function StressPage() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [stressedResult, setStressedResult] = useState<StressedResult | null>(null);
  const [baseline, setBaseline] = useState<any>(null);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listStressPresets().then((data) => {
      if (data) setPresets(data.presets ?? data);
    });
  }, []);

  const handleRunStress = async () => {
    if (!selectedPreset) return;
    setRunning(true);
    setError(null);
    setStressedResult(null);
    setCompareResult(null);
    try {
      // 1. Get baseline run (if not already done)
      let base = baseline;
      if (!base) {
        base = await executeRun(undefined, DEMO_PORTFOLIO);
        setBaseline(base);
      }

      // 2. Apply stress preset
      const stressed = await applyStressPreset(selectedPreset, DEMO_PORTFOLIO);
      if (!stressed) throw new Error('Stress apply failed');

      // 3. Run analysis on stressed portfolio
      const stressedRun = await executeRun(undefined, { assets: stressed.stressed_portfolio?.assets ?? DEMO_PORTFOLIO.assets });

      const preset = await getStressPreset(selectedPreset);

      setStressedResult({
        presetId: selectedPreset,
        presetLabel: preset?.label ?? selectedPreset,
        runResult: stressedRun,
        stressedPortfolio: stressed,
      });

      // 4. Compare
      if (base && stressedRun) {
        const comparison = await compareRunsV2(
          {
            run_id: base.run_id ?? 'baseline',
            portfolio_value: base.portfolio_value,
            total_pnl: base.total_pnl,
            var_95: base.var_95,
            var_99: base.var_99,
            delta: base.delta,
            duration: base.duration,
          },
          {
            run_id: stressedRun.run_id ?? 'stressed',
            portfolio_value: stressedRun.portfolio_value,
            total_pnl: stressedRun.total_pnl,
            var_95: stressedRun.var_95,
            var_99: stressedRun.var_99,
            delta: stressedRun.delta,
            duration: stressedRun.duration,
          }
        );
        setCompareResult(comparison);
      }
    } catch (e: any) {
      setError(e.message || 'Stress run failed');
    }
    setRunning(false);
  };

  const deltaColor = (v: number | null) => {
    if (v === null || v === undefined) return 'text-gray-400';
    if (v < 0) return 'text-red-600';
    if (v > 0) return 'text-green-600';
    return 'text-gray-700';
  };

  return (
    <div data-testid="stress-page" className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Stress Library</h1>
        <p className="text-gray-600 mt-1">Select a canonical stress scenario and execute against the demo portfolio.</p>
      </div>

      {/* Preset cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {presets.map((p) => (
          <Card
            key={p.id}
            className={`p-4 cursor-pointer border-2 transition-colors ${
              selectedPreset === p.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-400'
            }`}
            data-testid={`stress-preset-${p.id}`}
            onClick={() => setSelectedPreset(p.id)}
          >
            <div className="font-semibold text-sm">{p.label}</div>
            <div className="text-xs text-gray-500 mt-1">{p.description}</div>
            <div className="text-xs font-mono text-gray-400 mt-2 truncate">
              {p.preset_hash?.substring(0, 12)}...
            </div>
          </Card>
        ))}
      </div>

      {selectedPreset && (
        <div className="flex gap-3 items-center">
          <Button
            data-testid="stress-run-btn"
            onClick={handleRunStress}
            disabled={running}
          >
            {running ? 'Running stress analysis...' : `Run: ${selectedPreset}`}
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              setBaseline(null);
              setStressedResult(null);
              setCompareResult(null);
            }}
          >
            Reset baseline
          </Button>
        </div>
      )}

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {/* Stressed result */}
      {stressedResult && (
        <Card className="p-4" data-testid="stress-run-complete">
          <h2 className="text-sm font-semibold mb-3">
            Stress Result - {stressedResult.presetLabel}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-xs text-gray-500">Portfolio Value</div>
              <div className="font-mono font-semibold">
                ${stressedResult.runResult?.portfolio_value?.toFixed(2) ?? 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">VaR 95</div>
              <div className="font-mono font-semibold">
                ${stressedResult.runResult?.var_95?.toFixed(2) ?? 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">VaR 99</div>
              <div className="font-mono font-semibold">
                ${stressedResult.runResult?.var_99?.toFixed(2) ?? 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Total P&L</div>
              <div className="font-mono font-semibold">
                ${stressedResult.runResult?.total_pnl?.toFixed(2) ?? 'N/A'}
              </div>
            </div>
          </div>
          <div className="text-xs text-gray-400 mt-2 font-mono">
            shocks applied: {stressedResult.stressedPortfolio?.shocks_applied ?? 0}
          </div>
        </Card>
      )}

      {/* Delta compare table */}
      {compareResult && (
        <Card className="p-4">
          <h2 className="text-sm font-semibold mb-3">Baseline vs Stress Delta</h2>
          <table className="w-full text-xs" data-testid="stress-delta-table">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-1 pr-4">Metric</th>
                <th className="pb-1 pr-4">Baseline</th>
                <th className="pb-1 pr-4">Stressed</th>
                <th className="pb-1">Delta</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Portfolio Value', key: 'delta_portfolio_value', baseKey: 'portfolio_value', stressKey: 'portfolio_value' },
                { label: 'VaR 95', key: 'delta_var_95', baseKey: 'var_95', stressKey: 'var_95' },
                { label: 'VaR 99', key: 'delta_var_99', baseKey: 'var_99', stressKey: 'var_99' },
                { label: 'P&L', key: 'delta_pnl', baseKey: 'total_pnl', stressKey: 'total_pnl' },
              ].map(({ label, key }) => (
                <tr key={key} className="border-b last:border-0">
                  <td className="py-1 pr-4 text-gray-600">{label}</td>
                  <td className="py-1 pr-4 font-mono">
                    {baseline?.[key.replace('delta_', '').replace('delta_pnl', 'total_pnl')]?.toFixed(2) ?? 'N/A'}
                  </td>
                  <td className="py-1 pr-4 font-mono">
                    {stressedResult?.runResult?.[key.replace('delta_', '').replace('delta_pnl', 'total_pnl')]?.toFixed(2) ?? 'N/A'}
                  </td>
                  <td className={`py-1 font-mono font-semibold ${deltaColor(compareResult[key])}`}>
                    {compareResult[key] != null ? compareResult[key].toFixed(4) : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 text-xs text-gray-500">{compareResult.summary}</div>
        </Card>
      )}
    </div>
  );
}
