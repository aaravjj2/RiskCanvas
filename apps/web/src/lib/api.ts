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

/**
 * v1.1+ Portfolio Library APIs
 */

export async function listPortfolios() {
  return apiFetch<any[]>('/portfolios', { method: 'GET' });
}

export async function createPortfolio(portfolio: any, name?: string, tags?: string[]) {
  return apiFetch<any>('/portfolios', {
    method: 'POST',
    body: JSON.stringify({ portfolio, name, tags }),
  });
}

export async function getPortfolio(portfolioId: string) {
  return apiFetch<any>(`/portfolios/${portfolioId}`, { method: 'GET' });
}

export async function deletePortfolio(portfolioId: string) {
  return apiFetch<any>(`/portfolios/${portfolioId}`, { method: 'DELETE' });
}

export async function listRuns(portfolioId?: string) {
  const query = portfolioId ? `?portfolio_id=${portfolioId}` : '';
  return apiFetch<any[]>(`/runs${query}`, { method: 'GET' });
}

export async function getRun(runId: string) {
  return apiFetch<any>(`/runs/${runId}`, { method: 'GET' });
}

export async function executeRun(portfolioId?: string, portfolio?: any, params?: any) {
  return apiFetch<any>('/runs/execute', {
    method: 'POST',
    body: JSON.stringify({ portfolio_id: portfolioId, portfolio, params }),
  });
}

export async function compareRuns(runIdA: string, runIdB: string) {
  return apiFetch<any>('/runs/compare', {
    method: 'POST',
    body: JSON.stringify({ run_id_a: runIdA, run_id_b: runIdB }),
  });
}

/**
 * v1.2+ Report Bundle APIs
 */

export async function buildReport(runId: string) {
  return apiFetch<any>('/reports/build', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId }),
  });
}

export async function getReportManifest(reportBundleId: string) {
  return apiFetch<any>(`/reports/${reportBundleId}/manifest`, { method: 'GET' });
}

/**
 * v1.3+ Hedge Studio APIs
 */

export async function suggestHedges(portfolio: any, targetReductionPct: number, maxCost?: number) {
  return apiFetch<any>('/hedge/suggest', {
    method: 'POST',
    body: JSON.stringify({
      portfolio,
      target_reduction_pct: targetReductionPct,
      max_cost: maxCost,
    }),
  });
}

export async function evaluateHedge(portfolio: any, hedgeCandidate: any) {
  return apiFetch<any>('/hedge/evaluate', {
    method: 'POST',
    body: JSON.stringify({ portfolio, hedge_candidate: hedgeCandidate }),
  });
}

/**
 * v1.4+ Workspace APIs
 */

export async function listWorkspaces(owner?: string) {
  const params = owner ? `?owner=${encodeURIComponent(owner)}` : '';
  return apiFetch<any[]>(`/workspaces${params}`, { method: 'GET' });
}

export async function createWorkspace(name: string, owner: string, tags?: string[]) {
  return apiFetch<any>('/workspaces', {
    method: 'POST',
    body: JSON.stringify({ name, owner, tags }),
  });
}

export async function getWorkspace(workspaceId: string) {
  return apiFetch<any>(`/workspaces/${workspaceId}`, { method: 'GET' });
}

export async function deleteWorkspace(workspaceId: string) {
  return apiFetch<any>(`/workspaces/${workspaceId}`, { method: 'DELETE' });
}

/**
 * v1.4+ Audit APIs
 */

export async function listAuditEvents(workspaceId?: string, actor?: string, resourceType?: string, limit?: number) {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (actor) params.append('actor', actor);
  if (resourceType) params.append('resource_type', resourceType);
  if (limit) params.append('limit', limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any[]>(`/audit${query}`, { method: 'GET' });
}

/**
 * v1.5+ DevOps APIs
 */

export async function generateRiskBotReport(basePortfolio: any, headPortfolio: any) {
  return apiFetch<any>('/devops/risk-bot', {
    method: 'POST',
    body: JSON.stringify({
      base_portfolio: basePortfolio,
      head_portfolio: headPortfolio,
    }),
  });
}

/**
 * v1.6+ Monitoring APIs
 */

export async function listMonitors(workspaceId?: string, portfolioId?: string) {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (portfolioId) params.append('portfolio_id', portfolioId);
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any[]>(`/monitors${query}`, { method: 'GET' });
}

export async function createMonitor(
  portfolioId: string,
  name: string,
  schedule: string,
  thresholds: Record<string, number>,
  workspaceId?: string,
  scenarioPreset?: any
) {
  return apiFetch<any>('/monitors', {
    method: 'POST',
    body: JSON.stringify({
      portfolio_id: portfolioId,
      name,
      schedule,
      thresholds,
      workspace_id: workspaceId,
      scenario_preset: scenarioPreset,
    }),
  });
}

export async function getMonitor(monitorId: string) {
  return apiFetch<any>(`/monitors/${monitorId}`, { method: 'GET' });
}

export async function runMonitorNow(monitorId: string) {
  return apiFetch<any>(`/monitors/${monitorId}/run-now`, { method: 'POST' });
}

export async function listAlerts(monitorId?: string, limit?: number) {
  const params = new URLSearchParams();
  if (monitorId) params.append('monitor_id', monitorId);
  if (limit) params.append('limit', limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any[]>(`/alerts${query}`, { method: 'GET' });
}

export async function listDriftSummaries(monitorId?: string, limit?: number) {
  const params = new URLSearchParams();
  if (monitorId) params.append('monitor_id', monitorId);
  if (limit) params.append('limit', limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any[]>(`/drift-summaries${query}`, { method: 'GET' });
}
