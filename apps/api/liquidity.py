"""
RiskCanvas v4.34.0–v4.36.0 — Liquidity + Transaction Cost Models (Wave 21)

Provides:
- Liquidity tiers per symbol (fixture)
- Deterministic haircut model (tier-based)
- Transaction cost / slippage model based on notional + tier + vol proxy
- Cost vs Risk tradeoff metrics
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
LIQUIDITY_VERSION = "v1.0"
ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "liq_c3d4e5f6a7"


# ─────────────────── Liquidity Tier Fixtures ──────────────────────────────────
# Tier 1 = most liquid, Tier 4 = least liquid
# Columns: tier, daily_vol_usd_mm, haircut_pct, spread_bps, vol_proxy

_LIQ_TIERS: Dict[str, Dict[str, Any]] = {
    "AAPL":  {"tier": 1, "daily_vol_mm": 8500, "haircut_pct": 0.5,  "spread_bps": 1.2,  "vol_proxy": 0.0732},
    "MSFT":  {"tier": 1, "daily_vol_mm": 7200, "haircut_pct": 0.5,  "spread_bps": 1.1,  "vol_proxy": 0.0681},
    "GOOGL": {"tier": 1, "daily_vol_mm": 4800, "haircut_pct": 0.5,  "spread_bps": 1.3,  "vol_proxy": 0.0754},
    "AMZN":  {"tier": 1, "daily_vol_mm": 4200, "haircut_pct": 0.5,  "spread_bps": 1.4,  "vol_proxy": 0.0790},
    "TSLA":  {"tier": 2, "daily_vol_mm": 3100, "haircut_pct": 1.5,  "spread_bps": 2.1,  "vol_proxy": 0.1823},
    "NVDA":  {"tier": 1, "daily_vol_mm": 5600, "haircut_pct": 0.5,  "spread_bps": 1.2,  "vol_proxy": 0.0843},
    "META":  {"tier": 1, "daily_vol_mm": 4100, "haircut_pct": 0.75, "spread_bps": 1.5,  "vol_proxy": 0.0812},
    "SHELL": {"tier": 2, "daily_vol_mm": 1200, "haircut_pct": 1.5,  "spread_bps": 3.2,  "vol_proxy": 0.0921},
    "BP":    {"tier": 2, "daily_vol_mm": 900,  "haircut_pct": 1.5,  "spread_bps": 3.5,  "vol_proxy": 0.0985},
    "ASML":  {"tier": 2, "daily_vol_mm": 800,  "haircut_pct": 2.0,  "spread_bps": 4.2,  "vol_proxy": 0.1021},
    "SAP":   {"tier": 2, "daily_vol_mm": 600,  "haircut_pct": 2.0,  "spread_bps": 4.5,  "vol_proxy": 0.0934},
    "CORP_A":{"tier": 3, "daily_vol_mm": 150,  "haircut_pct": 5.0,  "spread_bps": 15.0, "vol_proxy": 0.0500},
    "CORP_B":{"tier": 3, "daily_vol_mm": 120,  "haircut_pct": 5.0,  "spread_bps": 18.0, "vol_proxy": 0.0550},
    "CORP_C":{"tier": 4, "daily_vol_mm": 40,   "haircut_pct": 10.0, "spread_bps": 35.0, "vol_proxy": 0.0800},
}

_DEFAULT_TIER = {"tier": 3, "daily_vol_mm": 100, "haircut_pct": 5.0, "spread_bps": 20.0, "vol_proxy": 0.0800}

_TIER_LABELS = {1: "Tier 1 — Ultra Liquid", 2: "Tier 2 — Liquid", 3: "Tier 3 — Semi-Liquid", 4: "Tier 4 — Illiquid"}


def _get_tier(symbol: str) -> Dict[str, Any]:
    return _LIQ_TIERS.get(symbol.upper(), dict(_DEFAULT_TIER))


# ─────────────────── Haircut Model ────────────────────────────────────────────


def compute_haircut(portfolio: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute liquidity haircut for each position.
    portfolio items: {symbol, notional}
    """
    rows = []
    total_before = 0.0
    total_after = 0.0

    for item in sorted(portfolio, key=lambda x: x.get("symbol", "")):
        symbol = item.get("symbol", "UNK")
        notional = float(item.get("notional", 0.0))
        t = _get_tier(symbol)
        hc = t["haircut_pct"] / 100.0
        haircut_value = round(notional * hc, 2)
        net_value = round(notional - haircut_value, 2)
        total_before += notional
        total_after += net_value
        rows.append({
            "symbol": symbol,
            "tier": t["tier"],
            "tier_label": _TIER_LABELS[t["tier"]],
            "notional": notional,
            "haircut_pct": t["haircut_pct"],
            "haircut_value": haircut_value,
            "net_value": net_value,
        })

    output = {
        "portfolio_rows": rows,
        "total_notional": round(total_before, 2),
        "total_net_after_haircut": round(total_after, 2),
        "total_haircut": round(total_before - total_after, 2),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    output["output_hash"] = _sha256(output)
    return output


# ─────────────────── Transaction Cost / Slippage Model ───────────────────────


def compute_tcost(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Estimate transaction cost (slippage) per trade.
    trade items: {symbol, notional, side (buy|sell)}
    slippage_bps = spread_bps/2 + vol_proxy * sqrt(notional/daily_vol) * 0.5 * 10000
    """
    import math
    rows = []
    total_cost = 0.0

    for trade in sorted(trades, key=lambda x: x.get("symbol", "")):
        symbol = trade.get("symbol", "UNK")
        notional = float(trade.get("notional", 0.0))
        side = trade.get("side", "buy").lower()
        t = _get_tier(symbol)
        daily_vol_usd = t["daily_vol_mm"] * 1e6
        spread_bps = t["spread_bps"]
        vol_proxy = t["vol_proxy"]

        # Market impact component
        participation = notional / daily_vol_usd if daily_vol_usd > 0 else 0.001
        impact_bps = vol_proxy * math.sqrt(max(participation, 1e-9)) * 10000 * 0.5
        total_bps = round(spread_bps / 2.0 + impact_bps, 4)
        cost_usd = round(notional * total_bps / 10000.0, 2)
        total_cost += cost_usd

        rows.append({
            "symbol": symbol,
            "notional": notional,
            "side": side,
            "tier": t["tier"],
            "spread_component_bps": round(spread_bps / 2.0, 4),
            "impact_component_bps": round(impact_bps, 4),
            "total_cost_bps": total_bps,
            "estimated_cost_usd": cost_usd,
        })

    output = {
        "trades": rows,
        "total_estimated_cost_usd": round(total_cost, 2),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    output["output_hash"] = _sha256(output)
    return output


# ─────────────────── Cost vs Risk Tradeoff ────────────────────────────────────


def compute_tradeoff(
    hedge_trades: List[Dict[str, Any]],
    risk_reduction_usd: float,
    constraint_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute risk vs cost tradeoff for a set of hedge trades.
    """
    tcost = compute_tcost(hedge_trades)
    total_cost = tcost["total_estimated_cost_usd"]
    ratio = round(risk_reduction_usd / max(total_cost, 0.01), 4)

    sides = []
    for row in tcost["trades"]:
        sides.append({
            "symbol": row["symbol"],
            "risk_reduction_contribution": round(risk_reduction_usd / len(hedge_trades), 2),
            "cost_usd": row["estimated_cost_usd"],
            "cost_bps": row["total_cost_bps"],
            "net_benefit_usd": round(
                risk_reduction_usd / len(hedge_trades) - row["estimated_cost_usd"], 2
            ),
        })

    output = {
        "tradeoff": sides,
        "total_risk_reduction_usd": round(risk_reduction_usd, 2),
        "total_cost_usd": round(total_cost, 2),
        "risk_reduction_to_cost_ratio": ratio,
        "recommendation": (
            "EXECUTE — risk reduction > 10x cost" if ratio > 10
            else "REVIEW — risk reduction > 3x cost" if ratio > 3
            else "CAUTION — cost is high relative to risk reduction"
        ),
        "constraint_notes": constraint_notes or "",
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    output["output_hash"] = _sha256(output)
    return output


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class HaircutRequest(BaseModel):
    portfolio: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL",   "notional": 500000},
            {"symbol": "TSLA",   "notional": 200000},
            {"symbol": "CORP_A", "notional": 300000},
            {"symbol": "CORP_C", "notional": 100000},
        ]
    )


class TCostRequest(BaseModel):
    trades: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL",   "notional": 500000, "side": "sell"},
            {"symbol": "TSLA",   "notional": 200000, "side": "buy"},
            {"symbol": "CORP_A", "notional": 300000, "side": "sell"},
        ]
    )


class TradeoffRequest(BaseModel):
    hedge_trades: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL", "notional": 500000, "side": "sell"},
            {"symbol": "TSLA", "notional": 200000, "side": "sell"},
        ]
    )
    risk_reduction_usd: float = 450000.0
    constraint_notes: Optional[str] = None


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

liquidity_router = APIRouter(prefix="/liquidity", tags=["liquidity"])


@liquidity_router.get("/tiers")
def api_liq_tiers():
    tiers = []
    for sym, t in sorted(_LIQ_TIERS.items()):
        tiers.append({
            "symbol": sym,
            "tier": t["tier"],
            "tier_label": _TIER_LABELS[t["tier"]],
            "daily_vol_mm": t["daily_vol_mm"],
            "haircut_pct": t["haircut_pct"],
            "spread_bps": t["spread_bps"],
        })
    return {
        "tiers": tiers,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


@liquidity_router.post("/haircut")
def api_haircut(req: HaircutRequest):
    return compute_haircut(req.portfolio)


tcost_router = APIRouter(prefix="/tcost", tags=["tcost"])


@tcost_router.post("/estimate")
def api_tcost(req: TCostRequest):
    return compute_tcost(req.trades)


@tcost_router.post("/tradeoff")
def api_tradeoff(req: TradeoffRequest):
    return compute_tradeoff(req.hedge_trades, req.risk_reduction_usd, req.constraint_notes)


liquidity_exports_router = APIRouter(prefix="/exports", tags=["liquidity-exports"])


class LiqPackRequest(BaseModel):
    portfolio: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL",   "notional": 500000},
            {"symbol": "TSLA",   "notional": 200000},
        ]
    )
    trades: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL",   "notional": 500000, "side": "sell"},
            {"symbol": "TSLA",   "notional": 200000, "side": "sell"},
        ]
    )
    risk_reduction_usd: float = 400000.0


@liquidity_exports_router.post("/liquidity-pack")
def api_liq_pack(req: LiqPackRequest):
    haircut = compute_haircut(req.portfolio)
    tcost = compute_tcost(req.trades)
    tradeoff = compute_tradeoff(req.trades, req.risk_reduction_usd)
    pack = {
        "pack_type": "liquidity-tcost-pack",
        "version": LIQUIDITY_VERSION,
        "haircut": haircut,
        "tcost": tcost,
        "tradeoff": tradeoff,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    pack["pack_hash"] = _sha256(pack)
    return pack
