import { useState, useCallback } from 'react';
import { computeHaircut, estimateTcost, computeTradeoff, exportLiquidityPack } from '@/lib/api';

const DEMO_PORTFOLIO = [
  { symbol: 'AAPL', notional_usd: 1_000_000 },
  { symbol: 'SPY',  notional_usd: 500_000 },
  { symbol: 'HYG',  notional_usd: 300_000 },
];
const DEMO_TRADES = [
  { symbol: 'AAPL', notional_usd: 200_000, side: 'sell' },
  { symbol: 'HYG',  notional_usd: 150_000, side: 'sell' },
];

export default function LiquidityPage() {
  const [haircutResult, setHaircutResult] = useState<any>(null);
  const [tcostResult, setTcostResult] = useState<any>(null);
  const [tradeoffResult, setTradeoffResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHaircut = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await computeHaircut(DEMO_PORTFOLIO); if (data) setHaircutResult(data); }
    catch { setError('Haircut computation failed'); }
    setLoading(false);
  }, []);

  const loadTcost = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await estimateTcost(DEMO_TRADES); if (data) setTcostResult(data); }
    catch { setError('TCost estimation failed'); }
    setLoading(false);
  }, []);

  const loadTradeoff = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await computeTradeoff([{ symbol: 'SPY', notional_usd: 100_000, side: 'buy' }], 500_000); if (data) setTradeoffResult(data); }
    catch { setError('Tradeoff computation failed'); }
    setLoading(false);
  }, []);

  const doExport = useCallback(async () => {
    if (!haircutResult) return;
    setLoading(true);
    const data = await exportLiquidityPack(DEMO_PORTFOLIO, DEMO_TRADES);
    if (data) setExportResult(data);
    setLoading(false);
  }, [haircutResult]);

  return (
    <div data-testid="liq-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Liquidity &amp; Transaction Costs</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 21   v4.34–v4.37</p>
      {error && <div data-testid="liq-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <div className="flex gap-3 mb-6">
        <button data-testid="liq-haircut-btn" onClick={loadHaircut} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Compute Haircuts</button>
        <button data-testid="liq-tcost-btn" onClick={loadTcost} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Estimate T-Costs</button>
        <button data-testid="liq-tradeoff-btn" onClick={loadTradeoff} disabled={loading} className="px-3 py-1 bg-orange-600 text-white rounded text-sm disabled:opacity-50">Hedge Tradeoff</button>
      </div>
      {(haircutResult || tcostResult || tradeoffResult) && (
        <div data-testid="liq-ready" className="space-y-4">
          {haircutResult && (
            <div className="bg-gray-50 rounded p-4 text-sm">
              <div className="font-semibold">Net Liquid Value: ${haircutResult.net_liquid_value_usd?.toLocaleString()}</div>
              <div className="font-mono text-xs text-gray-400 mt-1">hash: {haircutResult.output_hash?.slice(0, 16)}...</div>
            </div>
          )}
          {tcostResult && (
            <div className="bg-gray-50 rounded p-4 text-sm">
              <div className="font-semibold">Total TCost: ${tcostResult.total_cost_usd?.toLocaleString()}</div>
              <div className="font-mono text-xs text-gray-400 mt-1">hash: {tcostResult.output_hash?.slice(0, 16)}...</div>
            </div>
          )}
          {tradeoffResult && (
            <div className="bg-gray-50 rounded p-4 text-sm">
              <div className="font-semibold">Recommendation: {tradeoffResult.recommendation}</div>
              <div className="font-mono text-xs text-gray-400 mt-1">hash: {tradeoffResult.output_hash?.slice(0, 16)}...</div>
            </div>
          )}
        </div>
      )}
      <div className="mt-6">
        <button data-testid="liq-export-btn" onClick={doExport} disabled={loading || !haircutResult} className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Export Liquidity Pack</button>
        {exportResult && <div data-testid="liq-export-ready" className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0, 16)}...</div>}
      </div>
    </div>
  );
}
