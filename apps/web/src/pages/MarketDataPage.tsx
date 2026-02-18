import { useState, useCallback } from 'react';
import {
  getMarketAsof,
  getMarketSpot,
  postMarketSeries,
  getMarketCurve,
} from '../lib/api';

interface SpotData {
  symbol: string;
  price: number;
  asof: string;
  provider: string;
  output_hash: string;
}

interface SeriesEntry {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface SeriesData {
  symbol: string;
  freq: string;
  count: number;
  series: SeriesEntry[];
  output_hash: string;
  asof: string;
}

interface CurvePoint {
  tenor: string;
  tenor_years: number;
  rate: number;
}

interface CurveData {
  curve_id: string;
  currency: string;
  count: number;
  points: CurvePoint[];
  output_hash: string;
  asof: string;
}

export default function MarketDataPage() {
  const [asof, setAsof] = useState<string>('');
  const [provider, setProvider] = useState<string>('');
  const [asofHash, setAsofHash] = useState<string>('');

  const [spotSymbol, setSpotSymbol] = useState('AAPL');
  const [spotData, setSpotData] = useState<SpotData | null>(null);
  const [spotReady, setSpotReady] = useState(false);

  const [seriesSymbol, setSeriesSymbol] = useState('AAPL');
  const [seriesData, setSeriesData] = useState<SeriesData | null>(null);
  const [seriesReady, setSeriesReady] = useState(false);

  const [curveId, setCurveId] = useState('USD_SOFR');
  const [curveData, setCurveData] = useState<CurveData | null>(null);
  const [curveReady, setCurveReady] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAsof = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getMarketAsof();
      if (result) {
        setAsof(result.asof ?? '');
        setProvider(result.provider ?? '');
        setAsofHash(result.output_hash ?? '');
      }
    } catch (e) {
      setError('Failed to load as-of date');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSpot = useCallback(async () => {
    if (!spotSymbol.trim()) return;
    setLoading(true);
    setError(null);
    setSpotReady(false);
    try {
      const result = await getMarketSpot(spotSymbol.trim().toUpperCase());
      if (result) {
        setSpotData(result as SpotData);
        setSpotReady(true);
      } else {
        setError(`Symbol not found: ${spotSymbol}`);
      }
    } catch (e) {
      setError('Failed to load spot price');
    } finally {
      setLoading(false);
    }
  }, [spotSymbol]);

  const loadSeries = useCallback(async () => {
    if (!seriesSymbol.trim()) return;
    setLoading(true);
    setError(null);
    setSeriesReady(false);
    try {
      const result = await postMarketSeries({ symbol: seriesSymbol.trim().toUpperCase() });
      if (result) {
        setSeriesData(result as SeriesData);
        setSeriesReady(true);
      } else {
        setError(`No series available for: ${seriesSymbol}`);
      }
    } catch (e) {
      setError('Failed to load series');
    } finally {
      setLoading(false);
    }
  }, [seriesSymbol]);

  const loadCurve = useCallback(async () => {
    if (!curveId.trim()) return;
    setLoading(true);
    setError(null);
    setCurveReady(false);
    try {
      const result = await getMarketCurve(curveId.trim());
      if (result) {
        setCurveData(result as CurveData);
        setCurveReady(true);
      } else {
        setError(`Curve not found: ${curveId}`);
      }
    } catch (e) {
      setError('Failed to load curve');
    } finally {
      setLoading(false);
    }
  }, [curveId]);

  return (
    <div data-testid="market-page" style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px' }}>
        Market Data
      </h1>
      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Deterministic market data provider — fixture-backed, audit-safe, no external calls.
      </p>

      {error && (
        <div style={{ background: '#fee2e2', color: '#b91c1c', padding: '10px 16px', borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* As-Of Panel */}
      <section
        style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20, marginBottom: 24 }}
      >
        <h2 style={{ fontWeight: 600, marginBottom: 12 }}>Market As-Of Date</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <button
            onClick={loadAsof}
            disabled={loading}
            style={{
              background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6,
              padding: '8px 20px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600,
            }}
          >
            Load As-Of
          </button>
          {asof && (
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              <span>
                <strong>As-Of:</strong>{' '}
                <span data-testid="market-asof">{asof}</span>
              </span>
              <span>
                <strong>Provider:</strong>{' '}
                <span data-testid="market-provider">{provider}</span>
              </span>
              <span>
                <strong>Hash:</strong>{' '}
                <code style={{ fontSize: '12px', background: '#e5e7eb', padding: '2px 6px', borderRadius: 4 }}>
                  {asofHash}
                </code>
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Spot Lookup */}
      <section
        style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20, marginBottom: 24 }}
      >
        <h2 style={{ fontWeight: 600, marginBottom: 12 }}>Spot Price Lookup</h2>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <input
            value={spotSymbol}
            onChange={e => setSpotSymbol(e.target.value)}
            placeholder="Symbol (e.g. AAPL)"
            data-testid="market-spot-symbol-input"
            style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 12px', fontFamily: 'inherit' }}
          />
          <button
            onClick={loadSpot}
            disabled={loading}
            style={{
              background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6,
              padding: '8px 20px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600,
            }}
          >
            Get Spot
          </button>
        </div>

        {spotReady && spotData && (
          <div data-testid="market-spot-ready">
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  <th style={{ padding: '8px 16px', textAlign: 'left', border: '1px solid #e5e7eb' }}>Symbol</th>
                  <th style={{ padding: '8px 16px', textAlign: 'left', border: '1px solid #e5e7eb' }}>Price</th>
                  <th style={{ padding: '8px 16px', textAlign: 'left', border: '1px solid #e5e7eb' }}>Provider</th>
                  <th style={{ padding: '8px 16px', textAlign: 'left', border: '1px solid #e5e7eb' }}>Hash</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '8px 16px', border: '1px solid #e5e7eb' }}>{spotData.symbol}</td>
                  <td style={{ padding: '8px 16px', border: '1px solid #e5e7eb' }}>
                    <strong>${spotData.price.toLocaleString()}</strong>
                  </td>
                  <td style={{ padding: '8px 16px', border: '1px solid #e5e7eb' }}>{spotData.provider}</td>
                  <td style={{ padding: '8px 16px', border: '1px solid #e5e7eb' }}>
                    <code style={{ fontSize: '12px' }}>{spotData.output_hash}</code>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Series Viewer */}
      <section
        style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20, marginBottom: 24 }}
      >
        <h2 style={{ fontWeight: 600, marginBottom: 12 }}>OHLCV Series</h2>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <input
            value={seriesSymbol}
            onChange={e => setSeriesSymbol(e.target.value)}
            placeholder="Symbol (e.g. AAPL)"
            data-testid="market-series-symbol-input"
            style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 12px', fontFamily: 'inherit' }}
          />
          <button
            onClick={loadSeries}
            disabled={loading}
            style={{
              background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6,
              padding: '8px 20px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600,
            }}
          >
            Load Series
          </button>
        </div>

        {seriesReady && seriesData && (
          <div data-testid="market-series-ready">
            <p style={{ color: '#6b7280', marginBottom: 8 }}>
              {seriesData.count} candles · {seriesData.freq} · Provider hash:{' '}
              <code style={{ fontSize: '12px' }}>{seriesData.output_hash}</code>
            </p>
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  {['Date', 'Open', 'High', 'Low', 'Close', 'Volume'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', border: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {seriesData.series.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>{row.date}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>${row.open.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>${row.high.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>${row.low.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>${row.close.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>{row.volume.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Rates Curve */}
      <section
        style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}
      >
        <h2 style={{ fontWeight: 600, marginBottom: 12 }}>Interest Rate Curve</h2>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <input
            value={curveId}
            onChange={e => setCurveId(e.target.value)}
            placeholder="Curve ID (e.g. USD_SOFR)"
            data-testid="market-curve-id-input"
            style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 12px', fontFamily: 'inherit' }}
          />
          <button
            onClick={loadCurve}
            disabled={loading}
            style={{
              background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6,
              padding: '8px 20px', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600,
            }}
          >
            Load Curve
          </button>
        </div>

        {curveReady && curveData && (
          <div data-testid="market-curve-ready">
            <p style={{ color: '#6b7280', marginBottom: 8 }}>
              {curveData.currency} · {curveData.count} tenors · Hash:{' '}
              <code style={{ fontSize: '12px' }}>{curveData.output_hash}</code>
            </p>
            <table style={{ borderCollapse: 'collapse', width: '100%' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  {['Tenor', 'Years', 'Rate (%)'].map(h => (
                    <th key={h} style={{ padding: '8px 12px', textAlign: 'left', border: '1px solid #e5e7eb' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {curveData.points.map((pt, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>{pt.tenor}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>{pt.tenor_years.toFixed(2)}</td>
                    <td style={{ padding: '6px 12px', border: '1px solid #e5e7eb' }}>{(pt.rate * 100).toFixed(3)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
