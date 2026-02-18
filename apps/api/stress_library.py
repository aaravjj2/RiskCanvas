"""
Stress Library API Router (v3.5+)

Exposes:
  GET  /stress/presets           - list all canonical stress presets
  GET  /stress/presets/{id}      - get single preset
  POST /stress/apply             - apply preset to portfolio input
  POST /compare/runs             - compare two run result dicts by run_id or inline
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Engine path
_engine_path = str(Path(__file__).parent.parent.parent / "packages" / "engine")
if _engine_path not in sys.path:
    sys.path.insert(0, _engine_path)

from src.stress import list_presets, get_preset, apply_preset

stress_router = APIRouter(tags=["stress"])
compare_router = APIRouter(prefix="/compare", tags=["compare"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class StressApplyRequest(BaseModel):
    preset_id: str
    portfolio: Dict[str, Any]   # same shape as runs/execute portfolio


class StressApplyResponse(BaseModel):
    preset_id: str
    preset_label: str
    input_hash: str
    stressed_input_hash: str
    shocks_applied: Dict[str, Any]
    stressed_portfolio: Dict[str, Any]


# Compare schemas ─────────────────────────────────────────

class RunSnapshot(BaseModel):
    """Inline run KPI snapshot for comparison (no DB required)."""
    run_id: str
    portfolio_value: Optional[float] = None
    total_pnl: Optional[float] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    delta: Optional[float] = None     # portfolio delta if available
    duration: Optional[float] = None  # bond duration if available


class CompareRunsRequest(BaseModel):
    run_a: RunSnapshot
    run_b: RunSnapshot


def _safe_delta(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return round(b - a, 6)


class CompareRunsResponse(BaseModel):
    run_id_a: str
    run_id_b: str
    delta_var_95: Optional[float]
    delta_var_99: Optional[float]
    delta_pnl: Optional[float]
    delta_portfolio_value: Optional[float]
    delta_delta: Optional[float]
    delta_duration: Optional[float]
    delta_cache_hit: Optional[str]
    summary: str


# ── Stress endpoints ──────────────────────────────────────────────────────────

@stress_router.get("/stress/presets")
async def list_stress_presets():
    """List all deterministic stress scenario presets."""
    return {"presets": list_presets(), "count": len(list_presets())}


@stress_router.get("/stress/presets/{preset_id}")
async def get_stress_preset(preset_id: str):
    """Get a single stress preset by ID."""
    p = get_preset(preset_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id!r}")
    return p


@stress_router.post("/stress/apply", response_model=StressApplyResponse)
async def apply_stress_preset(request: StressApplyRequest):
    """Apply a stress preset to a portfolio dict."""
    try:
        result = apply_preset(request.preset_id, request.portfolio)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return StressApplyResponse(
        preset_id=result["stress_preset_id"],
        preset_label=result["preset_label"],
        input_hash=result["input_hash"],
        stressed_input_hash=result["stressed_input_hash"],
        shocks_applied=result["shocks_applied"],
        stressed_portfolio=result["stressed_portfolio"],
    )


# ── Compare endpoints ─────────────────────────────────────────────────────────

@compare_router.post("/runs", response_model=CompareRunsResponse)
async def compare_runs_delta(request: CompareRunsRequest):
    """
    Compare two run snapshots and return delta KPIs.
    Deltas computed deterministically: round(b - a, 6).
    """
    a = request.run_a
    b = request.run_b

    d_var95 = _safe_delta(a.var_95, b.var_95)
    d_var99 = _safe_delta(a.var_99, b.var_99)
    d_pnl = _safe_delta(a.total_pnl, b.total_pnl)
    d_value = _safe_delta(a.portfolio_value, b.portfolio_value)
    d_delta = _safe_delta(a.delta, b.delta)
    d_duration = _safe_delta(a.duration, b.duration)

    # Build text summary
    parts = []
    if d_pnl is not None:
        sign = "+" if d_pnl >= 0 else ""
        parts.append(f"PnL {sign}{d_pnl:.2f}")
    if d_var95 is not None:
        sign = "+" if d_var95 >= 0 else ""
        parts.append(f"VaR95 {sign}{d_var95:.2f}")
    summary = " | ".join(parts) if parts else "no comparable metrics"

    return CompareRunsResponse(
        run_id_a=a.run_id,
        run_id_b=b.run_id,
        delta_var_95=d_var95,
        delta_var_99=d_var99,
        delta_pnl=d_pnl,
        delta_portfolio_value=d_value,
        delta_delta=d_delta,
        delta_duration=d_duration,
        delta_cache_hit=None,
        summary=summary,
    )
