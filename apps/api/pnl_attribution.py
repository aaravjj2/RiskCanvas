"""
RiskCanvas v4.10.0 — PnL Attribution Engine (Deterministic)

Provides factor-bucketed PnL attribution with stable ordering and rounding.
Factor buckets: spot, vol, rates, spread (if available), residual

All outputs are deterministic: same inputs → identical outputs + hashes.
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

# ─────────────────────────── Helpers ─────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _input_hash(**kwargs: Any) -> str:
    return _sha256(kwargs)


def _chain_head() -> str:
    return "pnlattrb3c4d5e6f7"


NUMERIC_PRECISION = 6


def _round(v: float) -> float:
    return round(v, NUMERIC_PRECISION)


# ─────────────────────────── Demo presets ────────────────────────────────────

DEMO_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "preset_tech_v1",
        "name": "Tech Portfolio Q1",
        "base_run_id": "run_base_001",
        "compare_run_id": "run_cmp_001",
        "description": "AAPL/MSFT/GOOGL spot move attribution",
    },
    {
        "id": "preset_rates_v1",
        "name": "Rates Sensitivity",
        "base_run_id": "run_base_002",
        "compare_run_id": "run_cmp_002",
        "description": "Options portfolio vol-move attribution",
    },
]

# ─────────────────────────── Attribution Engine ───────────────────────────────


def compute_pnl_attribution(
    base_run_id: str,
    compare_run_id: str,
    *,
    portfolio_id: str = "demo_portfolio",
) -> Dict[str, Any]:
    """
    Deterministic PnL attribution.
    Uses run_ids as seeds for reproducible demo values.
    Returns factor contributions table + hashes.
    """
    # Deterministic seeded values from run_ids
    seed_b = int(_sha256({"run": base_run_id})[:8], 16)
    seed_c = int(_sha256({"run": compare_run_id})[:8], 16)
    delta_seed = (seed_c - seed_b) % 100000

    # Factor contributions (deterministic, sum to total_pnl)
    spot_contrib = _round((delta_seed % 10000) / 100.0)
    vol_contrib = _round(-((delta_seed // 100) % 1000) / 100.0)
    rates_contrib = _round(((delta_seed // 10) % 500) / 100.0)
    spread_contrib = _round(-((delta_seed // 5) % 200) / 100.0)
    residual = _round(spot_contrib * 0.03)
    total_pnl = _round(spot_contrib + vol_contrib + rates_contrib + spread_contrib + residual)

    contributions = [
        {
            "factor": "spot",
            "bucket": "market_move",
            "contribution": spot_contrib,
            "pct_of_total": _round(spot_contrib / total_pnl * 100) if total_pnl != 0 else 0.0,
        },
        {
            "factor": "vol",
            "bucket": "vol_move",
            "contribution": vol_contrib,
            "pct_of_total": _round(vol_contrib / total_pnl * 100) if total_pnl != 0 else 0.0,
        },
        {
            "factor": "rates",
            "bucket": "rates_move",
            "contribution": rates_contrib,
            "pct_of_total": _round(rates_contrib / total_pnl * 100) if total_pnl != 0 else 0.0,
        },
        {
            "factor": "spread",
            "bucket": "spread_move",
            "contribution": spread_contrib,
            "pct_of_total": _round(spread_contrib / total_pnl * 100) if total_pnl != 0 else 0.0,
        },
        {
            "factor": "residual",
            "bucket": "unexplained",
            "contribution": residual,
            "pct_of_total": _round(residual / total_pnl * 100) if total_pnl != 0 else 0.0,
        },
    ]

    # Top drivers (deterministic sort by abs contribution desc)
    top_drivers = sorted(
        [c for c in contributions if c["factor"] != "residual"],
        key=lambda x: abs(x["contribution"]),
        reverse=True,
    )[:3]

    request = {
        "base_run_id": base_run_id,
        "compare_run_id": compare_run_id,
        "portfolio_id": portfolio_id,
    }
    ih = _input_hash(**request)
    result = {
        "base_run_id": base_run_id,
        "compare_run_id": compare_run_id,
        "portfolio_id": portfolio_id,
        "total_pnl": total_pnl,
        "contributions": contributions,
        "top_drivers": top_drivers,
    }
    oh = _sha256(result)

    return {
        **result,
        "input_hash": ih,
        "output_hash": oh,
        "audit_chain_head_hash": _chain_head(),
    }


def build_attribution_pack_manifest(attribution_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build deterministic export manifest for attribution pack."""
    manifest = {
        "pack_type": "pnl_attribution",
        "base_run_id": attribution_result["base_run_id"],
        "compare_run_id": attribution_result["compare_run_id"],
        "total_pnl": attribution_result["total_pnl"],
        "factor_count": len(attribution_result["contributions"]),
        "output_hash": attribution_result["output_hash"],
        "audit_chain_head_hash": attribution_result["audit_chain_head_hash"],
    }
    manifest["manifest_hash"] = _sha256(manifest)
    return manifest


# ─────────────────────────── Pydantic Models ─────────────────────────────────


class PnLAttributionRequest(BaseModel):
    base_run_id: str = Field(..., description="Base run ID")
    compare_run_id: str = Field(..., description="Comparison run ID")
    portfolio_id: str = Field("demo_portfolio", description="Portfolio ID")


class PnLAttributionExportRequest(BaseModel):
    base_run_id: str
    compare_run_id: str
    portfolio_id: str = "demo_portfolio"
    format: str = Field("json", description="Export format: json or md")


# ─────────────────────────── Router ──────────────────────────────────────────

pnl_router = APIRouter(prefix="/pnl", tags=["pnl-attribution"])


@pnl_router.post("/attribution")
async def get_pnl_attribution(req: PnLAttributionRequest) -> Dict[str, Any]:
    """
    Compute deterministic PnL attribution between two runs.
    Returns factor contributions table.
    """
    result = compute_pnl_attribution(
        req.base_run_id, req.compare_run_id, portfolio_id=req.portfolio_id
    )
    return result


@pnl_router.get("/drivers/presets")
async def get_pnl_driver_presets() -> Dict[str, Any]:
    """Return DEMO presets for PnL driver analysis."""
    ih = _input_hash(presets="demo")
    oh = _sha256(DEMO_PRESETS)
    return {
        "presets": DEMO_PRESETS,
        "count": len(DEMO_PRESETS),
        "input_hash": ih,
        "output_hash": oh,
        "audit_chain_head_hash": _chain_head(),
    }


# ─────────────────────────── Export Router ───────────────────────────────────

pnl_exports_router = APIRouter(prefix="/exports", tags=["pnl-exports"])


@pnl_exports_router.post("/pnl-attribution-pack")
async def export_pnl_attribution_pack(req: PnLAttributionExportRequest) -> Dict[str, Any]:
    """
    Export PnL attribution as a deterministic pack (JSON or MD).
    Stable ordering guaranteed.
    """
    result = compute_pnl_attribution(
        req.base_run_id,
        req.compare_run_id,
        portfolio_id=req.portfolio_id,
    )
    manifest = build_attribution_pack_manifest(result)

    pack: Dict[str, Any] = {
        "attribution": result,
        "manifest": manifest,
        "format": req.format,
    }

    if req.format == "md":
        lines = [
            f"# PnL Attribution Report",
            f"",
            f"**Base Run:** {result['base_run_id']}",
            f"**Compare Run:** {result['compare_run_id']}",
            f"**Total PnL:** {result['total_pnl']}",
            f"",
            f"## Factor Contributions",
            f"",
            f"| Factor | Contribution | % of Total |",
            f"|--------|-------------|------------|",
        ]
        for c in sorted(result["contributions"], key=lambda x: x["factor"]):
            lines.append(f"| {c['factor']} | {c['contribution']} | {c['pct_of_total']}% |")
        lines.extend([
            f"",
            f"## Audit",
            f"- Output Hash: `{result['output_hash']}`",
            f"- Manifest Hash: `{manifest['manifest_hash']}`",
            f"- Audit Chain Head: `{result['audit_chain_head_hash']}`",
        ])
        pack["content"] = "\n".join(lines)

    pack["pack_hash"] = _sha256(pack.get("content", pack["manifest"]))
    return pack
