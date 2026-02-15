import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { suggestHedges, evaluateHedge, compareRuns } from '@/lib/api';
import { useNavigate } from 'react-router-dom';

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

  const handleGenerateHedges = async () => {
    if (!portfolioId) {
      alert('Please enter a Portfolio ID');
      return;
    }

    setLoading(true);
    const result = await suggestHedges({
      portfolio_id: portfolioId,
      target_var_reduction_pct: targetReduction,
      max_cost: maxCost,
      instrument_types: Object.keys(instrumentTypes).filter((k) => instrumentTypes[k as keyof typeof instrumentTypes]),
    });

    if (result) {
      setHedges(result.hedges || []);
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
      // Compare original vs hedged
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

          {hedges.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              <p>Configure parameters and click "Generate Hedges" to see suggestions</p>
            </div>
          )}

          <div className="space-y-4" data-testid="hedges-list">
            {hedges.map((hedge, idx) => (
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
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
