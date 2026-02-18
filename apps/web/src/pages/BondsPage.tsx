import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  calculateBondPrice,
  calculateBondYield,
  calculateBondRiskMetrics,
} from '@/lib/api';

export default function BondsPage() {
  const [faceValue, setFaceValue] = useState(1000);
  const [couponRate, setCouponRate] = useState(0.05);
  const [yearsToMaturity, setYearsToMaturity] = useState(5);
  const [yieldToMaturity, setYieldToMaturity] = useState(0.06);
  const [price, setPrice] = useState(0);
  const [periodsPerYear] = useState(2);
  
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCalculatePrice = async () => {
    setLoading(true);
    const result = await calculateBondPrice({
      face_value: faceValue,
      coupon_rate: couponRate,
      years_to_maturity: yearsToMaturity,
      yield_to_maturity: yieldToMaturity,
      periods_per_year: periodsPerYear,
    });
    
    if (result) {
      setResults({ type: 'price', data: result });
    }
    setLoading(false);
  };

  const handleCalculateYield = async () => {
    if (price <= 0) {
      alert('Please enter a valid bond price');
      return;
    }
    
    setLoading(true);
    const result = await calculateBondYield({
      face_value: faceValue,
      coupon_rate: couponRate,
      years_to_maturity: yearsToMaturity,
      price: price,
      periods_per_year: periodsPerYear,
    });
    
    if (result) {
      setResults({ type: 'yield', data: result });
    }
    setLoading(false);
  };

  const handleCalculateRisk = async () => {
    setLoading(true);
    const result = await calculateBondRiskMetrics({
      face_value: faceValue,
      coupon_rate: couponRate,
      years_to_maturity: yearsToMaturity,
      yield_to_maturity: yieldToMaturity,
      periods_per_year: periodsPerYear,
    });
    
    if (result) {
      setResults({ type: 'risk', data: result });
    }
    setLoading(false);
  };

  return (
    <div className="p-4 space-y-4" data-testid="bonds-page">
      <h1 className="text-2xl font-bold">Bond Analytics</h1>

      <Card className="p-4">
        <h2 className="text-xl font-semibold mb-4">Bond Parameters</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="faceValue">Face Value ($)</Label>
            <Input
              id="faceValue"
              data-testid="face-value-input"
              type="number"
              value={faceValue}
              onChange={(e) => setFaceValue(parseFloat(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="couponRate">Coupon Rate (decimal)</Label>
            <Input
              id="couponRate"
              data-testid="coupon-rate-input"
              type="number"
              step="0.001"
              value={couponRate}
              onChange={(e) => setCouponRate(parseFloat(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="yearsToMaturity">Years to Maturity</Label>
            <Input
              id="yearsToMaturity"
              data-testid="years-to-maturity-input"
              type="number"
              step="0.5"
              value={yearsToMaturity}
              onChange={(e) => setYearsToMaturity(parseFloat(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="yieldToMaturity">Yield to Maturity (decimal)</Label>
            <Input
              id="yieldToMaturity"
              data-testid="yield-to-maturity-input"
              type="number"
              step="0.001"
              value={yieldToMaturity}
              onChange={(e) => setYieldToMaturity(parseFloat(e.target.value))}
            />
          </div>
          <div>
            <Label htmlFor="price">Current Price ($, for yield calc)</Label>
            <Input
              id="price"
              data-testid="price-input"
              type="number"
              value={price}
              onChange={(e) => setPrice(parseFloat(e.target.value))}
            />
          </div>
        </div>

        <div className="flex gap-3 mt-4">
          <Button onClick={handleCalculatePrice} disabled={loading} data-testid="calc-price-btn">
            {loading ? 'Calculating...' : 'Calculate Price'}
          </Button>
          <Button onClick={handleCalculateYield} disabled={loading} data-testid="calc-yield-btn">
            {loading ? 'Calculating...' : 'Calculate Yield'}
          </Button>
          <Button onClick={handleCalculateRisk} disabled={loading} data-testid="calc-risk-btn">
            {loading ? 'Calculating...' : 'Calculate Risk Metrics'}
          </Button>
        </div>
      </Card>

      {results && (
        <Card className="p-4" data-testid="bond-results">
          <h2 className="text-xl font-semibold mb-4">Results</h2>
          {results.type === 'price' && (
            <div>
              <p className="text-lg">Bond Price: <span className="font-bold">${results.data.price.toFixed(2)}</span></p>
            </div>
          )}
          {results.type === 'yield' && (
            <div>
              <p className="text-lg">Yield to Maturity: <span className="font-bold">{(results.data.yield_to_maturity * 100).toFixed(2)}%</span></p>
            </div>
          )}
          {results.type === 'risk' && (
            <div className="space-y-2">
              <p className="text-lg">Price: <span className="font-bold">${results.data.price.toFixed(2)}</span></p>
              <p className="text-lg">Duration: <span className="font-bold">{results.data.duration.toFixed(2)} years</span></p>
              <p className="text-lg">Modified Duration: <span className="font-bold">{results.data.modified_duration.toFixed(2)}</span></p>
              <p className="text-lg">Convexity: <span className="font-bold">{results.data.convexity.toFixed(2)}</span></p>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
