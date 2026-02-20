import type { AnalysisResult, Asset, DeterminismResult } from './types';
import { getAuthHeaders } from './config';

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
 * Fetch with timeout using AbortController
 */
async function fetchWithTimeout(url: string, init?: RequestInit, timeoutMs: number = 10000): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...init,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  }
}

/**
 * Generic API fetch wrapper with error handling and timeout
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    console.log(`[API] ${init?.method || 'GET'} ${path}`);
    const res = await fetchWithTimeout(`${API_BASE}${path}`, {
      ...init,
      headers: { 
        'Content-Type': 'application/json',
        ...getAuthHeaders(), // Add auth/demo headers based on mode
        ...(init?.headers || {}),
      },
    }, 15000); // 15 second timeout
    console.log(`[API] ${init?.method || 'GET'} ${path} => ${res.status}`);
    if (!res.ok) {
      console.error(`[API] ${path} failed: ${res.status} ${res.statusText}`);
      return null;
    }
    return (await res.json()) as T;
  } catch (error) {
    console.error(`[API] ${path} error:`, error);
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

export async function listRuns(filters?: { portfolio_id?: string }) {
  const query = filters?.portfolio_id ? `?portfolio_id=${filters.portfolio_id}` : '';
  return apiFetch<any>(`/runs${query}`, { method: 'GET' });
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

export async function listReports(filters?: { portfolio_id?: string; run_id?: string }) {
  const params = new URLSearchParams();
  if (filters?.portfolio_id) params.append('portfolio_id', filters.portfolio_id);
  if (filters?.run_id) params.append('run_id', filters.run_id);
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/reports${query}`, { method: 'GET' });
}

export async function buildReport(runId: string) {
  return apiFetch<any>('/reports/build', {
    method: 'POST',
    body: JSON.stringify({ run_id: runId }),
  });
}

// Alias for backwards compatibility
export const buildReportBundle = (params: { run_id: string }) => buildReport(params.run_id);

export async function getReportManifest(reportBundleId: string) {
  return apiFetch<any>(`/reports/${reportBundleId}/manifest`, { method: 'GET' });
}

/**
 * v1.3+ Hedge Studio APIs
 */

export async function suggestHedges(params: { portfolio_id: string; target_reduction_pct: number; max_cost: number; allowed_instruments?: string[] }) {
  return apiFetch<any>('/hedge/suggest', {
    method: 'POST',
    body: JSON.stringify({
      portfolio_id: params.portfolio_id,
      target_reduction_pct: params.target_reduction_pct,
      max_cost: params.max_cost,
      allowed_instruments: params.allowed_instruments || ['put_option', 'call_option'],
    }),
  });
}

export async function evaluateHedge(params: { portfolio_id: string; hedge_instruments: any[] }) {
  return apiFetch<any>('/hedge/evaluate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * v1.4+ Workspace APIs
 */

export async function listWorkspaces(owner?: string) {
  const params = owner ? `?owner=${encodeURIComponent(owner)}` : '';
  return apiFetch<any>(`/workspaces${params}`, { method: 'GET' });
}

export async function createWorkspace(params: { name: string; owner: string; tags?: string[] }) {
  return apiFetch<any>('/workspaces', {
    method: 'POST',
    body: JSON.stringify(params),
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

export async function listAuditEvents(filters?: { workspace_id?: string; actor?: string; resource_type?: string; limit?: number }) {
  const params = new URLSearchParams();
  if (filters?.workspace_id) params.append('workspace_id', filters.workspace_id);
  if (filters?.actor) params.append('actor', filters.actor);
  if (filters?.resource_type) params.append('resource_type', filters.resource_type);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/audit${query}`, { method: 'GET' });
}

/**
 * v1.5+ DevOps APIs
 */

export async function generateRiskBotReport(params: { scope: string; include_hashes: boolean }) {
  return apiFetch<any>('/devops/risk-bot', {
    method: 'POST',
    body: JSON.stringify(params),
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
  return apiFetch<any>(`/monitors${query}`, { method: 'GET' });
}

export async function createMonitor(params: {
  portfolio_id: string;
  name: string;
  schedule: string;
  thresholds: Record<string, number>;
  workspace_id?: string;
  scenario_preset?: any;
}) {
  return apiFetch<any>('/monitors', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getMonitor(monitorId: string) {
  return apiFetch<any>(`/monitors/${monitorId}`, { method: 'GET' });
}

export async function runMonitorNow(monitorId: string, params?: any) {
  return apiFetch<any>(`/monitors/${monitorId}/run-now`, { 
    method: 'POST',
    body: JSON.stringify(params || {}),
  });
}

export async function listAlerts(filters?: { monitor_id?: string; limit?: number }) {
  const params = new URLSearchParams();
  if (filters?.monitor_id) params.append('monitor_id', filters.monitor_id);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/alerts${query}`, { method: 'GET' });
}

export async function listDriftSummaries(filters?: { monitor_id?: string; limit?: number }) {
  const params = new URLSearchParams();
  if (filters?.monitor_id) params.append('monitor_id', filters.monitor_id);
  if (filters?.limit) params.append('limit', filters.limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/drift-summaries${query}`, { method: 'GET' });
}

// === v1.7 Governance ===

export async function createAgentConfig(params: {
  name: string;
  model: string;
  provider: string;
  system_prompt: string;
  tool_policies: Record<string, any>;
  thresholds: Record<string, any>;
  tags?: string[];
}) {
  return apiFetch<any>('/governance/configs', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function listAgentConfigs() {
  return apiFetch<any>('/governance/configs', { method: 'GET' });
}

export async function getAgentConfig(configId: string) {
  return apiFetch<any>(`/governance/configs/${configId}`, { method: 'GET' });
}

export async function activateAgentConfig(params: { config_id: string }) {
  return apiFetch<any>('/governance/configs/activate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function runEvalHarness(params: { config_id: string }) {
  return apiFetch<any>('/governance/evals/run', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function listEvalReports(filters?: { config_id?: string }) {
  const params = new URLSearchParams();
  if (filters?.config_id) params.append('config_id', filters.config_id);
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/governance/evals${query}`, { method: 'GET' });
}

export async function getEvalReport(reportId: string) {
  return apiFetch<any>(`/governance/evals/${reportId}`, { method: 'GET' });
}

// === v1.8 Bonds ===

export async function calculateBondPrice(params: {
  face_value: number;
  coupon_rate: number;
  years_to_maturity: number;
  yield_to_maturity: number;
  periods_per_year?: number;
}) {
  return apiFetch<any>('/bonds/price', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function calculateBondYield(params: {
  face_value: number;
  coupon_rate: number;
  years_to_maturity: number;
  price: number;
  periods_per_year?: number;
}) {
  return apiFetch<any>('/bonds/yield', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function calculateBondRiskMetrics(params: {
  face_value: number;
  coupon_rate: number;
  years_to_maturity: number;
  yield_to_maturity: number;
  periods_per_year?: number;
}) {
  return apiFetch<any>('/bonds/risk', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// === v1.9 Caching ===

export async function getCacheStats() {
  return apiFetch<any>('/cache/stats', { method: 'GET' });
}

export async function clearCache() {
  return apiFetch<any>('/cache/clear', { method: 'POST' });
}

// ===v2.3 Storage ===

export async function getReportDownloadUrls(reportBundleId: string) {
  return apiFetch<any>(`/reports/${reportBundleId}/downloads`, { method: 'GET' });
}

export async function getStorageFile(key: string) {
  return apiFetch<any>(`/storage/files/${encodeURIComponent(key)}`, { method: 'GET' });
}

// === v2.4 Job Queue ===

export async function submitJob(params: {
  job_type: 'run' | 'report' | 'hedge';
  payload: Record<string, any>;
  workspace_id?: string;
  async_mode?: boolean;
}){
  return apiFetch<any>('/jobs/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function getJob(jobId: string) {
  return apiFetch<any>(`/jobs/${jobId}`, { method: 'GET' });
}

export async function listJobs(filters?: {
  workspace_id?: string;
  job_type?: string;
  status?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.workspace_id) params.append('workspace_id', filters.workspace_id);
  if (filters?.job_type) params.append('job_type', filters.job_type);
  if (filters?.status) params.append('status', filters.status);
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/jobs${query}`, { method: 'GET' });
}

export async function cancelJob(jobId: string) {
  return apiFetch<any>(`/jobs/${jobId}/cancel`, { method: 'POST' });
}

export async function getJobsBackend() {
  return apiFetch<any>('/jobs/config/backend', { method: 'GET' });
}

// === v2.5 DevOps Automations ===

export async function analyzeGitLabMR(diffText: string) {
  return apiFetch<any>('/devops/gitlab/analyze-mr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diff_text: diffText }),
  });
}

export async function postGitLabComment(params: {
  project_id: string;
  mr_iid: number;
  comment_body: string;
}) {
  return apiFetch<any>('/devops/gitlab/post-comment', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getGitLabComments() {
  return apiFetch<any>('/devops/gitlab/comments', { method: 'GET' });
}

export async function generateMonitoringReport(params?: {
  include_health?: boolean;
  include_coverage?: boolean;
}) {
  return apiFetch<any>('/devops/monitor/generate-report', {
    method: 'POST',
    body: JSON.stringify(params || {}),
  });
}

export async function getMonitoringReports(limit?: number) {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit.toString());
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<any>(`/devops/monitor/reports${query}`, { method: 'GET' });
}

export async function runTestScenario(params: {
  scenario_type: 'mr_review' | 'monitoring_cycle';
  diff_text?: string;
}) {
  return apiFetch<any>('/devops/test-harness/run-scenario', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getTestScenarios() {
  return apiFetch<any>('/devops/test-harness/scenarios', { method: 'GET' });
}

// === v3.3 AuditV2 + Provenance ===

export async function getAuditV2Events(params?: { workspace_id?: string; limit?: number; since_event_id?: number }) {
  const q = new URLSearchParams();
  if (params?.workspace_id) q.append('workspace_id', params.workspace_id);
  if (params?.limit) q.append('limit', String(params.limit));
  if (params?.since_event_id != null) q.append('since_event_id', String(params.since_event_id));
  const qs = q.toString() ? `?${q.toString()}` : '';
  return apiFetch<any>(`/audit/v2/events${qs}`, { method: 'GET' });
}

export async function verifyAuditV2Chain() {
  return apiFetch<any>('/audit/v2/verify', { method: 'GET' });
}

export async function resetAuditV2() {
  return apiFetch<any>('/audit/v2/reset', { method: 'POST' });
}

export async function getProvenance(kind: string, resourceId: string) {
  return apiFetch<any>(`/provenance/${kind}/${resourceId}`, { method: 'GET' });
}

// === v3.4 Rates Curve ===

export async function getRatesFixture() {
  return apiFetch<any>('/rates/fixtures/simple', { method: 'GET' });
}

export async function bootstrapRatesCurve(instruments: any[]) {
  return apiFetch<any>('/rates/curve/bootstrap', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruments }),
  });
}

export async function priceBondWithCurve(params: {
  face_value: number;
  coupon_rate: number;
  years_to_maturity: number;
  periods_per_year: number;
  discount_factors: any[];
}) {
  return apiFetch<any>('/rates/bond/price-curve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

// === v3.5 Stress Library + Compare ===

export async function listStressPresets() {
  return apiFetch<any>('/stress/presets', { method: 'GET' });
}

export async function getStressPreset(presetId: string) {
  return apiFetch<any>(`/stress/presets/${presetId}`, { method: 'GET' });
}

export async function applyStressPreset(presetId: string, portfolio: any) {
  return apiFetch<any>('/stress/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset_id: presetId, portfolio }),
  });
}

export async function compareRunsV2(runA: any, runB: any) {
  return apiFetch<any>('/compare/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_a: runA, run_b: runB }),
  });
}

// === v3.7 Policy Engine v2 ===

export async function evaluatePolicy(runConfig: any, mode = 'DEMO') {
  return apiFetch<any>('/governance/policy/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_config: runConfig, mode }),
  });
}

export async function applyPolicy(runConfig: any, mode = 'DEMO') {
  return apiFetch<any>('/governance/policy/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_config: runConfig, mode }),
  });
}

export async function validateNarrative(narrative: string, computedResults: any, tolerance = 0.01) {
  return apiFetch<any>('/governance/narrative/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ narrative, computed_results: computedResults, tolerance }),
  });
}

// === v3.8 Eval Harness v2 ===

export async function listEvalSuites() {
  return apiFetch<any>('/governance/evals/suites', { method: 'GET' });
}

export async function runEvalSuite(suiteId: string) {
  return apiFetch<any>('/governance/evals/run-suite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ suite_id: suiteId }),
  });
}

export async function getEvalResult(runId: string) {
  return apiFetch<any>(`/governance/evals/results/${runId}`, { method: 'GET' });
}

export async function getScorecardMd(runId: string) {
  return fetch(`${API_BASE}/governance/evals/scorecard/${runId}/md`).then(r => r.text());
}

// === v3.9 DevOps Pro ===

export async function generateMRReviewBundle(diff: string, baseRef = 'main', headRef = 'feature') {
  return apiFetch<any>('/devops/mr/review-bundle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ diff, base_ref: baseRef, head_ref: headRef }),
  });
}

export async function analyzePipelineLog(log: string) {
  return apiFetch<any>('/devops/pipeline/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ log }),
  });
}

export async function buildArtifactPack(reviewMd?: string, pipelineJson?: string) {
  return apiFetch<any>('/devops/artifacts/build', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ review_md: reviewMd, pipeline_json: pipelineJson }),
  });
}

// === v4.0 SRE Playbooks ===

export async function generateSREPlaybook(params?: {
  policyGateResult?: any;
  pipelineAnalysis?: any;
  platformHealth?: any;
}) {
  const body: any = {};
  if (params?.policyGateResult) body.policy_gate_result = params.policyGateResult;
  if (params?.pipelineAnalysis) body.pipeline_analysis = params.pipelineAnalysis;
  if (params?.platformHealth) body.platform_health = params.platformHealth;
  return apiFetch<any>('/sre/playbook/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// === v4.1 Activity Stream ===

export async function getActivity(params?: { workspace_id?: string; limit?: number; since_event_id?: number }) {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set('workspace_id', params.workspace_id);
  if (params?.limit !== undefined) qs.set('limit', String(params.limit));
  if (params?.since_event_id !== undefined) qs.set('since_event_id', String(params.since_event_id));
  const query = qs.toString() ? `?${qs}` : '';
  return apiFetch<any>(`/activity${query}`);
}

export async function resetActivity() {
  return apiFetch<any>('/activity/reset', { method: 'POST' });
}

// === v4.1 Presence ===

export async function getPresence(params?: { workspace_id?: string }) {
  const qs = new URLSearchParams();
  if (params?.workspace_id) qs.set('workspace_id', params.workspace_id);
  const query = qs.toString() ? `?${qs}` : '';
  return apiFetch<any>(`/presence${query}`);
}

export async function updatePresence(body: { workspace_id: string; actor: string; status: string; display?: string }) {
  return apiFetch<any>('/presence/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// === v4.2 Live Run ===

export async function getRunStatus(run_id: string) {
  return apiFetch<any>(`/runs/${run_id}/status`);
}

// === v4.3 Search ===

export async function searchQuery(params: { text: string; filters?: string[]; limit?: number }) {
  return apiFetch<any>('/search/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function searchReindex() {
  return apiFetch<any>('/search/reindex', { method: 'POST' });
}

export async function searchStatus() {
  return apiFetch<any>('/search/status');
}
// === v4.6 Market Data Provider ===

export async function getMarketAsof() {
  return apiFetch<any>('/market/asof', { method: 'GET' });
}

export async function getMarketSpot(symbol: string) {
  return apiFetch<any>(`/market/spot?symbol=${encodeURIComponent(symbol)}`, { method: 'GET' });
}

export async function postMarketSeries(params: { symbol: string; start?: string; end?: string; freq?: string }) {
  return apiFetch<any>('/market/series', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function getMarketCurve(curveId: string) {
  return apiFetch<any>(`/market/curves/${encodeURIComponent(curveId)}`, { method: 'GET' });
}

// === v4.7 Cache v2 ===

export async function getCacheV2Stats() {
  return apiFetch<any>('/cache/v2/stats', { method: 'GET' });
}

export async function clearCacheV2(layer?: string) {
  const qs = layer ? `?layer=${encodeURIComponent(layer)}` : '';
  return apiFetch<any>(`/cache/v2/clear${qs}`, { method: 'POST' });
}

export async function getCacheV2Keys(layer: string, limit = 20) {
  return apiFetch<any>(`/cache/v2/keys?layer=${encodeURIComponent(layer)}&limit=${limit}`, { method: 'GET' });
}

// === v4.8 Hedge Engine v2 ===

export async function getHedgeTemplates() {
  return apiFetch<any>('/hedge/v2/templates', { method: 'GET' });
}

export async function suggestHedgesV2(params: {
  portfolio_id?: string;
  portfolio_value?: number;
  template_id?: string;
  objective?: string;
  before_metrics?: Record<string, number>;
  constraints?: Record<string, any>;
}) {
  return apiFetch<any>('/hedge/v2/suggest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function compareHedgeV2(params: {
  base_run_id?: string;
  base_metrics?: Record<string, number>;
  hedged_metrics?: Record<string, number>;
}) {
  return apiFetch<any>('/hedge/v2/compare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

// === v4.9 Decision Memo ===

export async function buildDecisionMemo(params: {
  hedge_result: any;
  compare_deltas: any;
  provenance_hashes?: Record<string, string>;
  analyst_notes?: string;
}) {
  return apiFetch<any>('/hedge/v2/memo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function exportHedgeDecisionPack(params: {
  memo_request: {
    hedge_result: any;
    compare_deltas: any;
    provenance_hashes?: Record<string, string>;
    analyst_notes?: string;
  };
  include_candidates?: boolean;
  include_compare?: boolean;
}) {
  return apiFetch<any>('/exports/hedge-decision-pack', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

// ===== PnL Attribution (v4.10.0) =====

export async function postPnLAttribution(params: {
  base_run_id: string;
  compare_run_id: string;
  portfolio_id?: string;
}) {
  return apiFetch<any>('/pnl/attribution', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getPnLDriverPresets() {
  return apiFetch<any>('/pnl/drivers/presets', { method: 'GET' });
}

export async function exportPnLAttributionPack(params: {
  base_run_id: string;
  compare_run_id: string;
  portfolio_id?: string;
  format?: 'json' | 'md';
}) {
  return apiFetch<any>('/exports/pnl-attribution-pack', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// ===== Scenario DSL (v4.14.0) =====

export async function postScenarioValidate(scenario: Record<string, any>) {
  return apiFetch<any>('/scenarios/validate', {
    method: 'POST',
    body: JSON.stringify({ scenario }),
  });
}

export async function postScenarioCreate(scenario: Record<string, any>) {
  return apiFetch<any>('/scenarios/create', {
    method: 'POST',
    body: JSON.stringify({ scenario }),
  });
}

export async function getScenarioList() {
  return apiFetch<any>('/scenarios/list', { method: 'GET' });
}

export async function getScenarioById(scenarioId: string) {
  return apiFetch<any>(`/scenarios/${encodeURIComponent(scenarioId)}`, { method: 'GET' });
}

export async function postScenarioDiff(aId: string, bId: string) {
  return apiFetch<any>('/scenarios/diff', {
    method: 'POST',
    body: JSON.stringify({ a_id: aId, b_id: bId }),
  });
}

export async function exportScenarioPack(scenarioIds: string[]) {
  return apiFetch<any>('/exports/scenario-pack', {
    method: 'POST',
    body: JSON.stringify({ scenario_ids: scenarioIds }),
  });
}

// ===== Replay Store (v4.18.0) =====

export async function postReplayStore(params: {
  endpoint: string;
  request_payload: Record<string, any>;
  response_payload: Record<string, any>;
}) {
  return apiFetch<any>('/replay/store', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function postReplayVerify(replayId: string) {
  return apiFetch<any>('/replay/verify', {
    method: 'POST',
    body: JSON.stringify({ replay_id: replayId }),
  });
}

export async function getReplaySuites() {
  return apiFetch<any>('/replay/suites/list', { method: 'GET' });
}

export async function postReplayRunSuite(suiteId: string) {
  return apiFetch<any>('/replay/run-suite', {
    method: 'POST',
    body: JSON.stringify({ suite_id: suiteId }),
  });
}

export async function exportReproPack(suiteId: string) {
  return apiFetch<any>('/exports/repro-report-pack', {
    method: 'POST',
    body: JSON.stringify({ suite_id: suiteId }),
  });
}

// ===== Construction Engine (v4.22.0) =====

export async function postConstructionSolve(params: {
  current_weights: Record<string, number>;
  constraints: Record<string, any>;
  objective?: string;
}) {
  return apiFetch<any>('/construct/solve', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function postConstructionCompare(before: any, after: any) {
  return apiFetch<any>('/construct/compare', {
    method: 'POST',
    body: JSON.stringify({ before, after }),
  });
}

export async function exportConstructionPack(solveResult: any) {
  return apiFetch<any>('/exports/construction-decision-pack', {
    method: 'POST',
    body: JSON.stringify({ solve_result: solveResult }),
  });
}

// ===== FX Risk (Wave 19, v4.26-v4.29) =====

export async function getFxSpot(pair: string) {
  return apiFetch<any>(`/fx/spot?pair=${pair}`, { method: 'GET' });
}

export async function getFxForward(pair: string, tenor: string) {
  return apiFetch<any>(`/fx/forward?pair=${pair}&tenor=${tenor}`, { method: 'GET' });
}

export async function getFxVol(pair: string) {
  return apiFetch<any>(`/fx/vol?pair=${pair}`, { method: 'GET' });
}

export async function getFxPairs() {
  return apiFetch<any>('/fx/pairs', { method: 'GET' });
}

export async function getFxExposure(portfolio: any[], base_ccy: string = 'USD') {
  return apiFetch<any>('/fx/exposure', {
    method: 'POST',
    body: JSON.stringify({ portfolio, base_ccy }),
  });
}

export async function applyFxShocks(exposure: any, fx_shocks: Array<{pair: string, pct: number}>) {
  return apiFetch<any>('/fx/shock', {
    method: 'POST',
    body: JSON.stringify({ exposure, fx_shocks }),
  });
}

export async function exportFxPack(portfolio?: any[], base_ccy?: string, fx_shocks?: any[]) {
  return apiFetch<any>('/exports/fx-pack', {
    method: 'POST',
    body: JSON.stringify({ portfolio, base_ccy, fx_shocks }),
  });
}

// ===== Credit Risk (Wave 20, v4.30-v4.33) =====

export async function getCreditCurves() {
  return apiFetch<any>('/credit/curves', { method: 'GET' });
}

export async function getCreditCurve(curveId: string) {
  return apiFetch<any>(`/credit/curves/${curveId}`, { method: 'GET' });
}

export async function computeCreditRisk(
  positions: any[],
  curve_id: string = 'usd_ig',
  shock_bps: number = 0,
) {
  return apiFetch<any>('/credit/risk', {
    method: 'POST',
    body: JSON.stringify({ positions, curve_id, shock_bps }),
  });
}

export async function exportCreditPack(positions: any[], curve_id: string, shock_bps: number) {
  return apiFetch<any>('/exports/credit-risk-pack', {
    method: 'POST',
    body: JSON.stringify({ positions, curve_id, shock_bps }),
  });
}

// ===== Liquidity (Wave 21, v4.34-v4.37) =====

export async function getLiquidityTiers() {
  return apiFetch<any>('/liquidity/tiers', { method: 'GET' });
}

export async function computeHaircut(portfolio: any[]) {
  return apiFetch<any>('/liquidity/haircut', {
    method: 'POST',
    body: JSON.stringify({ portfolio }),
  });
}

export async function estimateTcost(trades: any[]) {
  return apiFetch<any>('/tcost/estimate', {
    method: 'POST',
    body: JSON.stringify({ trades }),
  });
}

export async function computeTradeoff(hedge_trades: any[], risk_reduction_usd: number) {
  return apiFetch<any>('/tcost/tradeoff', {
    method: 'POST',
    body: JSON.stringify({ hedge_trades, risk_reduction_usd }),
  });
}

export async function exportLiquidityPack(portfolio: any[], trades: any[]) {
  return apiFetch<any>('/exports/liquidity-pack', {
    method: 'POST',
    body: JSON.stringify({ portfolio, trades }),
  });
}

// ===== Approvals (Wave 22, v4.38-v4.41) =====

export async function listApprovals(state?: string) {
  const qs = state ? `?state=${state}` : '';
  return apiFetch<any>(`/approvals/list${qs}`, { method: 'GET' });
}

export async function createApproval(payload: {
  document_type: string;
  title: string;
  payload: Record<string, any>;
  requester: string;
}) {
  return apiFetch<any>('/approvals/create', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function submitApproval(approvalId: string, actor: string = 'demo_user') {
  return apiFetch<any>(`/approvals/submit/${approvalId}`, {
    method: 'POST',
    body: JSON.stringify({ actor }),
  });
}

export async function decideApproval(
  approvalId: string,
  decision: 'approved' | 'rejected',
  actor: string = 'risk_committee',
  notes?: string,
) {
  return apiFetch<any>(`/approvals/decide/${approvalId}`, {
    method: 'POST',
    body: JSON.stringify({ decision, actor, notes }),
  });
}

export async function getApproval(approvalId: string) {
  return apiFetch<any>(`/approvals/${approvalId}`, { method: 'GET' });
}

export async function exportApprovalPack(approvalId: string) {
  return apiFetch<any>(`/exports/approval-pack/${approvalId}`, { method: 'GET' });
}

// ===== GitLab Adapter (Wave 23, v4.42-v4.45) =====

export async function listMrs() {
  return apiFetch<any>('/gitlab/mrs', { method: 'GET' });
}

export async function getMrDiff(iid: number) {
  return apiFetch<any>(`/gitlab/mrs/${iid}/diff`, { method: 'GET' });
}

export async function postMrComment(iid: number, body: string, author: string = 'demo_user') {
  return apiFetch<any>(`/gitlab/mrs/${iid}/comment`, {
    method: 'POST',
    body: JSON.stringify({ body, author }),
  });
}

export async function exportMrCompliancePack(iid: number) {
  return apiFetch<any>(`/exports/mr-compliance-pack/${iid}`, { method: 'GET' });
}

// ===== CI Intelligence (Wave 24, v4.46-v4.47) =====

export async function listPipelines() {
  return apiFetch<any>('/ci/pipelines', { method: 'GET' });
}

export async function analyzePipeline(pipelineId: string) {
  return apiFetch<any>(`/ci/pipelines/${pipelineId}/analysis`, { method: 'GET' });
}

export async function getCiTemplateFeatures() {
  return apiFetch<any>('/ci/template/features', { method: 'GET' });
}

export async function generateCiTemplate(features: string[]) {
  return apiFetch<any>('/ci/template/generate', {
    method: 'POST',
    body: JSON.stringify({ features }),
  });
}

export async function exportCiTemplatePack(features: string[]) {
  return apiFetch<any>('/exports/ci-template-pack', {
    method: 'POST',
    body: JSON.stringify({ features }),
  });
}

// ===== DevSecOps (Wave 25, v4.48-v4.49) =====

export async function getSecurityRules() {
  return apiFetch<any>('/sec/rules', { method: 'GET' });
}

export async function scanDiff(content: string) {
  return apiFetch<any>('/sec/scan/diff', {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

export async function getSbom() {
  return apiFetch<any>('/sec/sbom', { method: 'GET' });
}

export async function validateSecurityRules(rules: any[]) {
  return apiFetch<any>('/sec/rules/validate', {
    method: 'POST',
    body: JSON.stringify({ rules }),
  });
}

export async function getAttestation(
  commit_sha: string,
  proof_pack_hash: string,
  scan_results: any,
) {
  return apiFetch<any>('/exports/attestation', {
    method: 'POST',
    body: JSON.stringify({ commit_sha, proof_pack_hash, scan_results }),
  });
}

export async function exportDevSecOpsPack(
  commit_sha: string = 'HEAD',
  proof_pack_hash: string = '',
  diff_content?: string,
) {
  return apiFetch<any>('/exports/devsecops-pack', {
    method: 'POST',
    body: JSON.stringify({ commit_sha, proof_pack_hash, diff_content }),
  });
}

// ═══════════════════════════════════════════════════════════════
// Wave 26 — Agentic MR Review (v4.50-v4.53)
// ═══════════════════════════════════════════════════════════════
export async function mrListFixtures() {
  return apiFetch<any>('/mr/fixtures');
}
export async function mrPlanReview(mr_id: string, options: Record<string, any> = {}) {
  return apiFetch<any>('/mr/review/plan', { method: 'POST', body: JSON.stringify({ mr_id, options }) });
}
export async function mrRunReview(plan_id: string) {
  return apiFetch<any>('/mr/review/run', { method: 'POST', body: JSON.stringify({ plan_id }) });
}
export async function mrGetReview(review_id: string) {
  return apiFetch<any>(`/mr/review/${review_id}`);
}
export async function mrCommentPreview(review_id: string) {
  return apiFetch<any>('/mr/review/comments/preview', { method: 'POST', body: JSON.stringify({ review_id }) });
}
export async function mrPostComments(review_id: string, comments: any[]) {
  return apiFetch<any>('/mr/review/comments/post', { method: 'POST', body: JSON.stringify({ review_id, comments }) });
}
export async function mrExportPack(review_id: string) {
  return apiFetch<any>('/exports/mr-review-pack', { method: 'POST', body: JSON.stringify({ review_id }) });
}

// ═══════════════════════════════════════════════════════════════
// Wave 27 — Incident Drills (v4.54-v4.57)
// ═══════════════════════════════════════════════════════════════
export async function incidentListScenarios() {
  return apiFetch<any>('/incidents/scenarios');
}
export async function incidentRunDrill(scenario_id: string, options: Record<string, any> = {}) {
  return apiFetch<any>('/incidents/run', { method: 'POST', body: JSON.stringify({ scenario_id, options }) });
}
export async function incidentGetRun(run_id: string) {
  return apiFetch<any>(`/incidents/runs/${run_id}`);
}
export async function incidentExportPack(run_id: string) {
  return apiFetch<any>('/exports/incident-pack', { method: 'POST', body: JSON.stringify({ run_id }) });
}

// ═══════════════════════════════════════════════════════════════
// Wave 28 — Release Readiness (v4.58-v4.61)
// ═══════════════════════════════════════════════════════════════
export async function releaseEvaluate(metrics: Record<string, number>, context: Record<string, any>) {
  return apiFetch<any>('/release/readiness/evaluate', { method: 'POST', body: JSON.stringify({ metrics, context }) });
}
export async function releaseGetAssessment(assessment_id: string) {
  return apiFetch<any>(`/release/readiness/${assessment_id}`);
}
export async function releaseExportPack(assessment_id: string) {
  return apiFetch<any>('/exports/release-memo-pack', { method: 'POST', body: JSON.stringify({ assessment_id }) });
}

// ═══════════════════════════════════════════════════════════════
// Wave 29 — Workflow Studio (v4.62-v4.65)
// ═══════════════════════════════════════════════════════════════
export async function wfGenerate(spec: Record<string, any>) {
  return apiFetch<any>('/workflows/generate', { method: 'POST', body: JSON.stringify(spec) });
}
export async function wfActivate(workflow_id: string) {
  return apiFetch<any>('/workflows/activate', { method: 'POST', body: JSON.stringify({ workflow_id }) });
}
export async function wfList() {
  return apiFetch<any>('/workflows/list');
}
export async function wfSimulate(workflow_id: string) {
  return apiFetch<any>('/workflows/simulate', { method: 'POST', body: JSON.stringify({ workflow_id }) });
}
export async function wfRuns(workflow_id?: string) {
  const qs = workflow_id ? `?workflow_id=${workflow_id}` : '';
  return apiFetch<any>(`/workflows/runs${qs}`);
}

// ═══════════════════════════════════════════════════════════════
// Wave 30 — Policy Registry V2 (v4.66-v4.69)
// ═══════════════════════════════════════════════════════════════
export async function policyV2Create(slug: string, title: string, body: string, tags: string[]) {
  return apiFetch<any>('/policies/v2/create', { method: 'POST', body: JSON.stringify({ slug, title, body, tags }) });
}
export async function policyV2Publish(slug: string, version_number: number | null) {
  return apiFetch<any>('/policies/v2/publish', { method: 'POST', body: JSON.stringify({ slug, version_number }) });
}
export async function policyV2Rollback(slug: string, to_version: number) {
  return apiFetch<any>('/policies/v2/rollback', { method: 'POST', body: JSON.stringify({ slug, to_version }) });
}
export async function policyV2List() {
  return apiFetch<any>('/policies/v2/list');
}
export async function policyV2Versions(slug: string) {
  return apiFetch<any>(`/policies/v2/versions/${slug}`);
}

// ═══════════════════════════════════════════════════════════════
// Wave 31 — Search V2 (v4.70-v4.71)
// ═══════════════════════════════════════════════════════════════
export async function searchV2Stats() {
  return apiFetch<any>('/search/v2/stats');
}
export async function searchV2Query(q: string, type?: string, page = 1, page_size = 10) {
  return apiFetch<any>('/search/v2/query', { method: 'POST', body: JSON.stringify({ q, type, page, page_size }) });
}

// ═══════════════════════════════════════════════════════════════
// Wave 32 — Judge Mode W26-32 (v4.72-v4.73)
// ═══════════════════════════════════════════════════════════════
export async function judgeW26W32GeneratePack() {
  return apiFetch<any>('/judge/w26-32/generate-pack', { method: 'POST' });
}
export async function judgeW26W32GetFiles() {
  return apiFetch<any>('/judge/w26-32/files');
}


// ═══════════════════════════════════════════════════════════════
// Wave 34 — Exports Hub (v4.80.0)
// ═══════════════════════════════════════════════════════════════
export async function exportsGetRecent() {
  return apiFetch<any>('/exports/recent');
}
export async function exportsVerify(packId: string) {
  return apiFetch<any>(`/exports/verify/${packId}`);
}
export async function exportsGenerateDecisionPacket(
  subjectType: string,
  subjectId: string,
  requestedBy = 'demo@riskcanvas.io',
  tenantId = 'demo-tenant',
) {
  return apiFetch<any>('/exports/decision-packet', {
    method: 'POST',
    body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId, requested_by: requestedBy, tenant_id: tenantId }),
  });
}
export async function exportsListDecisionPackets(tenantId = 'demo-tenant') {
  return apiFetch<any>(`/exports/decision-packets?tenant_id=${tenantId}`);
}
export async function exportsVerifyDecisionPacket(packetId: string) {
  return apiFetch<any>(`/exports/decision-packets/${packetId}/verify`, { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════
// Wave 40 — Judge Pack W33-40 (v4.97.0)
// ═══════════════════════════════════════════════════════════════
export async function judgeW33W40GeneratePack() {
  return apiFetch<any>('/judge/w33-40/generate-pack', { method: 'POST' });
}
export async function judgeW33W40GetFiles() {
  return apiFetch<any>('/judge/w33-40/files');
}

// ═══════════════════════════════════════════════════════════════
// Wave 41 — Tenancy v2 + RBAC (v4.98.0-v5.01.0)
// ═══════════════════════════════════════════════════════════════
export async function tenantsListAll(role = 'OWNER') {
  return apiFetch<any>('/tenants', { headers: { 'x-demo-role': role } });
}
export async function tenantsListMembers(tenantId: string) {
  return apiFetch<any>(`/tenants/${tenantId}/members`);
}
export async function tenantsAddMember(tenantId: string, email: string, role: string) {
  return apiFetch<any>(`/tenants/${tenantId}/members`, {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
}
export async function tenantContext() {
  return apiFetch<any>('/tenants/~context');
}

// ═══════════════════════════════════════════════════════════════
// Wave 42 — Artifact Registry (v5.02.0-v5.05.0)
// ═══════════════════════════════════════════════════════════════
export async function artifactsList(tenantId?: string, type?: string) {
  const params = new URLSearchParams();
  if (tenantId) params.set('tenant_id', tenantId);
  if (type) params.set('type', type);
  const qs = params.toString();
  return apiFetch<any>(`/artifacts${qs ? '?' + qs : ''}`);
}
export async function artifactsGet(artifactId: string) {
  return apiFetch<any>(`/artifacts/${artifactId}`);
}
export async function artifactsGetDownload(artifactId: string) {
  return apiFetch<any>(`/artifacts/${artifactId}/downloads`);
}

// ═══════════════════════════════════════════════════════════════
// Wave 43 — Attestations (v5.06.0-v5.09.0)
// ═══════════════════════════════════════════════════════════════
export async function attestationsList(tenantId?: string) {
  const qs = tenantId ? `?tenant_id=${tenantId}` : '';
  return apiFetch<any>(`/attestations${qs}`);
}
export async function attestationsGet(id: string) {
  return apiFetch<any>(`/attestations/${id}`);
}
export async function attestationsReceiptsPack(tenantId?: string) {
  const qs = tenantId ? `?tenant_id=${tenantId}` : '';
  return apiFetch<any>(`/attestations/receipts-pack${qs}`, { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════
// Wave 44 — Compliance Pack (v5.10.0-v5.13.0)
// ═══════════════════════════════════════════════════════════════
export async function complianceGeneratePack(window = 'last_30_demo_days') {
  return apiFetch<any>('/compliance/generate-pack', {
    method: 'POST',
    body: JSON.stringify({ window }),
  });
}
export async function complianceListPacks(tenantId?: string) {
  const qs = tenantId ? `?tenant_id=${tenantId}` : '';
  return apiFetch<any>(`/compliance/packs${qs}`);
}
export async function complianceVerifyPack(packId: string) {
  return apiFetch<any>(`/compliance/packs/${packId}/verify`, { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════
// Wave 47 — Judge Mode v2 (v5.18.0-v5.19.0)
// ═══════════════════════════════════════════════════════════════
export async function judgeV2Generate(target = 'all') {
  return apiFetch<any>('/judge/v2/generate', { method: 'POST', body: JSON.stringify({ target }) });
}
export async function judgeV2ListPacks() {
  return apiFetch<any>('/judge/v2/packs');
}
export async function judgeV2Definitions() {
  return apiFetch<any>('/judge/v2/definitions');
}

// ═══════════════════════════════════════════════════════════════
// Wave 49 — Dataset Ingestion (v5.22.0-v5.25.0)
// ═══════════════════════════════════════════════════════════════
export async function datasetsList(kind?: string, limit = 100) {
  const params = new URLSearchParams();
  if (kind) params.set('kind', kind);
  params.set('limit', String(limit));
  return apiFetch<any>(`/datasets?${params.toString()}`);
}
export async function datasetsGet(datasetId: string) {
  return apiFetch<any>(`/datasets/${datasetId}`);
}
export async function datasetsIngest(kind: string, name: string, payload: unknown, createdBy = 'api@riskcanvas.io') {
  return apiFetch<any>('/datasets/ingest', {
    method: 'POST',
    body: JSON.stringify({ kind, name, payload, created_by: createdBy }),
  });
}
export async function datasetsValidate(kind: string, name: string, payload: unknown) {
  return apiFetch<any>('/datasets/validate', {
    method: 'POST',
    body: JSON.stringify({ kind, name, payload }),
  });
}

// ═══════════════════════════════════════════════════════════════
// Wave 50 — Scenarios v2 (v5.26.0-v5.29.0)
// ═══════════════════════════════════════════════════════════════
export async function scenariosV2List(kind?: string) {
  const qs = kind ? `?kind=${kind}` : '';
  return apiFetch<any>(`/scenarios-v2${qs}`);
}
export async function scenariosV2Create(name: string, kind: string, payload: unknown, createdBy = 'api@riskcanvas.io') {
  return apiFetch<any>('/scenarios-v2', {
    method: 'POST',
    body: JSON.stringify({ name, kind, payload, created_by: createdBy }),
  });
}
export async function scenariosV2Get(scenarioId: string) {
  return apiFetch<any>(`/scenarios-v2/${scenarioId}`);
}
export async function scenariosV2Run(scenarioId: string, triggeredBy = 'api@riskcanvas.io') {
  return apiFetch<any>(`/scenarios-v2/${scenarioId}/run`, {
    method: 'POST',
    body: JSON.stringify({ triggered_by: triggeredBy }),
  });
}
export async function scenariosV2Replay(scenarioId: string, triggeredBy = 'api@riskcanvas.io') {
  return apiFetch<any>(`/scenarios-v2/${scenarioId}/replay`, {
    method: 'POST',
    body: JSON.stringify({ triggered_by: triggeredBy }),
  });
}
export async function scenariosV2Runs(scenarioId: string) {
  return apiFetch<any>(`/scenarios-v2/${scenarioId}/runs`);
}
export async function scenariosV2Templates() {
  return apiFetch<any>('/scenarios-v2/templates/all');
}

// ═══════════════════════════════════════════════════════════════
// Wave 51 — Reviews & Decision Packets (v5.30.0-v5.33.0)
// ═══════════════════════════════════════════════════════════════
export async function reviewsList(status?: string, subjectType?: string) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (subjectType) params.set('subject_type', subjectType);
  const qs = params.toString();
  return apiFetch<any>(`/reviews${qs ? '?' + qs : ''}`);
}
export async function reviewsCreate(subjectType: string, subjectId: string, requestedBy: string, notes = '') {
  return apiFetch<any>('/reviews', {
    method: 'POST',
    body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId, requested_by: requestedBy, notes }),
  });
}
export async function reviewsGet(reviewId: string) {
  return apiFetch<any>(`/reviews/${reviewId}`);
}
export async function reviewsSubmit(reviewId: string) {
  return apiFetch<any>(`/reviews/${reviewId}/submit`, { method: 'POST' });
}
export async function reviewsDecide(reviewId: string, decision: 'APPROVED' | 'REJECTED', decidedBy: string) {
  return apiFetch<any>(`/reviews/${reviewId}/decide`, {
    method: 'POST',
    body: JSON.stringify({ decision, decided_by: decidedBy }),
  });
}
export async function decisionPacketGenerate(tenantId: string, subjectType: string, subjectId: string, requestedBy = 'api@riskcanvas.io') {
  return apiFetch<any>('/exports/decision-packet', {
    method: 'POST',
    body: JSON.stringify({ tenant_id: tenantId, subject_type: subjectType, subject_id: subjectId, requested_by: requestedBy }),
  });
}
export async function decisionPacketsList(tenantId?: string) {
  const qs = tenantId ? `?tenant_id=${tenantId}` : '';
  return apiFetch<any>(`/exports/decision-packets${qs}`);
}
export async function decisionPacketGet(packetId: string) {
  return apiFetch<any>(`/exports/decision-packets/${packetId}`);
}
export async function decisionPacketVerify(packetId: string) {
  return apiFetch<any>(`/exports/decision-packets/${packetId}/verify`, { method: 'POST' });
}

// ═══════════════════════════════════════════════════════════════
// Wave 53 — Deploy Validator (v5.38.0-v5.39.0)
// ═══════════════════════════════════════════════════════════════
export async function deployValidateAzure(env: Record<string, string>) {
  return apiFetch<any>('/deploy/validate-azure', { method: 'POST', body: JSON.stringify({ env }) });
}
export async function deployValidateDO(env: Record<string, string>) {
  return apiFetch<any>('/deploy/validate-do', { method: 'POST', body: JSON.stringify({ env }) });
}
export async function deployValidateAll(env: Record<string, string>) {
  return apiFetch<any>('/deploy/validate-all', { method: 'POST', body: JSON.stringify({ env }) });
}
export async function deployLintTemplate(template: string, templateType: 'do_compose' | 'nginx') {
  return apiFetch<any>('/deploy/lint-template', { method: 'POST', body: JSON.stringify({ template, template_type: templateType }) });
}

// ═══════════════════════════════════════════════════════════════
// Wave 54 — Judge Mode v3 (v5.40.0-v5.41.0)
// ═══════════════════════════════════════════════════════════════
export async function judgeV3Generate(target = 'all') {
  return apiFetch<any>('/judge/v3/generate', { method: 'POST', body: JSON.stringify({ target }) });
}
export async function judgeV3ListPacks() {
  return apiFetch<any>('/judge/v3/packs');
}
export async function judgeV3Definitions() {
  return apiFetch<any>('/judge/v3/definitions');
}

// ═══════════════════════════════════════════════════════════════
// Wave 62/71 — Judge Mode v4 (v5.50.0-v5.61.0)
// ═══════════════════════════════════════════════════════════════
export async function judgeV4Generate(generatedBy = 'api@riskcanvas.io') {
  return apiFetch<any>('/judge/v4/generate', { method: 'POST', body: JSON.stringify({ generated_by: generatedBy }) });
}
export async function judgeV4ListPacks(limit = 50) {
  return apiFetch<any>(`/judge/v4/packs?limit=${limit}`);
}
export async function judgeV4GetPack(packId: string) {
  return apiFetch<any>(`/judge/v4/packs/${packId}`);
}
export async function judgeV4PackSummary(packId: string) {
  return apiFetch<any>(`/judge/v4/packs/${packId}/summary`);
}
