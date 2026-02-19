"""
scenario_runner.py (v5.46.0 — Wave 59)

Scenario Runner v1 — executes composed scenarios deterministically.

Produces run records with:
  - inputs_hash: SHA-256 of (scenario_id, payload, kind)  
  - outputs_hash: SHA-256 of impact output
  - step-by-step timeline (deterministic timestamps)
  - status: pending | running | completed | failed

Endpoints:
  POST /scenario-runner/runs           — start a run
  GET  /scenario-runner/runs           — list all runs
  GET  /scenario-runner/runs/{run_id}  — get run status + results
  GET  /scenario-runner/runs/by-scenario/{scenario_id} — runs for scenario
  POST /scenario-runner/runs/{run_id}/replay — replay deterministically
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

# In-memory store
RUNNER_STORE: Dict[str, Dict[str, Any]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sha(data: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _timeline_step(step_name: str, step_index: int, detail: str = "") -> Dict[str, Any]:
    """Deterministic timeline step — timestamp based on ASOF + step index."""
    # Deterministic: timestamp = ASOF base, with step offset encoded in microseconds
    ts = ASOF.replace("Z", f".{step_index:06d}000Z")
    return {
        "step": step_index,
        "name": step_name,
        "detail": detail,
        "timestamp": ts,
    }


def _compute_impact(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic impact calculation (identical to scenarios_v2._compute_impact).
    Must produce identical results for same (kind, payload) — determinism proof.
    """
    seed_json = json.dumps({"kind": kind, "payload": payload}, sort_keys=True)
    seed_int = int(hashlib.md5(seed_json.encode()).hexdigest(), 16)

    def _det(base: float, offset: int) -> float:
        return round(base + ((seed_int % (offset * 1000)) / 1000), 4)

    if kind == "rate_shock":
        shock = payload.get("shock_bps", 100)
        return {
            "parallel_shift": shock,
            "pnl_estimate": _det(-145_000.0, 3) * (shock / 100),
            "duration_impact": _det(-2.83, 7),
        }
    elif kind == "credit_event":
        return {
            "pnl_estimate": _det(-320_000.0, 5),
            "spread_widening": _det(85.0, 11),
            "affected_positions": abs(seed_int % 12) + 1,
        }
    elif kind == "fx_move":
        return {
            "pnl_estimate": _det(-78_000.0, 4),
            "fx_sensitivity": _det(0.045, 13),
            "hedge_cost": _det(2_100.0, 17),
        }
    elif kind == "stress_test":
        return {
            "pnl_estimate": _det(-520_000.0, 8),
            "var_impact": _det(0.082, 19),
            "tail_loss": _det(-890_000.0, 23),
        }
    else:  # liquidity_crisis
        return {
            "pnl_estimate": _det(-230_000.0, 6),
            "liquidity_gap": _det(15_500_000.0, 13),
            "funding_cost": _det(42_000.0, 9),
        }


def _build_timeline(kind: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build deterministic step-by-step timeline for a scenario run."""
    return [
        _timeline_step("validate_inputs", 1, f"kind={kind}"),
        _timeline_step("load_market_data", 2, f"tenant=demo, asof={ASOF}"),
        _timeline_step("initialize_engine", 3, "RiskCanvas Engine v5.46"),
        _timeline_step("compute_impact", 4, f"payload_keys={sorted(payload.keys())}"),
        _timeline_step("hash_outputs", 5, "SHA-256 of normalized impact"),
        _timeline_step("persist_results", 6, "stored in RUNNER_STORE"),
        _timeline_step("complete", 7, "status=completed"),
    ]


# ── Core business logic ────────────────────────────────────────────────────────


def start_run(
    scenario_id: str,
    kind: str,
    payload: Dict[str, Any],
    tenant_id: str = "tenant-001",
    initiated_by: str = "runner@riskcanvas.io",
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Start (and immediately complete) a deterministic scenario run.

    - For same (scenario_id, kind, payload): inputs_hash is identical.
    - Impact is computed deterministically, so outputs_hash is also identical.
    """
    if run_id is None:
        run_id = f"srun-{uuid.uuid4().hex[:12]}"

    inputs = {"scenario_id": scenario_id, "kind": kind, "payload": payload}
    inputs_hash = _sha(inputs)

    impact = _compute_impact(kind, payload)
    outputs_hash = _sha(impact)

    timeline = _build_timeline(kind, payload)

    run = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "tenant_id": tenant_id,
        "kind": kind,
        "payload": payload,
        "status": "completed",
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "impact": impact,
        "timeline": timeline,
        "initiated_by": initiated_by,
        "started_at": ASOF,
        "completed_at": ASOF,
        "engine_version": "v5.46.0",
    }

    RUNNER_STORE[run_id] = run
    return run


def get_run(run_id: str) -> Dict[str, Any]:
    if run_id not in RUNNER_STORE:
        raise ValueError(f"Run not found: {run_id}")
    return RUNNER_STORE[run_id]


def list_runs(scenario_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    runs = list(RUNNER_STORE.values())
    if scenario_id:
        runs = [r for r in runs if r["scenario_id"] == scenario_id]
    return runs[:limit]


def replay_run(existing_run_id: str) -> Dict[str, Any]:
    """
    Replay a run using the original inputs. Produces identical outputs_hash.
    The new run gets a fresh run_id but same inputs_hash and outputs_hash.
    """
    existing = get_run(existing_run_id)
    new_run_id = f"srun-replay-{uuid.uuid4().hex[:8]}"
    return start_run(
        scenario_id=existing["scenario_id"],
        kind=existing["kind"],
        payload=existing["payload"],
        tenant_id=existing["tenant_id"],
        run_id=new_run_id,
    )


# ── Demo seed ──────────────────────────────────────────────────────────────────


def _seed_demo_runs() -> None:
    if RUNNER_STORE:
        return

    seeds = [
        ("scn-demo-001", "rate_shock", {"shock_bps": 100, "curve": "USD_SOFR"}),
        ("scn-demo-002", "credit_event", {"issuer": "DEMO_CORP", "rating_drop": 3}),
        ("scn-demo-003", "fx_move", {"pairs": [{"from": "USD", "to": "EUR", "move_pct": -5}]}),
    ]
    for scn_id, kind, payload in seeds:
        start_run(
            scenario_id=scn_id,
            kind=kind,
            payload=payload,
            run_id=f"srun-demo-{scn_id[-3:]}",
        )


_seed_demo_runs()


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/scenario-runner", tags=["scenario-runner"])


class StartRunRequest(BaseModel):
    scenario_id: str
    kind: str
    payload: Dict[str, Any]
    tenant_id: str = "tenant-001"
    initiated_by: str = "runner@riskcanvas.io"
    run_id: Optional[str] = None


@router.post("/runs")
def http_start_run(req: StartRunRequest):
    run = start_run(
        scenario_id=req.scenario_id,
        kind=req.kind,
        payload=req.payload,
        tenant_id=req.tenant_id,
        initiated_by=req.initiated_by,
        run_id=req.run_id,
    )
    return {"run": run}


@router.get("/runs")
def http_list_runs(scenario_id: Optional[str] = None, limit: int = 50):
    return {"runs": list_runs(scenario_id=scenario_id, limit=limit), "count": len(RUNNER_STORE)}


@router.get("/runs/{run_id}")
def http_get_run(run_id: str):
    try:
        return {"run": get_run(run_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/by-scenario/{scenario_id}")
def http_runs_for_scenario(scenario_id: str, limit: int = 50):
    runs = list_runs(scenario_id=scenario_id, limit=limit)
    return {"runs": runs, "count": len(runs)}


@router.post("/runs/{run_id}/replay")
def http_replay_run(run_id: str):
    try:
        replayed = replay_run(run_id)
        return {"run": replayed, "original_run_id": run_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
