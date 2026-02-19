import { useState, useCallback } from 'react';
import { getCreditCurves, computeCreditRisk, exportCreditPack } from '@/lib/api';

const DEMO_POSITIONS = [
  { symbol: 'IBM', notional: 1_000_000, duration_years: 5 },
  { symbol: 'TSLA', notional: 500_000, duration_years: 3 },
];

export default function CreditPage() {
  const [curves, setCurves] = useState<any>(null);
  const [riskResult, setRiskResult] = useState<any>(null);
  const [exportResult, setExportResult] = useState<any>(null);
  const [selectedCurve, setSelectedCurve] = useState('usd_ig');
  const [shockBps, setShockBps] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCurves = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await getCreditCurves(); if (data) setCurves(data); }
    catch { setError('Curve fetch failed'); }
    setLoading(false);
  }, []);

  const computeRisk = useCallback(async () => {
    setLoading(true); setError(null);
    try { const data = await computeCreditRisk(DEMO_POSITIONS, selectedCurve, shockBps); if (data) setRiskResult(data); }
    catch { setError('Credit risk computation failed'); }
    setLoading(false);
  }, [selectedCurve, shockBps]);

  const doExport = useCallback(async () => {
    if (!riskResult) return;
    setLoading(true);
    const data = await exportCreditPack(DEMO_POSITIONS, selectedCurve, shockBps);
    if (data) setExportResult(data);
    setLoading(false);
  }, [riskResult, selectedCurve, shockBps]);

  return (
    <div data-testid="credit-page" className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Credit &amp; Spread Risk</h1>
      <p className="text-gray-500 mb-6 text-sm">Wave 20   v4.30–v4.33</p>
      {error && <div data-testid="credit-error" className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Spread Curves</h2>
        <button data-testid="credit-curves-btn" onClick={loadCurves} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50 mb-3">Load Curves</button>
        {curves && (
          <div data-testid="credit-curve-ready" className="bg-gray-50 rounded p-4 text-sm">
            <div className="flex gap-2 flex-wrap">
              {curves.curves?.map((c: any) => (
                <button key={c.curve_id} onClick={() => setSelectedCurve(c.curve_id)}
                  className={`px-3 py-1 rounded text-xs border ${selectedCurve === c.curve_id ? 'bg-blue-600 text-white border-blue-600' : 'bg-white border-gray-300'}`}>
                  {c.curve_id}
                </button>
              ))}
            </div>
            <div className="font-mono text-xs text-gray-400 mt-2">hash: {curves.output_hash?.slice(0, 16)}...</div>
          </div>
        )}
      </section>
      <section className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Credit Risk</h2>
        <div className="flex gap-3 mb-3 items-center">
          <label className="text-sm text-gray-600">Shock (bps):</label>
          <input data-testid="credit-shock-input" type="number" value={shockBps} onChange={e => setShockBps(Number(e.target.value))} className="border rounded px-2 py-1 text-sm w-24" />
          <button data-testid="credit-risk-btn" onClick={computeRisk} disabled={loading} className="px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:opacity-50">Compute Risk</button>
        </div>
        {riskResult && (
          <div data-testid="credit-risk-ready" className="bg-gray-50 rounded p-4 text-sm">
            <div className="font-semibold mb-2">Total DV01: ${riskResult.total_dv01?.toLocaleString()}   Shock P&L: ${riskResult.shock_pnl?.toLocaleString()}</div>
            <div className="font-mono text-xs text-gray-400">hash: {riskResult.output_hash?.slice(0, 16)}...</div>
          </div>
        )}
      </section>
      <section>
        <button data-testid="credit-export-btn" onClick={doExport} disabled={loading || !riskResult} className="px-3 py-1 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Export Credit Risk Pack</button>
        {exportResult && <div data-testid="credit-export-ready" className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono">pack_hash: {exportResult.pack_hash?.slice(0, 16)}...</div>}
      </section>
    </div>
  );
}
