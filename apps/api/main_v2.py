"""
RiskCanvas API - FastAPI Backend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
import uuid
from typing import Dict, Any

# Add engine to path
engine_path = str(Path(__file__).parent.parent.parent / "packages" / "engine" / "src")
sys.path.insert(0, engine_path)

# Import engine functions
from pricing import price_option
from greeks import calculate_greeks
from portfolio import portfolio_pnl, portfolio_greeks
from var import var_parametric, var_historical
from scenario import scenario_run

# Import schemas
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
)

API_VERSION = "0.2.0"
ENGINE_VERSION = "0.1.0"

app = FastAPI(
    title="RiskCanvas API",
    description="Deterministic risk analytics platform",
    version=API_VERSION
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_request_id() -> str:
    """Generate a deterministic request ID (for demo/test mode)"""
    return str(uuid.uuid4())


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=API_VERSION
    )


@app.get("/version", response_model=VersionResponse)
async def get_version():
    """Get version information"""
    return VersionResponse(
        api_version=API_VERSION,
        engine_version=ENGINE_VERSION
    )


@app.post("/price/option", response_model=OptionPriceResponse)
async def price_option_endpoint(request: OptionPriceRequest):
    """
    Price a European option using Black-Scholes model.
    """
    request_id = generate_request_id()
    warnings = []
    
    try:
        price = price_option(
            S=request.S,
            K=request.K,
            T=request.T,
            r=request.r,
            sigma=request.sigma,
            option_type=request.option_type
        )
        
        greeks = calculate_greeks(
            S=request.S,
            K=request.K,
            T=request.T,
            r=request.r,
            sigma=request.sigma,
            option_type=request.option_type
        )
        
        if request.T == 0:
            warnings.append("Option at expiration; intrinsic value returned")
        if request.sigma == 0:
            warnings.append("Zero volatility; intrinsic value returned")
        
        return OptionPriceResponse(
            request_id=request_id,
            price=price,
            greeks=greeks,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze/portfolio", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(request: PortfolioAnalysisRequest):
    """
    Comprehensive portfolio analysis including P&L, Greeks, and VaR.
    """
    request_id = generate_request_id()
    warnings = []
    portfolio = request.portfolio
    positions = portfolio.assets
    
    try:
        # Calculate P&L
        total_pnl = portfolio_pnl(positions)
        
        # Calculate total value
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        
        # Calculate portfolio Greeks (for options only)
        greeks = None
        option_count = sum(1 for p in positions if p.get("type") == "option")
        if option_count > 0:
            portfolio_greeks_data = portfolio_greeks(positions)
            greeks = GreeksResponse(**portfolio_greeks_data)
        
        metrics = PortfolioMetrics(
            total_pnl=total_pnl,
            total_value=total_value,
            asset_count=len(positions),
            portfolio_greeks=greeks
        )
        
        # Calculate VaR (parametric with default params)
        var_result = None
        if total_value > 0:
            var_value = var_parametric(
                portfolio_value=total_value,
                volatility=0.15,  # Default 15% volatility
                confidence_level=0.95,
                time_horizon_days=1
            )
            var_result = VaRResponse(
                request_id=request_id,
                method="parametric",
                var_value=var_value,
                confidence_level=0.95,
                time_horizon_days=1,
                warnings=[]
            )
        
        return PortfolioAnalysisResponse(
            request_id=request_id,
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            version=API_VERSION,
            metrics=metrics,
            var=var_result,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/risk/var", response_model=VaRResponse)
async def calculate_var(request: VaRRequest):
    """
    Calculate Value at Risk (VaR) for a portfolio.
    """
    request_id = generate_request_id()
    warnings = []
    
    try:
        if request.method == "parametric":
            if request.volatility is None:
                raise HTTPException(status_code=400, detail="volatility required for parametric VaR")
            
            var_value = var_parametric(
                portfolio_value=request.portfolio_value,
                volatility=request.volatility,
                confidence_level=request.confidence_level,
                time_horizon_days=request.time_horizon_days
            )
        elif request.method == "historical":
            if request.historical_returns is None or len(request.historical_returns) == 0:
                raise HTTPException(status_code=400, detail="historical_returns required for historical VaR")
            
            var_value = var_historical(
                current_value=request.portfolio_value,
                historical_returns=request.historical_returns,
                confidence_level=request.confidence_level
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid method: {request.method}")
        
        return VaRResponse(
            request_id=request_id,
            method=request.method,
            var_value=var_value,
            confidence_level=request.confidence_level,
            time_horizon_days=request.time_horizon_days if request.method == "parametric" else None,
            warnings=warnings
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/scenario/run", response_model=ScenarioResponse)
async def run_scenarios(request: ScenarioRequest):
    """
    Run stress test scenarios on a portfolio.
    """
    request_id = generate_request_id()
    warnings = []
    
    try:
        scenarios_list = [s.model_dump() for s in request.scenarios]
        results = scenario_run(request.positions, scenarios_list)
        
        scenario_results = [ScenarioResult(**r) for r in results]
        
        return ScenarioResponse(
            request_id=request_id,
            scenarios=scenario_results,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/report/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a comprehensive portfolio report.
    """
    request_id = generate_request_id()
    warnings = []
    portfolio = request.portfolio
    positions = portfolio.assets
    
    try:
        # Calculate metrics
        total_pnl = portfolio_pnl(positions)
        
        total_value = 0.0
        for pos in positions:
            current_price = pos.get("current_price", pos.get("price", 0))
            quantity = pos.get("quantity", 0)
            total_value += current_price * quantity
        
        greeks = None
        if request.include_greeks:
            option_count = sum(1 for p in positions if p.get("type") == "option")
            if option_count > 0:
                portfolio_greeks_data = portfolio_greeks(positions)
                greeks = GreeksResponse(**portfolio_greeks_data)
        
        metrics = PortfolioMetrics(
            total_pnl=total_pnl,
            total_value=total_value,
            asset_count=len(positions),
            portfolio_greeks=greeks
        )
        
        # VaR
        var_result = None
        if request.include_var and total_value > 0:
            var_value = var_parametric(
                portfolio_value=total_value,
                volatility=0.15,
                confidence_level=0.95,
                time_horizon_days=1
            )
            var_result = VaRResponse(
                request_id=request_id,
                method="parametric",
                var_value=var_value,
                confidence_level=0.95,
                time_horizon_days=1,
                warnings=[]
            )
        
        # Generate HTML report
        html_report = _generate_html_report(portfolio, metrics, var_result)
        
        return ReportResponse(
            request_id=request_id,
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            html=html_report,
            metrics=metrics,
            var=var_result,
            scenarios=None,
            warnings=warnings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _generate_html_report(portfolio: Any, metrics: PortfolioMetrics, var: Any) -> str:
    """Generate deterministic HTML report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>RiskCanvas Report - {portfolio.name or 'Portfolio'}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .metric {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>Portfolio Report: {portfolio.name or 'Unnamed'}</h1>
        
        <h2>Metrics</h2>
        <div class="metric"><strong>Total P&L:</strong> ${metrics.total_pnl:.2f}</div>
        <div class="metric"><strong>Total Value:</strong> ${metrics.total_value:.2f}</div>
        <div class="metric"><strong>Asset Count:</strong> {metrics.asset_count}</div>
        
        {f'''<h2>Portfolio Greeks</h2>
        <div class="metric"><strong>Delta:</strong> {metrics.portfolio_greeks.delta:.6f}</div>
        <div class="metric"><strong>Gamma:</strong> {metrics.portfolio_greeks.gamma:.6f}</div>
        <div class="metric"><strong>Vega:</strong> {metrics.portfolio_greeks.vega:.6f}</div>
        <div class="metric"><strong>Theta:</strong> {metrics.portfolio_greeks.theta:.6f}</div>
        <div class="metric"><strong>Rho:</strong> {metrics.portfolio_greeks.rho:.6f}</div>
        ''' if metrics.portfolio_greeks else ''}
        
        {f'''<h2>Value at Risk</h2>
        <div class="metric"><strong>Method:</strong> {var.method}</div>
        <div class="metric"><strong>VaR (95%):</strong> ${var.var_value:.2f}</div>
        ''' if var else ''}
        
        <h2>Positions</h2>
        <table>
            <tr>
                <th>Symbol</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
            {''.join(f'<tr><td>{p.get("symbol", "N/A")}</td><td>{p.get("type", "stock")}</td><td>{p.get("quantity", 0)}</td><td>${p.get("price", 0):.2f}</td></tr>' for p in portfolio.assets)}
        </table>
    </body>
    </html>
    """
    return html
