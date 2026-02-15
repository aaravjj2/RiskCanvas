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
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
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
)

# Error taxonomy
from errors import ErrorCode, RiskCanvasError, error_response

# ===== Constants =====

API_VERSION = "1.0.0"
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