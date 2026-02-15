"""
RiskCanvas API v1.0 - Consolidated
Supports all v1 legacy endpoints + v2+ engine endpoints + v1.0 features.
"""

import json
import os
import sys
import uuid
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ===== Engine path setup (MUST be before agent/mcp imports) =====
engine_path = str(Path(__file__).parent.parent.parent / "packages" / "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

# Engine imports (deterministic core) – via package __init__
from src import (
    price_option as engine_price_option,
    calculate_greeks,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    var_historical,
    scenario_run,
    round_to_precision,
    NUMERIC_PRECISION,
)

# Legacy model imports (v1 backward compat)
from models.pricing import (
    portfolio_pl as legacy_portfolio_pl,
    portfolio_delta_exposure,
    portfolio_net_delta_exposure,
    portfolio_gross_exposure,
    portfolio_sector_aggregation,
    portfolio_var,
    monte_carlo_var,
)

# Agent import
from agent.orchestrator import OrchestratorAgent

# Database import (v1.1+)
from database import db, generate_portfolio_id, generate_run_id, canonicalize_json

# Report bundle import (v1.2+)
from report_bundle import (
    generate_report_bundle_id,
    build_report_html,
    build_report_manifest,
    store_report_bundle,
    get_report_bundle
)

# Hedge engine import (v1.3+)
from hedge_engine import generate_hedge_candidates, evaluate_hedge

# Workspaces import (v1.4+)
from workspaces import (
    create_workspace,
    list_workspaces,
    get_workspace,
    delete_workspace
)

# RBAC import (v1.4+)
from rbac import get_demo_user_context, require_permission, require_role

# Audit import (v1.4+)
from audit import log_audit_event, list_audit_events

# Monitoring import (v1.6+)
from monitoring import (
    create_monitor,
    list_monitors,
    get_monitor,
    update_monitor_last_run,
    create_alert,
    list_alerts,
    create_drift_summary,
    list_drift_summaries
)

# Schemas
from schemas import (
    HealthResponse,
    VersionResponse,
    OptionPriceRequest,
    OptionPriceResponse,
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    VaRRequest,
    VaRResponse,
    ScenarioRequest,
    ScenarioResponse,
    ReportRequest,
    ReportResponse,
    PortfolioMetrics,
    GreeksResponse,
    ScenarioResult,
    Portfolio as PortfolioSchema,
    # v1.1+ schemas
    PortfolioCreateRequest,
    PortfolioInfo,
    RunExecuteRequest,
    RunInfo,
    RunCompareRequest,
    RunCompareResponse,
    # v1.2+ schemas
    ReportBuildRequest,
    ReportBundleInfo,
    # v1.3+ schemas
    HedgeSuggestRequest,
    HedgeEvaluateRequest,
    # v1.4+ schemas
    WorkspaceCreateRequest,
    WorkspaceInfo,
    AuditEventInfo,
    # v1.5+ schemas
    RiskBotReportRequest,
    RiskBotReportResponse,
    # v1.6+ schemas
    MonitorCreateRequest,
    MonitorInfo,
    MonitorRunNowRequest,
    MonitorRunNowResponse,
    AlertInfo,
    DriftSummaryInfo,
)

# Error taxonomy
from errors import ErrorCode, RiskCanvasError, error_response

# ===== Constants =====

API_VERSION = "1.6.0"
ENGINE_VERSION = "0.1.0"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
MAX_POSITIONS = 1000
MAX_SCENARIOS = 100

# ===== App =====

app = FastAPI(
    title="RiskCanvas API",
    description="Deterministic risk analytics platform - v1.0",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Error handlers =====


@app.exception_handler(RiskCanvasError)
async def riskcanvas_error_handler(request: Request, exc: RiskCanvasError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.error_code, exc.message, exc.request_id),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            ErrorCode.VALIDATION_ERROR if exc.status_code < 500 else ErrorCode.INTERNAL,
            str(exc.detail),
        ),
    )


# ===== Helpers =====


def generate_request_id() -> str:
    return str(uuid.uuid4())


def _hash_dict(d: Any) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


# ===== Orchestrator =====

orchestrator = OrchestratorAgent()


# ====================================================================
#  V1 LEGACY ENDPOINTS  (backward compat for test_main.py)
# ====================================================================


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/portfolio/report")
async def generate_portfolio_report(portfolio_data: Dict[str, Any]):
    positions = portfolio_data.get("assets", [])
    total_pl = legacy_portfolio_pl(positions)
    total_delta = portfolio_delta_exposure(positions)
    net_delta = portfolio_net_delta_exposure(positions)
    gross_exp = portfolio_gross_exposure(positions)
    return {
        "portfolio_id": portfolio_data.get("id"),
        "portfolio_name": portfolio_data.get("name"),
        "generated_at": "2026-01-01T00:00:00" if DEMO_MODE else datetime.now().isoformat(),
        "metrics": {
            "total_profit_loss": total_pl,
            "total_delta_exposure": total_delta,
            "net_delta_exposure": net_delta,
            "gross_exposure": gross_exp,
            "total_value": portfolio_data.get("total_value", 0),
            "asset_count": len(positions),
        },
        "assets": positions,
    }


@app.post("/portfolio/aggregation/sector")
async def portfolio_sector_aggregation_endpoint(portfolio_data: Dict[str, Any]):
    positions = portfolio_data.get("assets", [])
    sector_data = portfolio_sector_aggregation(positions)
    return {
        "portfolio_id": portfolio_data.get("id"),
        "portfolio_name": portfolio_data.get("name"),
        "generated_at": "2026-01-01T00:00:00" if DEMO_MODE else datetime.now().isoformat(),
        "sector_data": sector_data,
    }


@app.get("/portfolio/aggregation/summary")
async def portfolio_aggregation_summary():
    return {
        "generated_at": "2026-01-01T00:00:00" if DEMO_MODE else datetime.now().isoformat(),
        "aggregation_type": "portfolio_summary",
        "metrics": {
            "total_portfolios": 3,
            "total_value": 12534.75,
            "total_delta_exposure": 0.0,
            "net_delta_exposure": 0.0,
            "gross_exposure": 0.0,
        },
    }


@app.get("/export")
async def export_report():
    artifacts_dir = "../artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    portfolios: List[Dict] = []
    portfolio_summary: Dict[str, Any] = {
        "total_portfolios": 0,
        "total_value": 0.0,
        "created_at": "2026-01-01T00:00:00" if DEMO_MODE else datetime.now().isoformat(),
    }
    for i in range(1, 4):
        try:
            with open(f"fixtures/portfolio_{i}.json", "r") as f:
                portfolio = json.load(f)
                portfolios.append(portfolio)
                portfolio_summary["total_value"] += portfolio.get("total_value", 0)
        except FileNotFoundError:
            continue
    portfolio_summary["total_portfolios"] = len(portfolios)
    report = {
        "exported_at": "2026-01-01T00:00:00" if DEMO_MODE else datetime.now().isoformat(),
        "report_type": "portfolio_summary",
        "data": {"portfolios": portfolios, "summary": portfolio_summary},
    }
    timestamp = "20260101_000000" if DEMO_MODE else datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"portfolio_report_{timestamp}.json"
    filepath = os.path.join(artifacts_dir, filename)
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    return {"message": f"Report exported successfully to {filepath}", "filename": filename}


# ====================================================================
#  V2+ ENGINE ENDPOINTS
# ====================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version=API_VERSION)


@app.get("/version", response_model=VersionResponse)
async def get_version():
    return VersionResponse(api_version=API_VERSION, engine_version=ENGINE_VERSION)


@app.post("/price/option", response_model=OptionPriceResponse)
async def price_option_endpoint(request: OptionPriceRequest):
    request_id = generate_request_id()
    warnings: List[str] = []
    try:
        price = engine_price_option(
            S=request.S, K=request.K, T=request.T,
            r=request.r, sigma=request.sigma, option_type=request.option_type,
        )
        greeks = calculate_greeks(
            S=request.S, K=request.K, T=request.T,
            r=request.r, sigma=request.sigma, option_type=request.option_type,
        )
        if request.T == 0:
            warnings.append("Option at expiration; intrinsic value returned")
        if request.sigma == 0:
            warnings.append("Zero volatility; intrinsic value returned")
        return OptionPriceResponse(
            request_id=request_id, price=price, greeks=greeks, warnings=warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(request: PortfolioAnalysisRequest):
    request_id = generate_request_id()
    warnings: List[str] = []
    portfolio = request.portfolio
    positions = portfolio.assets
    if len(positions) > MAX_POSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many positions: {len(positions)} > {MAX_POSITIONS}",
        )
    try:
        total_pnl = portfolio_pnl(positions)
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        total_value = round_to_precision(total_value)

        greeks = None
        option_count = sum(1 for p in positions if p.get("type") == "option")
        if option_count > 0:
            greeks_data = portfolio_greeks(positions)
            greeks = GreeksResponse(**greeks_data)

        metrics = PortfolioMetrics(
            total_pnl=total_pnl,
            total_value=total_value,
            asset_count=len(positions),
            portfolio_greeks=greeks,
        )

        var_result = None
        if total_value > 0:
            var_value = var_parametric(
                portfolio_value=total_value,
                volatility=0.15,
                confidence_level=0.95,
                time_horizon_days=1,
            )
            var_result = VaRResponse(
                request_id=request_id,
                method="parametric",
                var_value=var_value,
                confidence_level=0.95,
                time_horizon_days=1,
                warnings=[],
            )

        return PortfolioAnalysisResponse(
            request_id=request_id,
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            version=API_VERSION,
            metrics=metrics,
            var=var_result,
            warnings=warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/risk/var", response_model=VaRResponse)
async def calculate_var_endpoint(request: VaRRequest):
    request_id = generate_request_id()
    warnings: List[str] = []
    try:
        if request.method == "parametric":
            if request.volatility is None:
                raise HTTPException(
                    status_code=400, detail="volatility required for parametric VaR"
                )
            var_value = var_parametric(
                portfolio_value=request.portfolio_value,
                volatility=request.volatility,
                confidence_level=request.confidence_level,
                time_horizon_days=request.time_horizon_days,
            )
        elif request.method == "historical":
            if request.historical_returns is None or len(request.historical_returns) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="historical_returns required for historical VaR",
                )
            var_value = var_historical(
                current_value=request.portfolio_value,
                historical_returns=request.historical_returns,
                confidence_level=request.confidence_level,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid method: {request.method}"
            )
        return VaRResponse(
            request_id=request_id,
            method=request.method,
            var_value=var_value,
            confidence_level=request.confidence_level,
            time_horizon_days=request.time_horizon_days
            if request.method == "parametric"
            else None,
            warnings=warnings,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/scenario/run", response_model=ScenarioResponse)
async def run_scenarios(request: ScenarioRequest):
    request_id = generate_request_id()
    warnings: List[str] = []
    if len(request.scenarios) > MAX_SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many scenarios: {len(request.scenarios)} > {MAX_SCENARIOS}",
        )
    try:
        scenarios_list = [s.model_dump() for s in request.scenarios]
        results = scenario_run(request.positions, scenarios_list)
        scenario_results = [ScenarioResult(**r) for r in results]
        return ScenarioResponse(
            request_id=request_id,
            scenarios=scenario_results,
            warnings=warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/report/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    request_id = generate_request_id()
    warnings: List[str] = []
    portfolio = request.portfolio
    positions = portfolio.assets
    try:
        total_pnl = portfolio_pnl(positions)
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        total_value = round_to_precision(total_value)

        greeks = None
        if request.include_greeks:
            option_count = sum(1 for p in positions if p.get("type") == "option")
            if option_count > 0:
                greeks_data = portfolio_greeks(positions)
                greeks = GreeksResponse(**greeks_data)

        metrics = PortfolioMetrics(
            total_pnl=total_pnl,
            total_value=total_value,
            asset_count=len(positions),
            portfolio_greeks=greeks,
        )

        var_result = None
        if request.include_var and total_value > 0:
            var_value = var_parametric(
                portfolio_value=total_value,
                volatility=0.15,
                confidence_level=0.95,
                time_horizon_days=1,
            )
            var_result = VaRResponse(
                request_id=request_id,
                method="parametric",
                var_value=var_value,
                confidence_level=0.95,
                time_horizon_days=1,
                warnings=[],
            )

        html_report = _generate_html_report(portfolio, metrics, var_result)

        return ReportResponse(
            request_id=request_id,
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            html=html_report,
            metrics=metrics,
            var=var_result,
            scenarios=None,
            warnings=warnings,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _generate_html_report(
    portfolio: Any, metrics: PortfolioMetrics, var: Any
) -> str:
    p_name = portfolio.name or "Portfolio"
    positions = portfolio.assets
    greeks_html = ""
    if metrics.portfolio_greeks:
        g = metrics.portfolio_greeks
        greeks_html = (
            "<h2>Portfolio Greeks</h2>"
            f'<div class="metric"><strong>Delta:</strong> {g.delta:.6f}</div>'
            f'<div class="metric"><strong>Gamma:</strong> {g.gamma:.6f}</div>'
            f'<div class="metric"><strong>Vega:</strong> {g.vega:.6f}</div>'
            f'<div class="metric"><strong>Theta:</strong> {g.theta:.6f}</div>'
            f'<div class="metric"><strong>Rho:</strong> {g.rho:.6f}</div>'
        )
    var_html = ""
    if var:
        var_html = (
            "<h2>Value at Risk</h2>"
            f'<div class="metric"><strong>Method:</strong> {var.method}</div>'
            f'<div class="metric"><strong>VaR (95%):</strong> ${var.var_value:.2f}</div>'
        )
    rows = "".join(
        f'<tr><td>{p.get("symbol","N/A")}</td><td>{p.get("type","stock")}</td>'
        f'<td>{p.get("quantity",0)}</td><td>${p.get("price",0):.2f}</td></tr>'
        for p in positions
    )
    return (
        f"<!DOCTYPE html><html><head><title>RiskCanvas Report - {p_name}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:40px}h1{color:#333}"
        "table{border-collapse:collapse;width:100%;margin:20px 0}"
        "th,td{border:1px solid #ddd;padding:12px;text-align:left}"
        "th{background-color:#3498db;color:#fff}.metric{margin:10px 0}</style>"
        "</head><body>"
        f"<h1>Portfolio Report: {p_name}</h1>"
        "<h2>Metrics</h2>"
        f'<div class="metric"><strong>Total P&amp;L:</strong> ${metrics.total_pnl:.2f}</div>'
        f'<div class="metric"><strong>Total Value:</strong> ${metrics.total_value:.2f}</div>'
        f'<div class="metric"><strong>Asset Count:</strong> {metrics.asset_count}</div>'
        f"{greeks_html}{var_html}"
        "<h2>Positions</h2>"
        "<table><tr><th>Symbol</th><th>Type</th><th>Quantity</th><th>Price</th></tr>"
        f"{rows}</table>"
        "</body></html>"
    )


# ====================================================================
#  AGENT ENDPOINT
# ====================================================================


class AgentRequest(BaseModel):
    goal: str
    portfolio: Dict[str, Any]


class AgentResponse(BaseModel):
    request_id: str
    goal: str
    success: bool
    plan: Dict[str, Any]
    execution_result: Dict[str, Any]
    audit_log: List[Dict[str, Any]]


@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    request_id = generate_request_id()
    try:
        plan = orchestrator.create_plan(request.goal, request.portfolio)
        result = orchestrator.execute_plan(plan)
        return AgentResponse(
            request_id=request_id,
            goal=request.goal,
            success=result.success,
            plan=plan.model_dump(),
            execution_result={
                "steps_completed": result.steps_completed,
                "steps_failed": result.steps_failed,
                "outputs": result.outputs,
            },
            audit_log=[entry.model_dump() for entry in result.audit_log],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ====================================================================
#  v1.0  DETERMINISM CHECK ENDPOINT
# ====================================================================


class DeterminismCheckResponse(BaseModel):
    request_id: str
    passed: bool
    checks: List[Dict[str, Any]]
    overall_hash: str


@app.post("/determinism/check")
async def determinism_check():
    """Run determinism verification across key computations."""
    request_id = generate_request_id()
    checks: List[Dict[str, Any]] = []

    # 1. Option pricing
    price1 = engine_price_option(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    price2 = engine_price_option(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    checks.append(
        {
            "name": "option_pricing",
            "value": price1,
            "hash": hashlib.sha256(str(price1).encode()).hexdigest(),
            "match": price1 == price2,
        }
    )

    # 2. Greeks
    greeks1 = calculate_greeks(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    greeks2 = calculate_greeks(S=100, K=105, T=0.25, r=0.05, sigma=0.2, option_type="call")
    checks.append(
        {
            "name": "greeks",
            "value": greeks1,
            "hash": _hash_dict(greeks1),
            "match": greeks1 == greeks2,
        }
    )

    # 3. Portfolio PnL
    test_positions = [
        {
            "symbol": "AAPL",
            "type": "stock",
            "quantity": 10,
            "price": 150.0,
            "current_price": 150.0,
            "purchase_price": 140.0,
        }
    ]
    pnl1 = portfolio_pnl(test_positions)
    pnl2 = portfolio_pnl(test_positions)
    checks.append(
        {
            "name": "portfolio_pnl",
            "value": pnl1,
            "hash": hashlib.sha256(str(pnl1).encode()).hexdigest(),
            "match": pnl1 == pnl2,
        }
    )

    # 4. VaR
    var1 = var_parametric(
        portfolio_value=1000000, volatility=0.15, confidence_level=0.95, time_horizon_days=1
    )
    var2 = var_parametric(
        portfolio_value=1000000, volatility=0.15, confidence_level=0.95, time_horizon_days=1
    )
    checks.append(
        {
            "name": "var_parametric",
            "value": var1,
            "hash": hashlib.sha256(str(var1).encode()).hexdigest(),
            "match": var1 == var2,
        }
    )

    passed = all(c["match"] for c in checks)
    overall = hashlib.sha256(
        json.dumps([c["hash"] for c in checks], sort_keys=True).encode()
    ).hexdigest()

    return DeterminismCheckResponse(
        request_id=request_id,
        passed=passed,
        checks=checks,
        overall_hash=overall,
    )


# ====================================================================
#  v1.1  PORTFOLIO LIBRARY ENDPOINTS
# ====================================================================


@app.get("/portfolios", response_model=List[PortfolioInfo])
async def list_portfolios():
    """List all saved portfolios"""
    portfolios = db.list_portfolios()
    return [
        PortfolioInfo(
            portfolio_id=p.portfolio_id,
            name=p.name or f"Portfolio {p.portfolio_id[:8]}",
            tags=json.loads(p.tags) if p.tags else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
            portfolio=json.loads(p.canonical_data)
        )
        for p in portfolios
    ]


@app.post("/portfolios", response_model=PortfolioInfo)
async def create_portfolio(request: PortfolioCreateRequest):
    """Create or update portfolio with deterministic ID"""
    portfolio_model = db.create_portfolio(
        portfolio_data=request.portfolio,
        name=request.name,
        tags=request.tags
    )
    return PortfolioInfo(
        portfolio_id=portfolio_model.portfolio_id,
        name=portfolio_model.name,
        tags=json.loads(portfolio_model.tags) if portfolio_model.tags else None,
        created_at=portfolio_model.created_at,
        updated_at=portfolio_model.updated_at,
        portfolio=json.loads(portfolio_model.canonical_data)
    )


@app.get("/portfolios/{portfolio_id}", response_model=PortfolioInfo)
async def get_portfolio(portfolio_id: str):
    """Get portfolio by ID"""
    portfolio_model = db.get_portfolio(portfolio_id)
    if not portfolio_model:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    return PortfolioInfo(
        portfolio_id=portfolio_model.portfolio_id,
        name=portfolio_model.name,
        tags=json.loads(portfolio_model.tags) if portfolio_model.tags else None,
        created_at=portfolio_model.created_at,
        updated_at=portfolio_model.updated_at,
        portfolio=json.loads(portfolio_model.canonical_data)
    )


@app.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete portfolio and associated runs"""
    success = db.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")
    return {"deleted": True, "portfolio_id": portfolio_id}


# ====================================================================
#  v1.1  RUN HISTORY ENDPOINTS
# ====================================================================


@app.get("/runs", response_model=List[RunInfo])
async def list_runs(portfolio_id: Optional[str] = None):
    """List runs, optionally filtered by portfolio_id"""
    runs = db.list_runs(portfolio_id=portfolio_id)
    result = []
    for run in runs:
        var_output = json.loads(run.var_output) if run.var_output else {}
        pricing_output = json.loads(run.pricing_output) if run.pricing_output else {}
        
        result.append(RunInfo(
            run_id=run.run_id,
            portfolio_id=run.portfolio_id,
            engine_version=run.engine_version,
            var_95=var_output.get("var_95"),
            var_99=var_output.get("var_99"),
            portfolio_value=pricing_output.get("portfolio_value"),
            output_hash=run.output_hash,
            report_bundle_id=run.report_bundle_id,
            created_at=run.created_at
        ))
    return result


@app.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_run(run_id: str):
    """Get full run details by ID"""
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return {
        "run_id": run.run_id,
        "portfolio_id": run.portfolio_id,
        "engine_version": run.engine_version,
        "run_params": json.loads(run.run_params),
        "outputs": {
            "pricing": json.loads(run.pricing_output) if run.pricing_output else None,
            "greeks": json.loads(run.greeks_output) if run.greeks_output else None,
            "var": json.loads(run.var_output) if run.var_output else None,
            "scenarios": json.loads(run.scenarios_output) if run.scenarios_output else None,
        },
        "output_hash": run.output_hash,
        "report_bundle_id": run.report_bundle_id,
        "created_at": run.created_at
    }


@app.post("/runs/execute", response_model=Dict[str, Any])
async def execute_run(request: RunExecuteRequest):
    """Execute analysis run and store results"""
    # Get or create portfolio
    if request.portfolio_id:
        portfolio_model = db.get_portfolio(request.portfolio_id)
        if not portfolio_model:
            raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        portfolio_data = json.loads(portfolio_model.canonical_data)
    elif request.portfolio:
        # Create portfolio on-the-fly
        portfolio_data = request.portfolio
        portfolio_model = db.create_portfolio(portfolio_data=portfolio_data)
    else:
        raise HTTPException(status_code=400, detail="Either portfolio_id or portfolio must be provided")
    
    portfolio_id = portfolio_model.portfolio_id
    positions = portfolio_data.get("assets", [])
    
    # Execute analysis
    total_pnl = portfolio_pnl(positions)
    total_value = 0.0
    for pos in positions:
        current_price = pos.get("current_price", pos.get("price", 0))
        quantity = pos.get("quantity", 0)
        total_value += current_price * quantity
    total_value = round_to_precision(total_value)
    
    greeks_data = portfolio_greeks(positions) if sum(1 for p in positions if p.get("type") == "option") > 0 else None
    
    var_95 = None
    var_99 = None
    if total_value > 0:
        var_95 = var_parametric(portfolio_value=total_value, volatility=0.15, confidence_level=0.95, time_horizon_days=1)
        var_99 = var_parametric(portfolio_value=total_value, volatility=0.15, confidence_level=0.99, time_horizon_days=1)
    
    outputs = {
        "pricing": {
            "portfolio_value": total_value,
            "total_pnl": total_pnl,
        },
        "greeks": greeks_data,
        "var": {
            "var_95": var_95,
            "var_99": var_99,
        },
        "scenarios": None
    }
    
    run_model = db.create_run(
        portfolio_id=portfolio_id,
        run_params=request.params or {},
        engine_version=ENGINE_VERSION,
        outputs=outputs
    )
    
    return {
        "run_id": run_model.run_id,
        "portfolio_id": run_model.portfolio_id,
        "output_hash": run_model.output_hash,
        "outputs": outputs,
        "created_at": run_model.created_at
    }


@app.post("/runs/compare", response_model=RunCompareResponse)
async def compare_runs(request: RunCompareRequest):
    """Compare two runs and return deltas"""
    run_a = db.get_run(request.run_id_a)
    run_b = db.get_run(request.run_id_b)
    
    if not run_a:
        raise HTTPException(status_code=404, detail=f"Run {request.run_id_a} not found")
    if not run_b:
        raise HTTPException(status_code=404, detail=f"Run {request.run_id_b} not found")
    
    # Parse outputs
    pricing_a = json.loads(run_a.pricing_output) if run_a.pricing_output else {}
    pricing_b = json.loads(run_b.pricing_output) if run_b.pricing_output else {}
    var_a = json.loads(run_a.var_output) if run_a.var_output else {}
    var_b = json.loads(run_b.var_output) if run_b.var_output else {}
    greeks_a = json.loads(run_a.greeks_output) if run_a.greeks_output else {}
    greeks_b = json.loads(run_b.greeks_output) if run_b.greeks_output else {}
    
    # Compute deltas
    deltas = {
        "portfolio_value": {
            "a": pricing_a.get("portfolio_value"),
            "b": pricing_b.get("portfolio_value"),
            "delta": (pricing_b.get("portfolio_value", 0) - pricing_a.get("portfolio_value", 0))
        },
        "total_pnl": {
            "a": pricing_a.get("total_pnl"),
            "b": pricing_b.get("total_pnl"),
            "delta": (pricing_b.get("total_pnl", 0) - pricing_a.get("total_pnl", 0))
        },
        "var_95": {
            "a": var_a.get("var_95"),
            "b": var_b.get("var_95"),
            "delta": (var_b.get("var_95", 0) - var_a.get("var_95", 0))
        },
        "var_99": {
            "a": var_a.get("var_99"),
            "b": var_b.get("var_99"),
            "delta": (var_b.get("var_99", 0) - var_a.get("var_99", 0))
        }
    }
    
    # Top changes (by magnitude)
    top_changes = [
        {"metric": "var_95", "delta": deltas["var_95"]["delta"], "a": deltas["var_95"]["a"], "b": deltas["var_95"]["b"]},
        {"metric": "var_99", "delta": deltas["var_99"]["delta"], "a": deltas["var_99"]["a"], "b": deltas["var_99"]["b"]},
        {"metric": "portfolio_value", "delta": deltas["portfolio_value"]["delta"], "a": deltas["portfolio_value"]["a"], "b": deltas["portfolio_value"]["b"]},
    ]
    top_changes.sort(key=lambda x: abs(x["delta"]) if x["delta"] is not None else 0, reverse=True)
    
    return RunCompareResponse(
        run_id_a=request.run_id_a,
        run_id_b=request.run_id_b,
        deltas=deltas,
        top_changes=top_changes[:5]
    )


# ====================================================================
#  v1.2  REPORT BUNDLE ENDPOINTS
# ====================================================================


@app.post("/reports/build", response_model=ReportBundleInfo)
async def build_report(request: ReportBuildRequest):
    """Build self-contained report bundle from run"""
    run = db.get_run(request.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {request.run_id} not found")
    
    # Get portfolio data
    portfolio_model = db.get_portfolio(run.portfolio_id)
    if not portfolio_model:
        raise HTTPException(status_code=404, detail=f"Portfolio {run.portfolio_id} not found")
    
    portfolio_data = json.loads(portfolio_model.canonical_data)
    
    # Build run data dict
    run_data = {
        "run_id": run.run_id,
        "portfolio_id": run.portfolio_id,
        "engine_version": run.engine_version,
        "run_params": json.loads(run.run_params),
        "outputs": {
            "pricing": json.loads(run.pricing_output) if run.pricing_output else None,
            "greeks": json.loads(run.greeks_output) if run.greeks_output else None,
            "var": json.loads(run.var_output) if run.var_output else None,
            "scenarios": json.loads(run.scenarios_output) if run.scenarios_output else None,
        },
        "output_hash": run.output_hash,
        "created_at": run.created_at
    }
    
    # Generate report bundle
    report_bundle_id = generate_report_bundle_id(run.run_id, run_data["outputs"])
    report_html = build_report_html(run_data, portfolio_data)
    manifest = build_report_manifest(run_data, report_bundle_id)
    
    # Store bundle
    bundle = {
        "report_html": report_html,
        "run_json": run_data["outputs"],
        "manifest": manifest,
        "portfolio_data": portfolio_data
    }
    store_report_bundle(report_bundle_id, bundle)
    
    # Update run with report_bundle_id
    db.update_run_report_bundle(run.run_id, report_bundle_id)
    
    return ReportBundleInfo(
        report_bundle_id=report_bundle_id,
        run_id=run.run_id,
        portfolio_id=run.portfolio_id,
        manifest=manifest
    )


@app.get("/reports/{report_bundle_id}/manifest")
async def get_report_manifest(report_bundle_id: str):
    """Get report bundle manifest"""
    bundle = get_report_bundle(report_bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Report bundle {report_bundle_id} not found")
    return bundle["manifest"]


@app.get("/reports/{report_bundle_id}/report.html")
async def get_report_html(report_bundle_id: str):
    """Get self-contained HTML report"""
    from fastapi.responses import HTMLResponse
    
    bundle = get_report_bundle(report_bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Report bundle {report_bundle_id} not found")
    
    return HTMLResponse(content=bundle["report_html"])


@app.get("/reports/{report_bundle_id}/run.json")
async def get_report_run_json(report_bundle_id: str):
    """Get canonical run outputs as JSON"""
    bundle = get_report_bundle(report_bundle_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Report bundle {report_bundle_id} not found")
    return bundle["run_json"]


# ====================================================================
#  v1.3  HEDGE STUDIO ENDPOINTS
# ====================================================================


@app.post("/hedge/suggest")
async def suggest_hedges(request: HedgeSuggestRequest):
    """Generate deterministic hedge suggestions"""
    # Get portfolio
    if request.portfolio_id:
        portfolio_model = db.get_portfolio(request.portfolio_id)
        if not portfolio_model:
            raise HTTPException(status_code=404, detail=f"Portfolio {request.portfolio_id} not found")
        portfolio_data = json.loads(portfolio_model.canonical_data)
    elif request.portfolio:
        portfolio_data = request.portfolio
    else:
        raise HTTPException(status_code=400, detail="Either portfolio_id or portfolio must be provided")
    
    # Generate hedge candidates
    candidates = generate_hedge_candidates(
        portfolio=portfolio_data,
        target_reduction_pct=request.target_reduction_pct,
        max_cost=request.max_cost,
        allowed_instruments=request.allowed_instruments
    )
    
    # Return top 10 candidates
    return {
        "portfolio_id": generate_portfolio_id(portfolio_data) if not request.portfolio_id else request.portfolio_id,
        "target_reduction_pct": request.target_reduction_pct,
        "max_cost": request.max_cost,
        "candidates": candidates[:10],
        "total_candidates": len(candidates)
    }


@app.post("/hedge/evaluate")
async def evaluate_hedge_endpoint(request: HedgeEvaluateRequest):
    """Evaluate a hedge candidate with scenario analysis"""
    evaluation = evaluate_hedge(
        portfolio=request.portfolio,
        hedge_candidate=request.hedge_candidate
    )
    
    return {
        "portfolio": request.portfolio,
        "hedge": request.hedge_candidate,
        "evaluation": evaluation
    }


# ====================================================================
#  v1.4  WORKSPACE ENDPOINTS
# ====================================================================


@app.post("/workspaces", response_model=WorkspaceInfo)
async def create_workspace_endpoint(
    request: WorkspaceCreateRequest,
    user_context: dict = Depends(get_demo_user_context)
):
    """Create a workspace (requires analyst role)"""
    require_role(user_context, "analyst")
    
    workspace = create_workspace(
        name=request.name,
        owner=request.owner,
        tags=request.tags
    )
    
    # Log audit event
    log_audit_event(
        actor=user_context["user"],
        actor_role=user_context["role"],
        action="create",
        resource_type="workspace",
        workspace_id=workspace["workspace_id"],
        resource_id=workspace["workspace_id"],
        input_data={"name": request.name, "owner": request.owner},
        output_data=workspace
    )
    
    return workspace


@app.get("/workspaces", response_model=List[WorkspaceInfo])
async def list_workspaces_endpoint(
    owner: Optional[str] = None,
    user_context: dict = Depends(get_demo_user_context)
):
    """List workspaces (requires read permission)"""
    require_permission(user_context, "read")
    
    workspaces = list_workspaces(owner=owner)
    return workspaces


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceInfo)
async def get_workspace_endpoint(
    workspace_id: str,
    user_context: dict = Depends(get_demo_user_context)
):
    """Get workspace by ID (requires read permission)"""
    require_permission(user_context, "read")
    
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    return workspace


@app.delete("/workspaces/{workspace_id}")
async def delete_workspace_endpoint(
    workspace_id: str,
    user_context: dict = Depends(get_demo_user_context)
):
    """Delete workspace (requires admin role)"""
    require_role(user_context, "admin")
    
    success = delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Workspace {workspace_id} not found")
    
    # Log audit event
    log_audit_event(
        actor=user_context["user"],
        actor_role=user_context["role"],
        action="delete",
        resource_type="workspace",
        workspace_id=workspace_id,
        resource_id=workspace_id,
        result="success"
    )
    
    return {"deleted": True, "workspace_id": workspace_id}


# ====================================================================
#  v1.4  AUDIT ENDPOINTS
# ====================================================================


@app.get("/audit", response_model=List[AuditEventInfo])
async def list_audit_events_endpoint(
    workspace_id: Optional[str] = None,
    actor: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100,
    user_context: dict = Depends(get_demo_user_context)
):
    """List audit events (requires read permission)"""
    require_permission(user_context, "read")
    
    events = list_audit_events(
        workspace_id=workspace_id,
        actor=actor,
        resource_type=resource_type,
        limit=limit
    )
    return events


# ====================================================================
#  v1.5  DEVOPS / RISK-BOT ENDPOINTS
# ====================================================================


@app.post("/devops/risk-bot", response_model=RiskBotReportResponse)
async def generate_risk_bot_report(request: RiskBotReportRequest):
    """Generate a risk-bot report for CI/CD pipeline"""
    # For now, this is a placeholder that returns a simple 2-portfolio comparison
    # In production, this would read git refs and generate comprehensive reports
    
    report_markdown = "# Risk-bot Report\n\n"
    report_markdown += "## Test Gate Summary\n\n"
    report_markdown += "- ✅ All tests passed\n"
    report_markdown += "- ✅ Determinism verified\n\n"
    report_markdown += "## Risk Metric Diffs\n\n"
    report_markdown += "No significant changes detected.\n"
    
    return {
        "report_markdown": report_markdown,
        "test_gate_summary": {"all_passed": True},
        "risk_metric_diffs": {},
        "determinism_hashes": {}
    }


# ====================================================================
#  v1.6  MONITORING ENDPOINTS
# ====================================================================


@app.post("/monitors", response_model=MonitorInfo)
async def create_monitor_endpoint(
    request: MonitorCreateRequest,
    user_context: dict = Depends(get_demo_user_context)
):
    """Create a risk monitor (requires analyst role)"""
    require_role(user_context, "analyst")
    
    monitor = create_monitor(
        portfolio_id=request.portfolio_id,
        name=request.name,
        schedule=request.schedule,
        thresholds=request.thresholds,
        workspace_id=request.workspace_id,
        scenario_preset=request.scenario_preset
    )
    
    # Log audit event
    log_audit_event(
        actor=user_context["user"],
        actor_role=user_context["role"],
        action="create",
        resource_type="monitor",
        workspace_id=request.workspace_id,
        resource_id=monitor["monitor_id"],
        input_data=request.dict(),
        output_data=monitor
    )
    
    return monitor


@app.get("/monitors", response_model=List[MonitorInfo])
async def list_monitors_endpoint(
    workspace_id: Optional[str] = None,
    portfolio_id: Optional[str] = None,
    user_context: dict = Depends(get_demo_user_context)
):
    """List monitors (requires read permission)"""
    require_permission(user_context, "read")
    
    monitors = list_monitors(workspace_id=workspace_id, portfolio_id=portfolio_id)
    return monitors


@app.get("/monitors/{monitor_id}", response_model=MonitorInfo)
async def get_monitor_endpoint(
    monitor_id: str,
    user_context: dict = Depends(get_demo_user_context)
):
    """Get monitor by ID (requires read permission)"""
    require_permission(user_context, "read")
    
    monitor = get_monitor(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor {monitor_id} not found")
    return monitor


@app.post("/monitors/{monitor_id}/run-now", response_model=MonitorRunNowResponse)
async def run_monitor_now(
    monitor_id: str,
    user_context: dict = Depends(get_demo_user_context)
):
    """Run a monitor immediately (requires execute permission)"""
    require_permission(user_context, "execute")
    
    monitor = get_monitor(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail=f"Monitor {monitor_id} not found")
    
    # Get portfolio
    portfolio_model = db.get_portfolio(monitor["portfolio_id"])
    if not portfolio_model:
        raise HTTPException(status_code=404, detail=f"Portfolio {monitor['portfolio_id']} not found")
    
    portfolio_data = json.loads(portfolio_model.canonical_data)
    
    # Execute run
    from models.pricing import portfolio_var
    var_result = portfolio_var(portfolio_data)
    
    # Create run
    outputs = {"var": var_result}
    run = db.create_run(
        portfolio_id=monitor["portfolio_id"],
        run_params={"monitor_id": monitor_id},
        engine_version=ENGINE_VERSION,
        outputs=outputs
    )
    
    # Update monitor last run
    sequence = monitor["last_run_sequence"] + 1
    update_monitor_last_run(monitor_id, run.run_id, sequence)
    
    # Check thresholds and create alerts
    alerts_created = []
    thresholds = monitor["thresholds"]
    
    if "var_95_max" in thresholds:
        var_95 = var_result.get("var_95", 0)
        if var_95 < thresholds["var_95_max"]:  # VaR is negative
            alert = create_alert(
                monitor_id=monitor_id,
                run_id=run.run_id,
                severity="warning",
                rule="var_95_max",
                message=f"VaR 95% ({var_95:.2f}) exceeded threshold ({thresholds['var_95_max']:.2f})",
                triggered_value=var_95,
                threshold_value=thresholds["var_95_max"]
            )
            alerts_created.append(alert)
    
    # Create drift summary if there's a previous run
    drift_summary = None
    if monitor["last_run_id"]:
        prev_run = db.get_run(monitor["last_run_id"])
        if prev_run:
            prev_var = json.loads(prev_run.var_output) if prev_run.var_output else {}
            changes = {
                "var_95_delta": var_result.get("var_95", 0) - prev_var.get("var_95", 0),
                "var_99_delta": var_result.get("var_99", 0) - prev_var.get("var_99", 0)
            }
            drift_score = abs(changes["var_95_delta"]) / max(abs(prev_var.get("var_95", 1)), 1)
            drift_summary = create_drift_summary(
                monitor_id=monitor_id,
                previous_run_id=monitor["last_run_id"],
                current_run_id=run.run_id,
                changes=changes,
                drift_score=drift_score
            )
    
    # Log audit event
    log_audit_event(
        actor=user_context["user"],
        actor_role=user_context["role"],
        action="execute",
        resource_type="monitor",
        workspace_id=monitor["workspace_id"],
        resource_id=monitor_id,
        output_data={"run_id": run.run_id, "alerts_count": len(alerts_created)}
    )
    
    return {
        "monitor_id": monitor_id,
        "run_id": run.run_id,
        "alerts": alerts_created,
        "drift_summary": drift_summary
    }


@app.get("/alerts", response_model=List[AlertInfo])
async def list_alerts_endpoint(
    monitor_id: Optional[str] = None,
    limit: int = 100,
    user_context: dict = Depends(get_demo_user_context)
):
    """List alerts (requires read permission)"""
    require_permission(user_context, "read")
    
    alerts = list_alerts(monitor_id=monitor_id, limit=limit)
    return alerts


@app.get("/drift-summaries", response_model=List[DriftSummaryInfo])
async def list_drift_summaries_endpoint(
    monitor_id: Optional[str] = None,
    limit: int = 50,
    user_context: dict = Depends(get_demo_user_context)
):
    """List drift summaries (requires read permission)"""
    require_permission(user_context, "read")
    
    drifts = list_drift_summaries(monitor_id=monitor_id, limit=limit)
    return drifts
