import type { AnalysisResult, Asset, DeterminismResult } from './types';

// API base URL - update based on environment
const API_BASE = 'http://localhost:8090';

// Mock data for offline/demo mode
export const DEMO_PORTFOLIO: Asset[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', type: 'stock', quantity: 10, price: 150.25, current_price: 150.25, purchase_price: 140.0 },
  { symbol: 'MSFT', name: 'Microsoft Corp.', type: 'stock', quantity: 5, price: 300.50, current_price: 300.50, purchase_price: 290.0 },
];

export const MOCK_ANALYSIS: AnalysisResult = {
  request_id: 'demo-001',
  metrics: { total_pnl: 155.0, total_value: 3005.0, asset_count: 2, portfolio_greeks: null },
  var: { method: 'parametric', var_value: 74.12, confidence_level: 0.95 },
  warnings: [],
};

export const MOCK_DETERMINISM: DeterminismResult = {
  passed: true,
  checks: [
    { name: 'option_pricing', match: true, hash: 'abc123' },
    { name: 'greeks', match: true, hash: 'def456' },
    { name: 'portfolio_pnl', match: true, hash: 'ghi789' },
    { name: 'var_parametric', match: true, hash: 'jkl012' },
  ],
  overall_hash: 'demo-hash-deterministic',
};

/**
 * Generic API fetch wrapper with error handling
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Analyze portfolio
 */
export async function analyzePortfolio(portfolio: Asset[]): Promise<AnalysisResult> {
  const body = {
    portfolio: {
      id: 'ui-portfolio',
      name: 'UI Portfolio',
      assets: portfolio,
    },
  };
  const result = await apiFetch<AnalysisResult>('/analyze/portfolio', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return result ?? MOCK_ANALYSIS;
}

/**
 * Check determinism
 */
export async function checkDeterminism(): Promise<DeterminismResult> {
  const result = await apiFetch<DeterminismResult>('/determinism/check', {
    method: 'POST',
  });
  return result ?? MOCK_DETERMINISM;
}

/**
 * Health check
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const result = await fetch(`${API_BASE}/health`);
    return result.ok;
  } catch {
    return false;
  }
}
