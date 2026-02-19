"""
scenarios_v2.py (v5.26.0-v5.29.0 — Wave 50)

Scenario model: first-class objects for stress/whatif/shock_ladder scenarios.

Scenario:
  scenario_id (sha256 of canonical payload), tenant_id, name, kind,
  payload, payload_hash, created_by, created_at, tags, run_count

Run linkage:
  POST /scenarios/{id}/run  → runs scenario, stores artifact + attestation
  GET  /scenarios/{id}/runs → list run records for scenario

All IDs deterministic — same payload → same scenario_id.
No external network calls.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# ── In-memory DEMO storage ────────────────────────────────────────────────────

SCENARIO_STORE: Dict[str, Dict[str, Any]] = {}
SCENARIO_RUNS: Dict[str, List[Dict[str, Any]]] = {}   # scenario_id → [run, ...]

# ── Deterministic helpers ─────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ── Scenario kinds ────────────────────────────────────────────────────────────

VALID_KINDS = ["stress", "whatif", "shock_ladder"]

DEMO_SCENARIO_TEMPLATES: Dict[str, Any] = {
    "stress": {
        "shocks": {"rates": 0.01, "equity": -0.15, "credit": 0.0075},
        "confidence_level": 0.99,
        "horizon_days": 10,
    },
    "whatif": {
        "variables": [
            {"name": "fed_rate", "from": 0.053, "to": 0.043, "step": 0.0025}
        ],
        "base_portfolio": "default",
    },
    "shock_ladder": {
        "factor": "equity",
        "steps": [-0.30, -0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20],
        "base_portfolio": "default",
    },
}


# ── Scenario engine (deterministic, DEMO) ────────────────────────────────────

def _compute_impact(kind: str, payload: Any) -> Dict[str, Any]:
    """
    Compute impact summary from scenario payload.
    Pure function — deterministic: same payload → same result.
    """
    if kind == "stress":
        rates_shock = payload.get("shocks", {}).get("rates", 0.0)
        equity_shock = payload.get("shocks", {}).get("equity", 0.0)
        credit_shock = payload.get("shocks", {}).get("credit", 0.0)
        # Deterministic formula
        portfolio_pnl = round(
            -1_250_000 * rates_shock * 100
            + 3_200_000 * equity_shock
            + -800_000 * credit_shock * 100,
            2,
        )
        return {
            "kind": "stress",
            "portfolio_pnl": portfolio_pnl,
            "var_95": round(abs(portfolio_pnl) * 0.82, 2),
            "var_99": round(abs(portfolio_pnl) * 1.15, 2),
            "max_drawdown": round(abs(portfolio_pnl) * 1.32, 2),
            "affected_positions": 7,
        }
    elif kind == "whatif":
        return {
            "kind": "whatif",
            "portfolio_pnl": -142_350.00,
            "sensitivity": -28_470.0,
            "break_even_rate": 0.0488,
            "affected_positions": 3,
        }
    elif kind == "shock_ladder":
        steps = payload.get("steps", [])
        ladder = [{"shock": s, "pnl": round(3_200_000 * s, 2)} for s in steps]
        return {
            "kind": "shock_ladder",
            "factor": payload.get("factor", "equity"),
            "ladder": ladder,
            "max_loss": min(e["pnl"] for e in ladder) if ladder else 0,
            "max_gain": max(e["pnl"] for e in ladder) if ladder else 0,
        }
    return {"kind": kind, "note": "no_engine_for_kind"}


def create_scenario(
    tenant_id: str,
    name: str,
    kind: str,
    payload: Any,
    created_by: str = "demo@riskcanvas.io",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    canonical = _canonical(payload)
    payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
    scenario_id_src = {"tenant_id": tenant_id, "kind": kind, "payload_hash": payload_hash, "name": name}
    scenario_id = _sha(scenario_id_src)[:32]

    impact = _compute_impact(kind, payload)

    scenario: Dict[str, Any] = {
        "scenario_id": scenario_id,
        "tenant_id": tenant_id,
        "name": name,
        "kind": kind,
        "payload": payload,
        "payload_hash": payload_hash,
        "created_by": created_by,
        "created_at": ASOF,
        "tags": tags or [],
        "run_count": 0,
        "impact_preview": impact,
        "replayable": True,
    }

    SCENARIO_STORE[scenario_id] = scenario
    SCENARIO_RUNS[scenario_id] = []
    return scenario


def get_scenario(scenario_id: str) -> Dict[str, Any]:
    s = SCENARIO_STORE.get(scenario_id)
    if not s:
        raise ValueError(f"Scenario not found: {scenario_id}")
    return s


def list_scenarios(
    tenant_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    results = list(SCENARIO_STORE.values())
    if tenant_id:
        results = [s for s in results if s["tenant_id"] == tenant_id]
    if kind:
        results = [s for s in results if s["kind"] == kind]
    results.sort(key=lambda s: s["scenario_id"])
    return results[:limit]


def run_scenario(
    scenario_id: str,
    triggered_by: str = "demo@riskcanvas.io",
) -> Dict[str, Any]:
    """Execute scenario and record run with attestation."""
    scenario = get_scenario(scenario_id)

    # Deterministic run
    run_payload = {
        "scenario_id": scenario_id,
        "kind": scenario["kind"],
        "payload_hash": scenario["payload_hash"],
        "triggered_by": triggered_by,
        "run_index": len(SCENARIO_RUNS.get(scenario_id, [])),
    }
    run_id = _sha(run_payload)[:32]
    output = _compute_impact(scenario["kind"], scenario["payload"])
    output_hash = _sha(output)

    # Register artifact
    from artifacts_registry import register_artifact_direct
    artifact = register_artifact_direct(
        tenant_id=scenario["tenant_id"],
        artifact_type="scenario-run-output",
        created_by=triggered_by,
        source_job_id=run_id,
        content=output,
        manifest={"scenario_id": scenario_id, "kind": scenario["kind"]},
    )

    # Issue attestation
    from attestations import issue_attestation
    attestation = issue_attestation(
        tenant_id=scenario["tenant_id"],
        subject=f"scenario/{scenario_id}/run/{run_id}",
        statement_type="scenario.run",
        issued_by=triggered_by,
        input_hash=scenario["payload_hash"],
        output_hash=output_hash,
    )

    run_record: Dict[str, Any] = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "tenant_id": scenario["tenant_id"],
        "kind": scenario["kind"],
        "payload_hash": scenario["payload_hash"],
        "output": output,
        "output_hash": output_hash,
        "artifact_id": artifact["artifact_id"],
        "attestation_id": attestation["attestation_id"],
        "triggered_by": triggered_by,
        "executed_at": ASOF,
        "replayable": True,
    }

    SCENARIO_RUNS.setdefault(scenario_id, []).append(run_record)
    scenario["run_count"] = len(SCENARIO_RUNS[scenario_id])
    return run_record


def replay_scenario(scenario_id: str, triggered_by: str = "demo@riskcanvas.io") -> Dict[str, Any]:
    """Replay: re-run with same payload → identical output_hash (deterministic)."""
    return run_scenario(scenario_id, triggered_by=triggered_by)


def get_scenario_runs(scenario_id: str) -> List[Dict[str, Any]]:
    get_scenario(scenario_id)  # validates existence
    return SCENARIO_RUNS.get(scenario_id, [])


# ── Seed DEMO scenarios ───────────────────────────────────────────────────────

def _seed() -> None:
    from tenancy_v2 import DEFAULT_TENANT_ID

    for kind, tmpl in DEMO_SCENARIO_TEMPLATES.items():
        name = f"Demo {kind.replace('_',' ').title()} Scenario"
        create_scenario(DEFAULT_TENANT_ID, name, kind, tmpl, "seed@riskcanvas.io", [kind, "demo"])

    # Run the stress scenario twice (to show replay)
    stress_id = next(
        (s["scenario_id"] for s in SCENARIO_STORE.values() if s["kind"] == "stress"),
        None,
    )
    if stress_id:
        run_scenario(stress_id, "seed@riskcanvas.io")
        run_scenario(stress_id, "seed@riskcanvas.io")


_seed()


# ── FastAPI router ────────────────────────────────────────────────────────────

router = APIRouter(prefix="/scenarios-v2", tags=["scenarios-v2"])


class CreateScenarioRequest(BaseModel):
    name: str
    kind: str
    payload: Any
    tenant_id: Optional[str] = None
    created_by: str = "demo@riskcanvas.io"
    tags: Optional[List[str]] = None


class RunScenarioRequest(BaseModel):
    triggered_by: str = "demo@riskcanvas.io"


@router.get("")
async def api_list_scenarios(
    tenant_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 50,
    x_demo_tenant: Optional[str] = Header(None),
):
    tid = tenant_id or x_demo_tenant
    items = list_scenarios(tenant_id=tid, kind=kind, limit=limit)
    return {"scenarios": items, "count": len(items)}


@router.post("")
async def api_create_scenario(
    req: CreateScenarioRequest,
    x_demo_tenant: Optional[str] = Header(None),
):
    if req.kind not in VALID_KINDS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown kind '{req.kind}'. Valid: {VALID_KINDS}",
        )
    tid = req.tenant_id or x_demo_tenant or "default"
    scenario = create_scenario(
        tenant_id=tid,
        name=req.name,
        kind=req.kind,
        payload=req.payload,
        created_by=req.created_by,
        tags=req.tags,
    )
    return {"scenario": scenario}


@router.get("/{scenario_id}")
async def api_get_scenario(scenario_id: str):
    try:
        return {"scenario": get_scenario(scenario_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{scenario_id}/run")
async def api_run_scenario(scenario_id: str, req: RunScenarioRequest):
    try:
        run = run_scenario(scenario_id, req.triggered_by)
        return {"run": run}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{scenario_id}/replay")
async def api_replay_scenario(scenario_id: str, req: RunScenarioRequest):
    try:
        run = replay_scenario(scenario_id, req.triggered_by)
        return {"run": run, "replay": True, "deterministic": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{scenario_id}/runs")
async def api_get_scenario_runs(scenario_id: str):
    try:
        runs = get_scenario_runs(scenario_id)
        return {"runs": runs, "count": len(runs)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/templates/all")
async def api_get_templates():
    return {
        "templates": [
            {"kind": k, "payload": v, "description": f"{k} scenario template"}
            for k, v in DEMO_SCENARIO_TEMPLATES.items()
        ]
    }
