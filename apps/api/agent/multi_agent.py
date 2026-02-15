"""
Multi-Agent System for RiskCanvas
Implements IntakeAgent, RiskAgent, and ReportAgent with strict contracts
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum
import sys
from pathlib import Path

# Add engine to path
engine_path = str(Path(__file__).parent.parent.parent.parent / "packages" / "engine")
if engine_path not in sys.path:
    sys.path.insert(0, engine_path)

from src import (
    price_option,
    calculate_greeks,
    portfolio_pnl,
    portfolio_greeks,
    var_parametric,
    var_historical,
    scenario_run,
)

from llm.providers import LLMFactory


# ===== Data Contracts =====


class AgentStatus(str, Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Position(BaseModel):
    """Validated position model"""
    symbol: str
    type: str = "stock"
    quantity: float
    price: Optional[float] = None
    current_price: Optional[float] = None
    purchase_price: Optional[float] = None
    # Option-specific fields
    S: Optional[float] = None
    K: Optional[float] = None
    T: Optional[float] = None
    r: Optional[float] = None
    sigma: Optional[float] = None
    option_type: Optional[str] = None


class NormalizedPortfolio(BaseModel):
    """Normalized and validated portfolio"""
    id: Optional[str] = None
    name: str
    positions: List[Position]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskMetrics(BaseModel):
    """Computed risk metrics"""
    total_pnl: float
    total_value: float
    asset_count: int
    portfolio_greeks: Optional[Dict[str, float]] = None
    var_parametric: Optional[float] = None
    var_confidence: Optional[float] = None
    scenario_results: Optional[List[Dict[str, Any]]] = None


class ReportOutput(BaseModel):
    """Final report output"""
    portfolio_name: str
    summary: str
    risk_metrics: RiskMetrics
    recommendations: List[str]
    html_report: Optional[str] = None


class AgentHandoff(BaseModel):
    """Handoff between agents"""
    from_agent: str
    to_agent: str
    data: Dict[str, Any]
    hash: str
    timestamp: Optional[str] = None


# ===== Agents =====


class IntakeAgent:
    """
    Validates input, normalizes portfolio, identifies missing fields.
    """
    
    def __init__(self):
        self.name = "IntakeAgent"
        self.status = AgentStatus.PENDING
    
    def process(self, raw_portfolio: Dict[str, Any]) -> NormalizedPortfolio:
        """
        Validate and normalize portfolio data.
        
        Args:
            raw_portfolio: Raw portfolio input
        
        Returns:
            NormalizedPortfolio with validated data
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Extract and validate positions
            raw_positions = raw_portfolio.get("assets", [])
            
            normalized_positions = []
            for pos in raw_positions:
                # Ensure required fields
                if "symbol" not in pos or "quantity" not in pos:
                    raise ValueError(f"Position missing required fields: {pos}")
                
                # Normalize price fields
                if "current_price" not in pos and "price" in pos:
                    pos["current_price"] = pos["price"]
                
                if "purchase_price" not in pos and "current_price" in pos:
                    # Default to 5% gain if purchase price not provided
                    pos["purchase_price"] = pos["current_price"] * 0.95
                
                # Validate option fields
                if pos.get("type") == "option":
                    required_option_fields = ["S", "K", "T", "r", "sigma"]
                    missing = [f for f in required_option_fields if f not in pos]
                    if missing:
                        raise ValueError(f"Option position missing fields: {missing}")
                
                normalized_positions.append(Position(**pos))
            
            # Create normalized portfolio
            normalized = NormalizedPortfolio(
                id=raw_portfolio.get("id"),
                name=raw_portfolio.get("name", "Unnamed Portfolio"),
                positions=normalized_positions,
                metadata={
                    "validated_by": self.name,
                    "position_count": len(normalized_positions)
                }
            )
            
            self.status = AgentStatus.COMPLETED
            return normalized
        
        except Exception as e:
            self.status = AgentStatus.FAILED
            raise ValueError(f"IntakeAgent validation failed: {str(e)}")


class RiskAgent:
    """
    Runs deterministic computations (engine/API).
    """
    
    def __init__(self):
        self.name = "RiskAgent"
        self.status = AgentStatus.PENDING
    
    def process(self, portfolio: NormalizedPortfolio) -> RiskMetrics:
        """
        Calculate risk metrics for portfolio.
        
        Args:
            portfolio: Normalized portfolio
        
        Returns:
            RiskMetrics with all computations
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Convert positions to dicts for engine functions (exclude None to avoid breaking scenario_run)
            positions_dict = [p.model_dump(exclude_none=True) for p in portfolio.positions]
            
            # Calculate P&L
            total_pnl = portfolio_pnl(positions_dict)
            
            # Calculate total value
            total_value = 0.0
            for pos in portfolio.positions:
                current_price = pos.current_price or pos.price or 0
                total_value += current_price * pos.quantity
            
            # Calculate Greeks (if options present)
            greeks = None
            has_options = any(p.type == "option" for p in portfolio.positions)
            if has_options:
                greeks = portfolio_greeks(positions_dict)
            
            # Calculate VaR
            var_value = None
            var_confidence = None
            if total_value > 0:
                var_value = var_parametric(
                    portfolio_value=total_value,
                    volatility=0.15,
                    confidence_level=0.95,
                    time_horizon_days=1
                )
                var_confidence = 0.95
            
            # Run stress scenarios
            scenarios = [
                {
                    "name": "Market Crash -20%",
                    "shock_type": "price",
                    "parameters": {"price_change_pct": -20.0}
                },
                {
                    "name": "Volatility Spike +50%",
                    "shock_type": "volatility",
                    "parameters": {"volatility_change_pct": 50.0}
                }
            ]
            scenario_results = scenario_run(positions_dict, scenarios)
            
            metrics = RiskMetrics(
                total_pnl=total_pnl,
                total_value=total_value,
                asset_count=len(portfolio.positions),
                portfolio_greeks=greeks,
                var_parametric=var_value,
                var_confidence=var_confidence,
                scenario_results=scenario_results
            )
            
            self.status = AgentStatus.COMPLETED
            return metrics
        
        except Exception as e:
            self.status = AgentStatus.FAILED
            raise RuntimeError(f"RiskAgent computation failed: {str(e)}")


class ReportAgent:
    """
    Generates narrative + charts strictly from computed results (no hallucinated numbers).
    """
    
    def __init__(self, llm_provider=None):
        self.name = "ReportAgent"
        self.status = AgentStatus.PENDING
        self.llm = llm_provider or LLMFactory.get_default_provider()
    
    def process(self, portfolio: NormalizedPortfolio, metrics: RiskMetrics) -> ReportOutput:
        """
        Generate report from computed metrics.
        
        Args:
            portfolio: Normalized portfolio
            metrics: Computed risk metrics
        
        Returns:
            ReportOutput with narrative and recommendations
        """
        self.status = AgentStatus.RUNNING
        
        try:
            # Generate narrative using LLM (only for interpretation, not for numbers)
            prompt = self._build_prompt(portfolio, metrics)
            summary = self.llm.generate(prompt)
            
            # Generate deterministic recommendations based on metrics
            recommendations = self._generate_recommendations(metrics)
            
            # Generate HTML report
            html_report = self._generate_html(portfolio, metrics, summary)
            
            report = ReportOutput(
                portfolio_name=portfolio.name,
                summary=summary,
                risk_metrics=metrics,
                recommendations=recommendations,
                html_report=html_report
            )
            
            self.status = AgentStatus.COMPLETED
            return report
        
        except Exception as e:
            self.status = AgentStatus.FAILED
            raise RuntimeError(f"ReportAgent generation failed: {str(e)}")
    
    def _build_prompt(self, portfolio: NormalizedPortfolio, metrics: RiskMetrics) -> str:
        """Build prompt for LLM (includes computed metrics, not asking for new ones)"""
        var_display = f"${metrics.var_parametric:,.2f}" if metrics.var_parametric is not None else "N/A"
        prompt = f"""
Provide a brief risk assessment summary for the following portfolio:

Portfolio: {portfolio.name}
Assets: {metrics.asset_count}
Total Value: ${metrics.total_value:,.2f}
Total P&L: ${metrics.total_pnl:,.2f}
VaR (95%): {var_display}

Focus on interpreting these metrics and providing context.
Do NOT calculate new numbers. Only interpret the provided metrics.
Keep response under 100 words.
"""
        return prompt
    
    def _generate_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """Generate deterministic recommendations based on metrics"""
        recommendations = []
        
        # P&L based
        if metrics.total_pnl > 0:
            recommendations.append("Portfolio showing positive P&L. Consider taking profits on winners.")
        elif metrics.total_pnl < 0:
            recommendations.append("Portfolio showing negative P&L. Review positions for rebalancing.")
        
        # VaR based
        if metrics.var_parametric and metrics.total_value > 0:
            var_pct = (metrics.var_parametric / metrics.total_value) * 100
            if var_pct > 2:
                recommendations.append(f"Daily VaR at {var_pct:.1f}% of portfolio. Consider hedging strategies.")
        
        # Greeks based
        if metrics.portfolio_greeks and abs(metrics.portfolio_greeks.get("delta", 0)) > 100:
            recommendations.append("High delta exposure detected. Consider delta hedging.")
        
        # Scenario based
        if metrics.scenario_results:
            for scenario in metrics.scenario_results:
                if scenario.get("change_pct", 0) < -15:
                    recommendations.append(f"Significant downside risk in {scenario.get('name')} scenario.")
        
        if not recommendations:
            recommendations.append("Portfolio metrics within normal parameters. Continue monitoring.")
        
        return recommendations
    
    def _generate_html(self, portfolio: NormalizedPortfolio, metrics: RiskMetrics, summary: str) -> str:
        """Generate deterministic HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Risk Report - {portfolio.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .metric strong {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .recommendations {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
        .recommendations li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Portfolio Risk Report: {portfolio.name}</h1>
        
        <h2>Executive Summary</h2>
        <p>{summary}</p>
        
        <h2>Key Metrics</h2>
        <div class="metric"><strong>Total Value:</strong> ${metrics.total_value:,.2f}</div>
        <div class="metric"><strong>Total P&L:</strong> <span class="{'positive' if metrics.total_pnl >= 0 else 'negative'}">${metrics.total_pnl:,.2f}</span></div>
        <div class="metric"><strong>Asset Count:</strong> {metrics.asset_count}</div>
        {f'<div class="metric"><strong>VaR (95% confidence):</strong> ${metrics.var_parametric:,.2f}</div>' if metrics.var_parametric else ''}
        
        {self._format_greeks_html(metrics.portfolio_greeks) if metrics.portfolio_greeks else ''}
        
        {self._format_scenarios_html(metrics.scenario_results) if metrics.scenario_results else ''}
        
        <h2>Positions</h2>
        <table>
            <tr>
                <th>Symbol</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
            {''.join(f'<tr><td>{p.symbol}</td><td>{p.type}</td><td>{p.quantity}</td><td>${(p.current_price or p.price or 0):.2f}</td></tr>' for p in portfolio.positions)}
        </table>
    </div>
</body>
</html>
"""
        return html
    
    def _format_greeks_html(self, greeks: Dict[str, float]) -> str:
        """Format Greeks for HTML"""
        return f"""
        <h2>Portfolio Greeks</h2>
        <div class="metric"><strong>Delta:</strong> {greeks['delta']:.4f}</div>
        <div class="metric"><strong>Gamma:</strong> {greeks['gamma']:.6f}</div>
        <div class="metric"><strong>Vega:</strong> {greeks['vega']:.4f}</div>
        <div class="metric"><strong>Theta:</strong> {greeks['theta']:.4f}</div>
        <div class="metric"><strong>Rho:</strong> {greeks['rho']:.4f}</div>
        """
    
    def _format_scenarios_html(self, scenarios: List[Dict[str, Any]]) -> str:
        """Format scenario results for HTML"""
        rows = ''
        for s in scenarios:
            css_class = 'positive' if s["change"] >= 0 else 'negative'
            rows += (
                f'<tr><td>{s["name"]}</td>'
                f'<td>${s["base_value"]:,.2f}</td>'
                f'<td>${s["scenario_value"]:,.2f}</td>'
                f'<td class="{css_class}">${s["change"]:,.2f} ({s["change_pct"]:.1f}%)</td></tr>'
            )
        
        return f"""
        <h2>Stress Test Scenarios</h2>
        <table>
            <tr>
                <th>Scenario</th>
                <th>Base Value</th>
                <th>Stressed Value</th>
                <th>Change</th>
            </tr>
            {rows}
        </table>
        """


# ===== Multi-Agent Coordinator =====


class MultiAgentCoordinator:
    """
    Coordinates the three agents with logging and handoffs.
    """
    
    def __init__(self, llm_provider=None):
        self.intake_agent = IntakeAgent()
        self.risk_agent = RiskAgent()
        self.report_agent = ReportAgent(llm_provider)
        self.handoffs: List[AgentHandoff] = []
    
    def execute(self, raw_portfolio: Dict[str, Any]) -> ReportOutput:
        """
        Execute full multi-agent workflow.
        
        Args:
            raw_portfolio: Raw portfolio input
        
        Returns:
            Final ReportOutput
        """
        # Stage 1: Intake
        normalized_portfolio = self.intake_agent.process(raw_portfolio)
        self._log_handoff("IntakeAgent", "RiskAgent", normalized_portfolio.model_dump())
        
        # Stage 2: Risk Calculation
        risk_metrics = self.risk_agent.process(normalized_portfolio)
        self._log_handoff("RiskAgent", "ReportAgent", risk_metrics.model_dump())
        
        # Stage 3: Report Generation
        report = self.report_agent.process(normalized_portfolio, risk_metrics)
        
        return report
    
    def _log_handoff(self, from_agent: str, to_agent: str, data: Dict[str, Any]):
        """Log agent handoff with hash"""
        data_json = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()
        
        handoff = AgentHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            data=data,
            hash=data_hash
        )
        self.handoffs.append(handoff)
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get audit trail of handoffs"""
        return [h.model_dump() for h in self.handoffs]
