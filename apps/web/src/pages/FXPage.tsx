import { useState, useCallback } from 'react';
import { getFxSpot, getFxExposure, applyFxShocks, exportFxPack } from '@/lib/api';

const DEMO_PORTFOLIO = [
  { symbol: 'AAPL', notional_usd: 500_000 },
  { symbol: 'SAP',  notional_usd: 200_000 },
  { symbol: 'ASML', notional_usd: 150_000 },
];

export default function FXPage() {
  const [spotData, setSpotData] = useState<any>(null);
  const [exposure, setExposure] = useState<any>(null);
  const [shockResult, setShockResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pair, setPair] = useState('EURUSD');

  const loadSpot = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await getFxSpot(pair);
      if (data) setSpotData(data);
    } catch { setError('FX spot fetch failed'); }
    setLoading(false);
  }, [pair]);

  const loadExposure = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await getFxExposure(DEMO_PORTFOLIO, 'USD');
      if (data) setExposure(data);
    } catch { setError('Exposure computation failed'); }
    setLoading(false);
  }, []);

  const runShock = useCallback(async () => {
    if (!exposure) return;
    setLoading(true); setError(null);
    try {
      const data = await applyFxShocks(exposure, [{ pair: 'EURUSD', pct: -5 }, { pair: 'GBPUSD', pct: -3 }, { pair: 'JPYUSD', pct: 2 }]);
      if (data) setShockResult(data);
    } catch { setError('FX shock failed'); }
    setLoading(false);
  }, [exposure]);

  const doExport = useCallback(async () => {
    if (!exposure) return;
    setLoading(true);
    const data = await exportFxPack(DEMO_PORTFOLIO, 'USD', []);
    if (data) setExportResult(data);
    setLoading(false);
  }, [exposure]);

  return (
    <div data-testid="fx-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">FX &amp; Cross-Currency Risk</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 19   v4.26–v4.29</p>
      {error && <div data-testid="fx-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">FX Spot</h2>
        <div className="flex gap-2 mb-3">
          <input data-testid="fx-pair-input" value={pair} onChange={e => setPair(e.target.value.toUpperCase())} className="border rounded px-3 py-1 text-sm w-32" />
          <button data-testid="fx-spot-btn" onClick={loadSpot} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Get Spot</button>
        </div>
        {spotData && (
          <div data-testid="fx-spot-ready" className="bg-gray-50 rounded p-3 text-sm font-mono">
            <div>Pair: {spotData.pair}   Rate: {spotData.rate}</div>
            <div className="text-xs text-gray-400">hash: {spotData.output_hash?.slice(0, 16)}...</div>
          </div>
        )}
      </section>
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Portfolio FX Exposure</h2>
        <button data-testid="fx-exposure-btn" onClick={loadExposure} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50 mb-3">Compute Exposure</button>
        {exposure && (
          <div data-testid="fx-exposure-ready" className="bg-gray-50 rounded p-4 text-sm">
            <div className="font-mono text-xs text-gray-400">hash: {exposure.output_hash?.slice(0, 16)}...</div>
            <div className="mt-2">{exposure.exposures?.map((e: any) => <div key={e.ccy}>{e.ccy}: ${e.total_notional_usd?.toLocaleString()}</div>)}</div>
          </div>
        )}
      </section>
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">FX Shock</h2>
        <button data-testid="fx-shock-btn" onClick={runShock} disabled={loading || !exposure} className="px-3 py-1 bg-orange-600 text-white rounded text-sm disabled:opacity-50 mb-3">Apply Shocks (EUR -5%, GBP -3%, JPY +2%)</button>
        {shockResult && (
          <div data-testid="fx-shock-ready" className="bg-gray-50 rounded p-4 text-sm">
            <div>Total P&amp;L: ${shockResult.total_pnl_impact_usd?.toLocaleString()}</div>
            <div className="font-mono text-xs text-gray-400">hash: {shockResult.output_hash?.slice(0, 16)}...</div>
          </div>
        )}
      </section>
      <section>
        <button data-testid="fx-export-btn" onClick={doExport} disabled={loading || !exposure} className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Export FX Pack</button>
        {exportResult && <div data-testid="fx-export-ready" className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0, 16)}...</div>}
      </section>
    </div>
  );
}
