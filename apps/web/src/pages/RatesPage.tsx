import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { getRatesFixture, bootstrapRatesCurve, priceBondWithCurve } from '@/lib/api';

const DEFAULT_FIXTURE_TEXT = JSON.stringify([
  { type: 'deposit', tenor: 0.25, rate: 0.04 },
  { type: 'deposit', tenor: 0.5, rate: 0.042 },
  { type: 'deposit', tenor: 1.0, rate: 0.045 },
  { type: 'swap', tenor: 2.0, rate: 0.048, periods_per_year: 2 },
  { type: 'swap', tenor: 5.0, rate: 0.052, periods_per_year: 2 },
  { type: 'swap', tenor: 10.0, rate: 0.055, periods_per_year: 2 },
], null, 2);

export default function RatesPage() {
  const [instrumentsText, setInstrumentsText] = useState(DEFAULT_FIXTURE_TEXT);
  const [curveResult, setCurveResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bond price with curve
  const [bondFace, setBondFace] = useState(1000);
  const [bondCoupon, setBondCoupon] = useState(0.05);
  const [bondMaturity, setBondMaturity] = useState(5);
  const [bondPrice, setBondPrice] = useState<number | null>(null);
  const [bondLoading, setBondLoading] = useState(false);

  const handleLoadFixture = async () => {
    const fx = await getRatesFixture();
    if (fx) {
      setInstrumentsText(JSON.stringify(fx.instruments, null, 2));
    }
  };

  const handleBootstrap = async () => {
    setLoading(true);
    setError(null);
    setCurveResult(null);
    try {
      const instruments = JSON.parse(instrumentsText);
      const result = await bootstrapRatesCurve(instruments);
      setCurveResult(result);
    } catch (e: any) {
      setError(e.message || 'Failed to bootstrap curve');
    }
    setLoading(false);
  };

  const handleBondPriceWithCurve = async () => {
    if (!curveResult) return;
    setBondLoading(true);
    const result = await priceBondWithCurve({
      face_value: bondFace,
      coupon_rate: bondCoupon,
      years_to_maturity: bondMaturity,
      periods_per_year: 2,
      discount_factors: curveResult.discount_factors,
    });
    if (result) setBondPrice(result.price);
    setBondLoading(false);
  };

  return (
    <div data-testid="rates-page" className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Rates Curve</h1>
        <p className="text-gray-600 mt-1">Bootstrap zero-rate + discount-factor curve from deposit / swap instruments.</p>
      </div>

      {/* Instruments input */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <Label className="text-sm font-semibold">Instruments (JSON array)</Label>
          <Button variant="outline" size="sm" onClick={handleLoadFixture}>
            Load fixture
          </Button>
        </div>
        <textarea
          className="w-full h-40 p-2 text-xs font-mono border rounded bg-gray-50"
          value={instrumentsText}
          onChange={(e) => setInstrumentsText(e.target.value)}
          data-testid="rates-instruments-input"
        />
        {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
        <div className="flex gap-2 mt-3">
          <Button
            data-testid="rates-bootstrap-btn"
            onClick={handleBootstrap}
            disabled={loading}
          >
            {loading ? 'Bootstrapping…' : 'Bootstrap Curve'}
          </Button>
        </div>
      </Card>

      {/* Curve table */}
      {curveResult && (
        <Card className="p-4" data-testid="rates-curve-ready">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold">Zero Curve</h2>
            <span className="text-xs text-gray-500 font-mono">
              hash: {curveResult.curve_hash?.substring(0, 16)}…
            </span>
          </div>
          <table className="w-full text-xs" data-testid="rates-curve-table">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-1 pr-4">Tenor (yr)</th>
                <th className="pb-1 pr-4">Zero Rate</th>
                <th className="pb-1">Discount Factor</th>
              </tr>
            </thead>
            <tbody>
              {curveResult.zero_rates.map((item: any, i: number) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-1 pr-4">{item.tenor}</td>
                  <td className="py-1 pr-4">{(item.zero_rate * 100).toFixed(3)}%</td>
                  <td className="py-1">
                    {curveResult.discount_factors[i]?.df?.toFixed(6)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Bond price with curve */}
          <div className="mt-4 pt-4 border-t">
            <h3 className="text-sm font-semibold mb-2">Price bond using this curve</h3>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-xs">Face Value</Label>
                <input
                  type="number"
                  value={bondFace}
                  onChange={(e) => setBondFace(Number(e.target.value))}
                  className="w-full p-1 text-sm border rounded"
                  data-testid="rates-bond-face"
                />
              </div>
              <div>
                <Label className="text-xs">Coupon Rate</Label>
                <input
                  type="number"
                  step="0.001"
                  value={bondCoupon}
                  onChange={(e) => setBondCoupon(Number(e.target.value))}
                  className="w-full p-1 text-sm border rounded"
                  data-testid="rates-bond-coupon"
                />
              </div>
              <div>
                <Label className="text-xs">Years to Maturity</Label>
                <input
                  type="number"
                  step="0.5"
                  value={bondMaturity}
                  onChange={(e) => setBondMaturity(Number(e.target.value))}
                  className="w-full p-1 text-sm border rounded"
                  data-testid="rates-bond-maturity"
                />
              </div>
            </div>
            <Button
              className="mt-2"
              size="sm"
              onClick={handleBondPriceWithCurve}
              disabled={bondLoading}
              data-testid="rates-bond-price-btn"
            >
              {bondLoading ? 'Pricing…' : 'Price Bond'}
            </Button>
            {bondPrice !== null && (
              <p className="mt-2 text-sm font-semibold" data-testid="rates-bond-price-result">
                Bond Price: <span className="text-blue-700">${bondPrice.toFixed(4)}</span>
              </p>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
