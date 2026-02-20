"""
run_outcomes.py (v5.56.1 — Depth Wave)

RunOutcome model: deterministic quality + risk metrics linked to a run_id.

Metrics:
  pnl_total, var_95, var_99, max_drawdown_proxy, scenario_severity_score
  completeness_score, data_freshness_score (both DEMO-stable, no wall-clock)

Endpoints:
  GET  /runs/{run_id}/outcome
  GET  /runs/outcomes?limit=&workspace_id=

All metrics deterministic: same run_id → same outcome.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

router = APIRouter(tags=["run-outcomes"])

# ── In-memory store ────────────────────────────────────────────────────────────

OUTCOME_STORE: Dict[str, Dict[str, Any]] = {}


# ── Deterministic helpers ──────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _det(seed: str, lo: float, hi: float, decimals: int = 4) -> float:
    """Deterministic float in [lo, hi] derived from sha256 of seed."""
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    raw = lo + (hi - lo) * (h / 0xFFFFFFFF)
    return round(raw, decimals)


# ── Metric computation ─────────────────────────────────────────────────────────

def _compute_outcome(run_id: str, scenario_id: str, kind: str, output_hash: str) -> Dict[str, Any]:
    """
    Pure deterministic function: given run metadata, produce stable metrics.
    Rounding: all monetary values to 2dp, scores to 4dp.
    """
    base = f"{run_id}:{scenario_id}:{output_hash}"

    # Risk metrics
    pnl_total        = round(_det(base + ":pnl",  -3_000_000, 0,      2), 2)
    var_95           = round(abs(pnl_total) * _det(base + ":var95", 0.78, 0.88, 4), 2)
    var_99           = round(abs(pnl_total) * _det(base + ":var99", 1.10, 1.25, 4), 2)
    max_drawdown     = round(abs(pnl_total) * _det(base + ":dd",    1.28, 1.45, 4), 2)

    # Severity: 0–10 scale (deterministic)
    severity_raw     = _det(base + ":sev", 3.5, 9.5, 4)
    severity         = round(severity_raw, 2)

    # Quality fields (DEMO-stable, independent of wall clock)
    completeness     = round(_det(base + ":cmp", 0.87, 0.99, 4), 4)
    data_freshness   = round(_det(base + ":frsh", 0.91, 0.99, 4), 4)

    outcome_id = "out-" + _sha({"run_id": run_id, "version": "v1"})[:16]

    return {
        "outcome_id": outcome_id,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "kind": kind,
        "output_hash": output_hash,
        # Risk metrics
        "pnl_total": pnl_total,
        "var_95": var_95,
        "var_99": var_99,
        "max_drawdown_proxy": max_drawdown,
        "scenario_severity_score": severity,
        # Quality fields
        "completeness_score": completeness,
        "data_freshness_score": data_freshness,
        # Meta
        "computed_at": ASOF,
        "engine_version": "v5.56.1",
        "rounding_note": "monetary=2dp; scores=4dp; deterministic via sha256 seed",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_or_create_outcome(run_id: str, scenario_id: str, kind: str, output_hash: str) -> Dict[str, Any]:
    """Idempotent: returns existing outcome or computes + stores one."""
    if run_id in OUTCOME_STORE:
        return OUTCOME_STORE[run_id]
    outcome = _compute_outcome(run_id, scenario_id, kind, output_hash)
    OUTCOME_STORE[run_id] = outcome
    return outcome


def list_outcomes(limit: int = 50, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
    results = list(OUTCOME_STORE.values())
    if workspace_id:
        results = [o for o in results if o.get("workspace_id") == workspace_id]
    results.sort(key=lambda o: o["outcome_id"])
    return results[:limit]


# ── HTTP endpoints ────────────────────────────────────────────────────────────

class OutcomeResponse(BaseModel):
    outcome: Dict[str, Any]


class OutcomeListResponse(BaseModel):
    outcomes: List[Dict[str, Any]]
    total: int


@router.get("/runs/outcomes", response_model=OutcomeListResponse)
def list_run_outcomes(
    limit: int = Query(50, ge=1, le=500),
    workspace_id: Optional[str] = Query(None),
):
    outcomes = list_outcomes(limit, workspace_id)
    return {"outcomes": outcomes, "total": len(outcomes)}


@router.get("/runs/{run_id}/outcome", response_model=OutcomeResponse)
def get_run_outcome(run_id: str):
    # If outcome already stored, return it
    if run_id in OUTCOME_STORE:
        return {"outcome": OUTCOME_STORE[run_id]}

    # Try to synthesize from SCENARIO_RUNS
    from scenarios_v2 import SCENARIO_RUNS, SCENARIO_STORE
    for scenario_id, runs in SCENARIO_RUNS.items():
        for r in runs:
            if r.get("run_id") == run_id:
                scenario = SCENARIO_STORE.get(scenario_id, {})
                outcome = get_or_create_outcome(
                    run_id=run_id,
                    scenario_id=scenario_id,
                    kind=scenario.get("kind", "stress"),
                    output_hash=r.get("output_hash", run_id),
                )
                return {"outcome": outcome}

    # DEMO fallback: auto-compute outcome for any run_id (deterministic)
    outcome = get_or_create_outcome(
        run_id=run_id,
        scenario_id="demo-scenario",
        kind="stress",
        output_hash=run_id,
    )
    return {"outcome": outcome}
