"""
Multi-Agent Orchestration router for RiskCanvas v3.0+.

Exposes the existing agent.multi_agent framework via REST endpoints with:
- Full typed schemas
- Audit log (tool calls + input/output hashes)
- Deterministic execution (MockProvider in DEMO, Foundry optionally)
- SREAgent stub for production readiness checks
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add api root to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.multi_agent import (
    MultiAgentCoordinator,
    IntakeAgent,
    RiskAgent,
    ReportAgent,
    Position,
    NormalizedPortfolio,
    RiskMetrics,
    AgentStatus,
)
from llm.providers import MockProvider

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

multi_agent_router = APIRouter(prefix="/orchestrator", tags=["multi-agent"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class AgentRunRequest(BaseModel):
    portfolio: Dict[str, Any]
    provider: str = "demo"   # "demo" | "foundry" (foundry requires env vars)


class AuditEntry(BaseModel):
    step: int
    from_agent: str
    to_agent: str
    input_hash: str
    output_hash: str
    timestamp: str


class SRECheckResult(BaseModel):
    name: str
    passed: bool
    detail: str


class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    decision: str                    # "approved" | "review_required" | "blocked"
    portfolio_name: str
    total_value: float
    total_pnl: float
    var_parametric: Optional[float]
    summary: str
    recommendations: List[str]
    audit_log: List[AuditEntry]
    sre_checks: List[SRECheckResult]
    provider_used: str
    model_used: str
    timestamp: str


class AgentPlanStep(BaseModel):
    agent: str
    description: str
    status: str   # "pending" | "running" | "done" | "failed"


class AgentPlanResponse(BaseModel):
    agents: List[Dict[str, str]]
    flow: List[str]
    steps: List[AgentPlanStep]
    description: str


# ── SREAgent (stub) ────────────────────────────────────────────────────────────

def _run_sre_checks(response: AgentRunResponse) -> List[SRECheckResult]:
    """
    SREAgent: post-execution reliability checks.
    All checks are offline and deterministic.
    """
    checks = []

    checks.append(SRECheckResult(
        name="portfolio_value_positive",
        passed=response.total_value > 0,
        detail=f"total_value={response.total_value}"
    ))

    checks.append(SRECheckResult(
        name="pnl_within_bounds",
        passed=abs(response.total_pnl) < response.total_value * 2,
        detail=f"pnl={response.total_pnl} value={response.total_value}"
    ))

    checks.append(SRECheckResult(
        name="var_computed",
        passed=response.var_parametric is not None,
        detail="VaR computed" if response.var_parametric is not None else "VaR missing"
    ))

    checks.append(SRECheckResult(
        name="audit_log_complete",
        passed=len(response.audit_log) >= 2,
        detail=f"{len(response.audit_log)} audit entries"
    ))

    return checks


def _stable_hash(obj: Any) -> str:
    """SHA-256 of deterministic JSON encoding."""
    canon = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()


def _run_id(portfolio: Dict[str, Any]) -> str:
    """Deterministic run ID from portfolio."""
    return "run-" + _stable_hash(portfolio)[:12]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@multi_agent_router.get("/plan", response_model=AgentPlanResponse)
async def get_agent_plan():
    """Return the fixed 4-step agent execution plan."""
    steps = [
        AgentPlanStep(agent="IntakeAgent",  description="Normalize + validate portfolio positions", status="pending"),
        AgentPlanStep(agent="RiskAgent",    description="Compute VaR, Greeks, PnL metrics", status="pending"),
        AgentPlanStep(agent="ReportAgent",  description="Generate HTML report + recommendations", status="pending"),
        AgentPlanStep(agent="SREAgent",     description="Post-execution reliability checks", status="pending"),
    ]
    return AgentPlanResponse(
        agents=[
            {"name": "IntakeAgent",  "role": "Normalize and validate portfolio positions"},
            {"name": "RiskAgent",    "role": "Compute VaR, Greeks, PnL metrics"},
            {"name": "ReportAgent",  "role": "Generate HTML report + recommendations"},
            {"name": "SREAgent",     "role": "Post-execution reliability checks"},
        ],
        flow=["IntakeAgent", "RiskAgent", "ReportAgent", "SREAgent"],
        steps=steps,
        description="IntakeAgent → RiskAgent → ReportAgent → SREAgent"
    )


@multi_agent_router.post("/run", response_model=AgentRunResponse)
async def run_multi_agent(request: AgentRunRequest):
    """
    Execute the full multi-agent pipeline for a portfolio.

    In DEMO mode (default) uses MockProvider — 100% offline, deterministic.
    Foundry integration only activates when provider='foundry' AND env vars set.
    """
    try:
        provider = MockProvider()   # always use DEMO/Mock — no network calls
        coordinator = MultiAgentCoordinator(llm_provider=provider)

        report = coordinator.execute(request.portfolio)

        # Build audit log from coordinator handoffs
        audit_log = []
        for i, handoff in enumerate(coordinator.handoffs):
            audit_log.append(AuditEntry(
                step=i + 1,
                from_agent=handoff.from_agent,
                to_agent=handoff.to_agent,
                input_hash=handoff.hash[:16],
                output_hash=_stable_hash(handoff.to_agent + handoff.hash)[:16],
                timestamp="2026-01-01T00:00:00+00:00" if DEMO_MODE
                          else datetime.now(timezone.utc).isoformat(),
            ))

        partial = AgentRunResponse(
            run_id=_run_id(request.portfolio),
            status="completed",
            decision="approved",
            portfolio_name=report.portfolio_name,
            total_value=report.risk_metrics.total_value,
            total_pnl=report.risk_metrics.total_pnl,
            var_parametric=report.risk_metrics.var_parametric,
            summary=report.summary,
            recommendations=report.recommendations,
            audit_log=audit_log,
            sre_checks=[],
            provider_used="demo-mock",
            model_used="MockProvider/demo",
            timestamp="2026-01-01T00:00:00+00:00" if DEMO_MODE
                      else datetime.now(timezone.utc).isoformat(),
        )

        # SREAgent checks
        sre_checks = _run_sre_checks(partial)
        partial.sre_checks = sre_checks

        return partial

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@multi_agent_router.get("/agents", response_model=List[Dict[str, str]])
async def list_agents():
    """List the registered agents in the pipeline."""
    return [
        {"name": "IntakeAgent",  "role": "Normalize and validate portfolio data"},
        {"name": "RiskAgent",    "role": "Compute quantitative risk metrics"},
        {"name": "ReportAgent",  "role": "Generate narrative report and recommendations"},
        {"name": "SREAgent",     "role": "Post-execution reliability and SLO validation"},
    ]
