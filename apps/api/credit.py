"""
RiskCanvas v4.30.0–v4.32.0 — Credit + Spread Risk "Lite" (Wave 20)

Provides:
- Spread curve fixtures (usd_ig, usd_hy, eur_ig, em_hy)
- Deterministic linear interpolation
- Spread DV01 approximate calculator
- Spread shock scenario impact (lite model)
- Credit risk pack export
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
CREDIT_VERSION = "v1.0"

ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "credit_f1e2d3c4b5"


# ─────────────────── Spread Curve Fixtures ────────────────────────────────────

# Nodes: tenor_years → spread_bps
_SPREAD_CURVES: Dict[str, Dict[str, Any]] = {
    "usd_ig": {
        "name": "USD Investment Grade",
        "currency": "USD",
        "rating": "IG",
        "nodes": {1: 32.5, 2: 45.2, 3: 58.7, 5: 78.3, 7: 92.1, 10: 108.4, 15: 118.6, 20: 124.1, 30: 131.8},
    },
    "usd_hy": {
        "name": "USD High Yield",
        "currency": "USD",
        "rating": "HY",
        "nodes": {1: 185.0, 2: 240.5, 3: 292.8, 5: 358.1, 7: 398.4, 10: 431.6, 15: 461.2, 20: 478.5, 30: 492.0},
    },
    "eur_ig": {
        "name": "EUR Investment Grade",
        "currency": "EUR",
        "rating": "IG",
        "nodes": {1: 28.1, 2: 39.6, 3: 52.3, 5: 69.8, 7: 83.5, 10: 97.9, 15: 107.1, 20: 112.4, 30: 119.6},
    },
    "em_hy": {
        "name": "Emerging Markets High Yield",
        "currency": "USD",
        "rating": "EM-HY",
        "nodes": {1: 245.0, 2: 315.0, 3: 375.5, 5: 442.0, 7: 492.5, 10: 528.5, 15: 558.0, 20: 576.0, 30: 590.0},
    },
}


def _interpolate_spread(nodes: Dict[int, float], tenor: float) -> float:
    """Linear interpolation of spread curve at tenor (years)."""
    tenors = sorted(nodes.keys())
    if tenor <= tenors[0]:
        return nodes[tenors[0]]
    if tenor >= tenors[-1]:
        return nodes[tenors[-1]]
    for i in range(len(tenors) - 1):
        t0, t1 = tenors[i], tenors[i + 1]
        if t0 <= tenor <= t1:
            s0, s1 = nodes[t0], nodes[t1]
            w = (tenor - t0) / (t1 - t0)
            return round(s0 + w * (s1 - s0), 4)
    return nodes[tenors[-1]]


def get_curve(curve_id: str) -> Dict[str, Any]:
    c_id = curve_id.lower()
    if c_id not in _SPREAD_CURVES:
        raise ValueError(f"Unknown curve_id: {curve_id}. Available: {list(_SPREAD_CURVES.keys())}")
    c = _SPREAD_CURVES[c_id]
    nodes_list = [{"tenor_years": t, "spread_bps": s} for t, s in sorted(c["nodes"].items())]
    result = {
        "curve_id": c_id,
        "name": c["name"],
        "currency": c["currency"],
        "rating": c["rating"],
        "nodes": nodes_list,
        "asof": ASOF,
        "hash": _sha256({"curve_id": c_id, "nodes": c["nodes"]}),
        "audit_chain_head_hash": _chain_head(),
    }
    return result


def list_curves() -> Dict[str, Any]:
    curves = []
    for c_id, c in sorted(_SPREAD_CURVES.items()):
        node_tenors = sorted(c["nodes"].keys())
        curves.append({
            "curve_id": c_id,
            "name": c["name"],
            "currency": c["currency"],
            "rating": c["rating"],
            "min_tenor": node_tenors[0],
            "max_tenor": node_tenors[-1],
        })
    return {
        "curves": curves,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


# ─────────────────── Spread DV01 + Risk ───────────────────────────────────────


def compute_spread_dv01(notional: float, duration_years: float, spread_bps: float) -> float:
    """
    Approximate Spread DV01 (dollar value of 1 bp move in spread).
    DV01 ≈ notional × duration × 0.0001
    """
    return round(notional * duration_years * 0.0001, 6)


def compute_credit_risk(
    positions: List[Dict[str, Any]],
    curve_id: str,
) -> Dict[str, Any]:
    """
    Compute credit risk for a set of positions.
    Each position: {symbol, notional, tenor_years}
    Returns: spread_dv01 per position + total, shock scenario impacts.
    """
    c_id = curve_id.lower()
    if c_id not in _SPREAD_CURVES:
        raise ValueError(f"Unknown curve_id: {curve_id}")

    curve_nodes = _SPREAD_CURVES[c_id]["nodes"]
    rows = []
    total_dv01 = 0.0

    for pos in sorted(positions, key=lambda x: x.get("symbol", "")):
        notional = float(pos.get("notional", 0.0))
        tenor = float(pos.get("tenor_years", 5.0))
        spread = _interpolate_spread(curve_nodes, tenor)
        dv01 = compute_spread_dv01(notional, tenor, spread)
        total_dv01 += dv01

        # 25bps shock impact
        shock_25bps = round(dv01 * 25, 2)
        # 100bps shock impact
        shock_100bps = round(dv01 * 100, 2)

        rows.append({
            "symbol": pos.get("symbol", "UNK"),
            "notional": notional,
            "tenor_years": tenor,
            "spread_bps": spread,
            "spread_dv01": dv01,
            "shock_25bps_usd": shock_25bps,
            "shock_100bps_usd": shock_100bps,
        })

    total_dv01 = round(total_dv01, 6)
    output = {
        "curve_id": c_id,
        "positions": rows,
        "total_spread_dv01": total_dv01,
        "total_shock_25bps_usd": round(total_dv01 * 25, 2),
        "total_shock_100bps_usd": round(total_dv01 * 100, 2),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    output["output_hash"] = _sha256(output)
    return output


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class CreditRiskRequest(BaseModel):
    positions: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "CORP_A", "notional": 1000000, "tenor_years": 5},
            {"symbol": "CORP_B", "notional": 500000,  "tenor_years": 3},
            {"symbol": "CORP_C", "notional": 750000,  "tenor_years": 7},
        ]
    )
    curve_id: str = "usd_ig"


class CreditPackRequest(BaseModel):
    positions: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "CORP_A", "notional": 1000000, "tenor_years": 5},
            {"symbol": "CORP_B", "notional": 500000,  "tenor_years": 3},
        ]
    )
    curve_id: str = "usd_ig"


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

credit_router = APIRouter(prefix="/credit", tags=["credit"])


@credit_router.get("/curves")
def api_list_curves():
    return list_curves()


@credit_router.get("/curves/{curve_id}")
def api_get_curve(curve_id: str):
    try:
        return get_curve(curve_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@credit_router.post("/risk")
def api_credit_risk(req: CreditRiskRequest):
    try:
        return compute_credit_risk(req.positions, req.curve_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


credit_exports_router = APIRouter(prefix="/exports", tags=["credit-exports"])


@credit_exports_router.post("/credit-risk-pack")
def api_credit_pack(req: CreditPackRequest):
    try:
        risk = compute_credit_risk(req.positions, req.curve_id)
        curve = get_curve(req.curve_id)
        pack = {
            "pack_type": "credit-risk-pack",
            "version": CREDIT_VERSION,
            "curve": curve,
            "risk": risk,
            "asof": ASOF,
            "audit_chain_head_hash": _chain_head(),
        }
        pack["pack_hash"] = _sha256(pack)
        return pack
    except ValueError as e:
        raise HTTPException(400, str(e))
