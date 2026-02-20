"""
Pydantic models for API request/response schemas
"""

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


# ===== Common Models =====


class AssetBase(BaseModel):
    """Base asset model"""
    symbol: str
    name: Optional[str] = None
    type: Literal["stock", "option"] = "stock"
    quantity: float


class StockAsset(AssetBase):
    """Stock position"""
    type: Literal["stock"] = "stock"
    price: float = Field(gt=0)
    purchase_price: Optional[float] = None
    current_price: Optional[float] = None


class OptionAsset(AssetBase):
    """Option position"""
    type: Literal["option"] = "option"
    S: float = Field(gt=0, description="Current stock price")
    K: float = Field(gt=0, description="Strike price")
    T: float = Field(ge=0, description="Time to maturity (years)")
    r: float = Field(description="Risk-free rate")
    sigma: float = Field(ge=0, description="Volatility")
    option_type: Literal["call", "put"] = "call"
    current_price: Optional[float] = None
    purchase_price: Optional[float] = None


# ===== Request Models =====


class OptionPriceRequest(BaseModel):
    """Request to price a single option"""
    S: float = Field(gt=0, description="Current stock price")
    K: float = Field(gt=0, description="Strike price")
    T: float = Field(ge=0, description="Time to maturity (years)")
    r: float = Field(description="Risk-free rate (annual)")
    sigma: float = Field(ge=0, description="Volatility (annual)")
    option_type: Literal["call", "put"] = "call"


class Portfolio(BaseModel):
    """Portfolio with assets"""
    id: Optional[str] = None
    name: Optional[str] = None
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    total_value: Optional[float] = None


class PortfolioAnalysisRequest(BaseModel):
    """Request for comprehensive portfolio analysis"""
    portfolio: Portfolio


class VaRRequest(BaseModel):
    """Request for VaR calculation"""
    portfolio_value: float = Field(gt=0)
    method: Literal["parametric", "historical"] = "parametric"
    # Parametric VaR parameters
    volatility: Optional[float] = Field(None, ge=0, description="Annual volatility")
    confidence_level: float = Field(0.95, ge=0, le=1)
    time_horizon_days: int = Field(1, gt=0)
    # Historical VaR parameters
    historical_returns: Optional[List[float]] = None


class Scenario(BaseModel):
    """Stress test scenario"""
    name: str
    shock_type: Literal["price", "volatility", "rate", "combined"]
    parameters: Dict[str, float]


class ScenarioRequest(BaseModel):
    """Request for scenario analysis"""
    positions: List[Dict[str, Any]]
    scenarios: List[Scenario]


class ReportRequest(BaseModel):
    """Request to generate a report"""
    portfolio: Portfolio
    include_greeks: bool = True
    include_var: bool = True
    include_scenarios: bool = False


# ===== Response Models =====


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    demo_mode: bool = False
    storage_backend: str = "memory"
    job_backend: str = "sync"


class VersionResponse(BaseModel):
    """Version information"""
    api_version: str
    engine_version: str


class OptionPriceResponse(BaseModel):
    """Option pricing response"""
    request_id: str
    price: float
    greeks: Optional[Dict[str, float]] = None
    warnings: List[str] = Field(default_factory=list)


class GreeksResponse(BaseModel):
    """Greeks calculation response"""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


class PortfolioMetrics(BaseModel):
    """Portfolio-level metrics"""
    total_pnl: float
    total_value: float
    asset_count: int
    portfolio_greeks: Optional[GreeksResponse] = None


class VaRResponse(BaseModel):
    """VaR calculation response"""
    request_id: str
    method: str
    var_value: float
    confidence_level: float
    time_horizon_days: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)


class ScenarioResult(BaseModel):
    """Single scenario result"""
    name: str
    shock_type: str
    base_value: float
    scenario_value: float
    change: float
    change_pct: float


class ScenarioResponse(BaseModel):
    """Scenario analysis response"""
    request_id: str
    scenarios: List[ScenarioResult]
    warnings: List[str] = Field(default_factory=list)


class PortfolioAnalysisResponse(BaseModel):
    """Comprehensive portfolio analysis"""
    request_id: str
    portfolio_id: Optional[str] = None
    portfolio_name: Optional[str] = None
    version: str
    metrics: PortfolioMetrics
    var: Optional[VaRResponse] = None
    warnings: List[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    """Report generation response"""
    request_id: str
    portfolio_id: Optional[str] = None
    portfolio_name: Optional[str] = None
    html: Optional[str] = None
    metrics: PortfolioMetrics
    var: Optional[VaRResponse] = None
    scenarios: Optional[List[ScenarioResult]] = None
    warnings: List[str] = Field(default_factory=list)


# ===== v1.1+ Persistence Schemas =====


class PortfolioCreateRequest(BaseModel):
    """Request to create/update portfolio"""
    portfolio: Dict[str, Any]
    name: Optional[str] = None
    tags: Optional[List[str]] = None


class PortfolioInfo(BaseModel):
    """Portfolio metadata"""
    portfolio_id: str
    name: str
    tags: Optional[List[str]] = None
    created_at: str
    updated_at: str
    portfolio: Dict[str, Any]


class RunExecuteRequest(BaseModel):
    """Request to execute analysis run"""
    portfolio_id: Optional[str] = None
    portfolio: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RunInfo(BaseModel):
    """Run metadata and results"""
    run_id: str
    portfolio_id: str
    engine_version: str
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    portfolio_value: Optional[float] = None
    output_hash: Optional[str] = None
    report_bundle_id: Optional[str] = None
    created_at: str


class RunCompareRequest(BaseModel):
    """Request to compare two runs"""
    run_id_a: str
    run_id_b: str


class RunCompareResponse(BaseModel):
    """Run comparison results"""
    run_id_a: str
    run_id_b: str
    deltas: Dict[str, Any]
    top_changes: List[Dict[str, Any]]


# ===== v1.2 Report Bundle Schemas =====


class ReportBuildRequest(BaseModel):
    """Request to build report bundle"""
    run_id: str


class ReportBundleInfo(BaseModel):
    """Report bundle metadata"""
    report_bundle_id: str
    run_id: str
    portfolio_id: str
    manifest: Dict[str, Any]


# ===== v1.3 Hedge Studio Schemas =====


class HedgeSuggestRequest(BaseModel):
    """Request to get hedge suggestions"""
    portfolio_id: Optional[str] = None
    portfolio: Optional[Dict[str, Any]] = None
    target_reduction_pct: float = Field(default=20.0, ge=0, le=100)
    max_cost: Optional[float] = None
    allowed_instruments: Optional[List[str]] = None


class HedgeEvaluateRequest(BaseModel):
    """Request to evaluate a hedge"""
    portfolio: Dict[str, Any]
    hedge_candidate: Dict[str, Any]


# ===== v1.4 Workspace, RBAC, Audit Schemas =====


class WorkspaceCreateRequest(BaseModel):
    """Request to create a workspace"""
    name: str
    owner: str
    tags: Optional[List[str]] = None


class WorkspaceInfo(BaseModel):
    """Workspace information"""
    workspace_id: str
    name: str
    owner: str
    tags: List[str]
    created_at: str
    updated_at: str


class AuditEventInfo(BaseModel):
    """Audit event information"""
    event_id: str
    workspace_id: Optional[str]
    actor: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    input_hash: Optional[str]
    output_hash: Optional[str]
    result: str
    error_message: Optional[str]
    sequence: int
    created_at: str


# ===== v1.5 DevOps / Risk-bot Schemas =====


class RiskBotReportRequest(BaseModel):
    """Request to generate a risk-bot report"""
    base_ref: Optional[str] = None
    head_ref: Optional[str] = None
    base_portfolio: Optional[Dict[str, Any]] = None
    head_portfolio: Optional[Dict[str, Any]] = None


class RiskBotReportResponse(BaseModel):
    """Risk-bot report response"""
    report_markdown: str
    test_gate_summary: Dict[str, Any]
    risk_metric_diffs: Dict[str, Any]
    determinism_hashes: Dict[str, str]


# ===== v1.6 Monitoring, Alerts, Drift Schemas =====


class MonitorCreateRequest(BaseModel):
    """Request to create a monitor"""
    portfolio_id: str
    name: str
    schedule: Literal["manual", "daily", "weekly"]
    thresholds: Dict[str, float]
    workspace_id: Optional[str] = None
    scenario_preset: Optional[Dict[str, Any]] = None


class MonitorInfo(BaseModel):
    """Monitor information"""
    monitor_id: str
    workspace_id: Optional[str]
    portfolio_id: str
    name: str
    schedule: str
    scenario_preset: Optional[Dict[str, Any]]
    thresholds: Dict[str, float]
    enabled: bool
    last_run_id: Optional[str]
    last_run_sequence: int
    created_at: str
    updated_at: str


class MonitorRunNowRequest(BaseModel):
    """Request to run a monitor now"""
    monitor_id: str


class MonitorRunNowResponse(BaseModel):
    """Response from running a monitor"""
    monitor_id: str
    run_id: str
    alerts: List[Dict[str, Any]]
    drift_summary: Optional[Dict[str, Any]]


class AlertInfo(BaseModel):
    """Alert information"""
    alert_id: str
    monitor_id: str
    run_id: str
    severity: str
    rule: str
    message: str
    triggered_value: float
    threshold_value: float
    sequence: int
    created_at: str


class DriftSummaryInfo(BaseModel):
    """Drift summary information"""
    drift_id: str
    monitor_id: str
    previous_run_id: str
    current_run_id: str
    changes: Dict[str, Any]
    drift_score: float
    sequence: int
    created_at: str


# ===== v1.7 Governance Schemas =====


class AgentConfigCreateRequest(BaseModel):
    """Request to create an agent configuration"""
    name: str
    model: str
    provider: str
    system_prompt: str
    tool_policies: Dict[str, Any]
    thresholds: Dict[str, Any]
    tags: Optional[List[str]] = None


class AgentConfigInfo(BaseModel):
    """Agent configuration information"""
    config_id: str
    name: str
    model: str
    provider: str
    system_prompt: str
    tool_policies: Dict[str, Any]
    thresholds: Dict[str, Any]
    tags: List[str]
    status: str
    sequence: Optional[int]
    created_at: str
    updated_at: str


class ConfigActivateRequest(BaseModel):
    """Request to activate a configuration"""
    config_id: str


class EvalRunRequest(BaseModel):
    """Request to run eval harness"""
    config_id: str


class EvalReportInfo(BaseModel):
    """Eval report information"""
    eval_report_id: str
    config_id: str
    sequence: Optional[int]
    total_cases: int
    passed: int
    failed: int
    score: float
    results: List[Dict[str, Any]]
    created_at: str


# ===== v1.8 Bonds Schemas =====


class BondPriceRequest(BaseModel):
    """Request to calculate bond price from yield"""
    face_value: float
    coupon_rate: float
    years_to_maturity: float
    yield_to_maturity: float
    periods_per_year: int = 2


class BondPriceResponse(BaseModel):
    """Bond price response"""
    price: float


class BondYieldRequest(BaseModel):
    """Request to calculate yield from price"""
    face_value: float
    coupon_rate: float
    years_to_maturity: float
    price: float
    periods_per_year: int = 2


class BondYieldResponse(BaseModel):
    """Bond yield response"""
    yield_to_maturity: float


class BondRiskRequest(BaseModel):
    """Request to calculate bond risk metrics"""
    face_value: float
    coupon_rate: float
    years_to_maturity: float
    yield_to_maturity: float
    periods_per_year: int = 2


class BondRiskResponse(BaseModel):
    """Bond risk metrics response"""
    price: float
    duration: float
    modified_duration: float
    convexity: float


# === v1.9 Caching Schemas ===


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    size: int
    hits: int
    misses: int
    hit_rate: float


class CacheClearResponse(BaseModel):
    """Cache clear response"""
    cleared: int
    status: str = "success"

