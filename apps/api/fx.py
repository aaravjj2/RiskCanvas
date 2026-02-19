"""
RiskCanvas v4.26.0–v4.28.0 — FX + Cross-Currency Risk (Wave 19)

Provides:
- FX spot, forward, vol fixtures (deterministic)
- FX exposure calculator for portfolios
- FX PnL conversion helpers
- FX shock support for Scenario DSL
- All outputs are deterministic: same inputs → identical outputs + hashes.
- No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
FX_VERSION = "v1.0"

# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "fx_risk_a1b2c3d4e5"


# ─────────────────── FX Spot Fixtures ────────────────────────────────────────

_FX_SPOT: Dict[str, float] = {
    "EURUSD": 1.0875,
    "USDJPY": 148.52,
    "GBPUSD": 1.2634,
    "USDCAD": 1.3481,
    "AUDUSD": 0.6523,
    "USDCHF": 0.8872,
    "NZDUSD": 0.5982,
    "EURGBP": 0.8609,
    "EURJPY": 161.52,
    "GBPJPY": 187.66,
}

# FX Forward points (basis, by tenor)  value = spot + fwd_pts/10000
_FX_FORWARD_PTS: Dict[str, Dict[str, float]] = {
    "EURUSD": {"1M": -2.5, "3M": -7.8, "6M": -15.3, "1Y": -28.6},
    "USDJPY": {"1M": 30.2,  "3M": 91.5,  "6M": 182.0, "1Y": 364.8},
    "GBPUSD": {"1M": -3.1, "3M": -9.2, "6M": -18.5, "1Y": -35.0},
    "USDCAD": {"1M": 7.2,  "3M": 21.5,  "6M": 43.0,  "1Y": 86.0},
    "AUDUSD": {"1M": -1.8, "3M": -5.3,  "6M": -10.5, "1Y": -20.8},
    "USDCHF": {"1M": -4.2, "3M": -12.5, "6M": -24.8, "1Y": -46.5},
    "NZDUSD": {"1M": -1.5, "3M": -4.4,  "6M": -8.8,  "1Y": -17.5},
    "EURGBP": {"1M": 0.8,  "3M": 2.4,   "6M": 4.8,   "1Y": 9.6},
    "EURJPY": {"1M": 28.5, "3M": 86.0,  "6M": 171.5, "1Y": 343.0},
    "GBPJPY": {"1M": 32.3, "3M": 97.0,  "6M": 194.2, "1Y": 388.5},
}

# FX vol scalars (annualised, decimal)
_FX_VOL: Dict[str, float] = {
    "EURUSD": 0.0732,
    "USDJPY": 0.0854,
    "GBPUSD": 0.0823,
    "USDCAD": 0.0641,
    "AUDUSD": 0.0912,
    "USDCHF": 0.0671,
    "NZDUSD": 0.0978,
    "EURGBP": 0.0589,
    "EURJPY": 0.0942,
    "GBPJPY": 0.1023,
}

# Symbol → reporting currency mapping (used for exposure conversion)
_SYMBOL_CCY: Dict[str, str] = {
    "AAPL": "USD", "MSFT": "USD", "GOOGL": "USD", "AMZN": "USD",
    "TSLA": "USD", "META": "USD", "NVDA": "USD",
    "SHELL": "GBP", "BP": "GBP", "HSBA": "GBP",
    "ASML": "EUR", "SAP": "EUR", "SIE": "EUR",
    "TM":   "JPY", "SONY": "JPY", "7203": "JPY",
    "RY":   "CAD", "TD":   "CAD", "BNS": "CAD",
}

ASOF = "2026-02-19T09:00:00Z"

# ─────────────────── FX Provider ──────────────────────────────────────────────


def get_fx_spot(pair: str) -> Dict[str, Any]:
    pair = pair.upper()
    if pair not in _FX_SPOT:
        raise ValueError(f"Unknown pair: {pair}")
    spot = _FX_SPOT[pair]
    return {
        "pair": pair,
        "spot": spot,
        "asof": ASOF,
        "hash": _sha256({"pair": pair, "spot": spot}),
        "audit_chain_head_hash": _chain_head(),
    }


def get_fx_forward(pair: str, tenor: str) -> Dict[str, Any]:
    pair = pair.upper()
    tenor = tenor.upper()
    if pair not in _FX_SPOT:
        raise ValueError(f"Unknown pair: {pair}")
    spot = _FX_SPOT[pair]
    pts = _FX_FORWARD_PTS.get(pair, {}).get(tenor, 0.0)
    forward = round(spot + pts / 10000, 6)
    return {
        "pair": pair,
        "tenor": tenor,
        "spot": spot,
        "forward_pts": pts,
        "forward": forward,
        "asof": ASOF,
        "hash": _sha256({"pair": pair, "tenor": tenor, "forward": forward}),
        "audit_chain_head_hash": _chain_head(),
    }


def get_fx_vol(pair: str) -> Dict[str, Any]:
    pair = pair.upper()
    if pair not in _FX_VOL:
        raise ValueError(f"Unknown pair: {pair}")
    vol = _FX_VOL[pair]
    return {
        "pair": pair,
        "vol": vol,
        "vol_pct": round(vol * 100, 4),
        "asof": ASOF,
        "hash": _sha256({"pair": pair, "vol": vol}),
        "audit_chain_head_hash": _chain_head(),
    }


# ─────────────────── FX Exposure Calculator ───────────────────────────────────


def _convert_to_base(amount: float, native_ccy: str, base_ccy: str) -> float:
    """Convert native amount to base currency using fixture spots."""
    if native_ccy == base_ccy:
        return amount
    pair_direct = native_ccy + base_ccy
    pair_inverse = base_ccy + native_ccy
    if pair_direct in _FX_SPOT:
        return amount * _FX_SPOT[pair_direct]
    if pair_inverse in _FX_SPOT:
        return amount / _FX_SPOT[pair_inverse]
    # Cross via USD
    if native_ccy != "USD" and base_ccy != "USD":
        in_usd = _convert_to_base(amount, native_ccy, "USD")
        return _convert_to_base(in_usd, "USD", base_ccy)
    return amount  # fallback: 1:1


def compute_fx_exposure(portfolio: List[Dict[str, Any]], base_ccy: str = "USD") -> Dict[str, Any]:
    """
    Compute FX exposure by currency for a portfolio.
    portfolio items: {symbol, notional, native_ccy (optional)}
    """
    base_ccy = base_ccy.upper()
    exposure_by_ccy: Dict[str, float] = {}
    rows = []

    for item in sorted(portfolio, key=lambda x: x.get("symbol", "")):
        symbol = item.get("symbol", "UNK")
        notional = float(item.get("notional", 0.0))
        native_ccy = item.get("native_ccy") or _SYMBOL_CCY.get(symbol, "USD")
        native_ccy = native_ccy.upper()
        base_amount = _convert_to_base(notional, native_ccy, base_ccy)
        exposure_by_ccy[native_ccy] = round(
            exposure_by_ccy.get(native_ccy, 0.0) + base_amount, 6
        )
        rows.append({
            "symbol": symbol,
            "native_ccy": native_ccy,
            "notional_native": notional,
            "notional_base": round(base_amount, 6),
        })

    total_base = round(sum(exposure_by_ccy.values()), 6)
    pairs_used = sorted(set(
        (r["native_ccy"] + base_ccy if r["native_ccy"] != base_ccy else "")
        for r in rows if r["native_ccy"] != base_ccy
    ))
    pairs_used = [p for p in pairs_used if p]

    output = {
        "base_ccy": base_ccy,
        "total_base": total_base,
        "exposure_by_ccy": {k: v for k, v in sorted(exposure_by_ccy.items())},
        "rows": rows,
        "pairs_used": pairs_used,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    output["output_hash"] = _sha256(output)
    return output


# ─────────────────── FX Shock support for Scenario DSL ────────────────────────


def apply_fx_shocks(
    exposure: Dict[str, Any],
    fx_shocks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply FX shocks {pair, pct} to an existing exposure output.
    Returns shocked exposure + delta.
    """
    base_exp = dict(exposure.get("exposure_by_ccy", {}))
    shocked_exp: Dict[str, float] = {}
    shock_map: Dict[str, float] = {}
    for shock in fx_shocks:
        pair = shock.get("pair", "").upper()
        pct = float(shock.get("pct", 0.0))
        shock_map[pair] = pct

    base_ccy = exposure.get("base_ccy", "USD")

    for ccy, base_amount in base_exp.items():
        # Find matching shock
        pair = ccy + base_ccy
        inv_pair = base_ccy + ccy
        pct = shock_map.get(pair, shock_map.get(inv_pair, 0.0))
        if pct != 0.0:
            # spot shock: divide exposure by (1 + pct/100) for a currency appreciation
            shocked_exp[ccy] = round(base_amount / (1.0 + pct / 100.0), 6)
        else:
            shocked_exp[ccy] = base_amount

    shocked_total = round(sum(shocked_exp.values()), 6)
    delta_total = round(shocked_total - exposure.get("total_base", 0.0), 6)

    result = {
        "base_ccy": base_ccy,
        "shocked_total_base": shocked_total,
        "original_total_base": exposure.get("total_base", 0.0),
        "delta_base": delta_total,
        "shocked_exposure_by_ccy": {k: v for k, v in sorted(shocked_exp.items())},
        "fx_shocks_applied": fx_shocks,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    result["output_hash"] = _sha256(result)
    return result


# ─────────────────── Pydantic Request / Response Models ───────────────────────


class FXExposureRequest(BaseModel):
    portfolio: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL", "notional": 150000, "native_ccy": "USD"},
            {"symbol": "SHELL", "notional": 80000, "native_ccy": "GBP"},
            {"symbol": "ASML",  "notional": 60000, "native_ccy": "EUR"},
            {"symbol": "TM",    "notional": 5000000, "native_ccy": "JPY"},
        ]
    )
    base_ccy: str = Field("USD")


class FXShockRequest(BaseModel):
    exposure: Dict[str, Any]
    fx_shocks: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"pair": "EURUSD", "pct": -5.0},
            {"pair": "GBPUSD", "pct": -3.0},
        ]
    )


# ─────────────────── FastAPI Router ───────────────────────────────────────────

fx_router = APIRouter(prefix="/fx", tags=["fx"])


@fx_router.get("/spot")
def api_fx_spot(pair: str = "EURUSD"):
    try:
        return get_fx_spot(pair)
    except ValueError as e:
        raise HTTPException(400, str(e))


@fx_router.get("/forward")
def api_fx_forward(pair: str = "EURUSD", tenor: str = "3M"):
    try:
        return get_fx_forward(pair, tenor)
    except ValueError as e:
        raise HTTPException(400, str(e))


@fx_router.get("/vol")
def api_fx_vol(pair: str = "EURUSD"):
    try:
        return get_fx_vol(pair)
    except ValueError as e:
        raise HTTPException(400, str(e))


@fx_router.get("/pairs")
def api_fx_pairs():
    return {
        "pairs": sorted(_FX_SPOT.keys()),
        "tenors": ["1M", "3M", "6M", "1Y"],
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


@fx_router.post("/exposure")
def api_fx_exposure(req: FXExposureRequest):
    return compute_fx_exposure(req.portfolio, req.base_ccy)


@fx_router.post("/shock")
def api_fx_shock(req: FXShockRequest):
    return apply_fx_shocks(req.exposure, req.fx_shocks)


# ─────────────────── Exports Router ───────────────────────────────────────────

fx_exports_router = APIRouter(prefix="/exports", tags=["fx-exports"])


class FXPackRequest(BaseModel):
    portfolio: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"symbol": "AAPL", "notional": 150000, "native_ccy": "USD"},
            {"symbol": "SHELL", "notional": 80000, "native_ccy": "GBP"},
        ]
    )
    base_ccy: str = "USD"
    fx_shocks: List[Dict[str, Any]] = Field(default_factory=list)


@fx_exports_router.post("/fx-pack")
def api_fx_pack(req: FXPackRequest):
    exposure = compute_fx_exposure(req.portfolio, req.base_ccy)
    shocked = None
    if req.fx_shocks:
        shocked = apply_fx_shocks(exposure, req.fx_shocks)
    pack = {
        "pack_type": "fx-risk-pack",
        "version": FX_VERSION,
        "exposure": exposure,
        "shocked": shocked,
        "spots": {p: _FX_SPOT[p] for p in sorted(_FX_SPOT.keys())},
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    pack["pack_hash"] = _sha256(pack)
    return pack
