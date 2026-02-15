// Portfolio types
export interface Asset {
  symbol: string;
  name: string;
  type: string;
  quantity: number;
  price: number;
  current_price?: number;
  purchase_price?: number;
}

export interface PortfolioMetrics {
  total_pnl: number;
  total_value: number;
  asset_count: number;
  portfolio_greeks?: Record<string, number> | null;
}

// Risk analysis types
export interface VaRResult {
  method: string;
  var_value: number;
  confidence_level: number;
}

export interface AnalysisResult {
  request_id: string;
  metrics: PortfolioMetrics;
  var?: VaRResult | null;
  warnings: string[];
}

// Determinism types
export interface DeterminismCheck {
  name: string;
  match: boolean;
  hash: string;
}

export interface DeterminismResult {
  passed: boolean;
  checks: DeterminismCheck[];
  overall_hash: string;
}

// Scenario types
export interface ScenarioRequest {
  spot_shock?: number;
  vol_shock?: number;
  rate_shock?: number;
}

export interface ScenarioResult {
  scenario: string;
  pnl: number;
  var?: number;
}

// Agent types
export interface AgentMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface AgentAuditEntry {
  tool: string;
  hash: string;
  duration: number;
  timestamp: Date;
}

// Report types
export interface Report {
  id: string;
  name: string;
  timestamp: Date;
  reportHash: string;
  inputHash: string;
  format: 'html' | 'json';
}
