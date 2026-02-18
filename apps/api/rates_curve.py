"""
Rates Curve API Router (v3.4+)

Exposes:
  POST /rates/curve/bootstrap     - bootstrap from instrument list
  POST /rates/bond/price-curve    - price bond using a discount-factor curve
  GET  /rates/fixtures/simple     - return simple fixture for demo
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

from src.rates import bootstrap_rates_curve, bond_price_from_curve

rates_router = APIRouter(prefix="/rates", tags=["rates"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CurveInstrument(BaseModel):
    type: str        # "deposit" | "swap"
    tenor: float
    rate: float
    periods_per_year: Optional[int] = None


class RatesBootstrapRequest(BaseModel):
    instruments: List[CurveInstrument]


class ZeroRateItem(BaseModel):
    tenor: float
    zero_rate: float


class DiscountFactorItem(BaseModel):
    tenor: float
    df: float


class RatesBootstrapResponse(BaseModel):
    zero_rates: List[ZeroRateItem]
    discount_factors: List[DiscountFactorItem]
    curve_hash: str
    instruments_count: int


class BondCurvePriceRequest(BaseModel):
    face_value: float = 1000.0
    coupon_rate: float = 0.05
    years_to_maturity: float = 5.0
    periods_per_year: int = 2
    discount_factors: List[DiscountFactorItem]


class BondCurvePriceResponse(BaseModel):
    price: float
    face_value: float
    coupon_rate: float
    years_to_maturity: float
    curve_tenors: int


# ── Simple fixture ────────────────────────────────────────────────────────────

SIMPLE_FIXTURE = [
    {"type": "deposit", "tenor": 0.25, "rate": 0.04},
    {"type": "deposit", "tenor": 0.5,  "rate": 0.042},
    {"type": "deposit", "tenor": 1.0,  "rate": 0.045},
    {"type": "swap",    "tenor": 2.0,  "rate": 0.048, "periods_per_year": 2},
    {"type": "swap",    "tenor": 5.0,  "rate": 0.052, "periods_per_year": 2},
    {"type": "swap",    "tenor": 10.0, "rate": 0.055, "periods_per_year": 2},
]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@rates_router.get("/fixtures/simple")
async def get_rates_fixture():
    """Return the simple demo fixture for curve bootstrapping."""
    return {"instruments": SIMPLE_FIXTURE, "description": "Simple deposit + swap curve for demo"}


@rates_router.post("/curve/bootstrap", response_model=RatesBootstrapResponse)
async def bootstrap_curve(request: RatesBootstrapRequest):
    """Bootstrap a zero-rate + discount-factor curve from a list of instruments."""
    if not request.instruments:
        raise HTTPException(status_code=422, detail="instruments list must not be empty")

    try:
        instrs = [i.model_dump(exclude_none=True) for i in request.instruments]
        result = bootstrap_rates_curve(instrs)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return RatesBootstrapResponse(
        zero_rates=[ZeroRateItem(**z) for z in result["zero_rates"]],
        discount_factors=[DiscountFactorItem(**d) for d in result["discount_factors"]],
        curve_hash=result["curve_hash"],
        instruments_count=len(result["instruments"]),
    )


@rates_router.post("/bond/price-curve", response_model=BondCurvePriceResponse)
async def price_bond_with_curve(request: BondCurvePriceRequest):
    """Price a bond using a provided discount-factor curve."""
    dfs = [{"tenor": item.tenor, "df": item.df} for item in request.discount_factors]
    if not dfs:
        raise HTTPException(status_code=422, detail="discount_factors must not be empty")

    price = bond_price_from_curve(
        face_value=request.face_value,
        coupon_rate=request.coupon_rate,
        years_to_maturity=request.years_to_maturity,
        discount_factors=dfs,
        periods_per_year=request.periods_per_year,
    )

    return BondCurvePriceResponse(
        price=price,
        face_value=request.face_value,
        coupon_rate=request.coupon_rate,
        years_to_maturity=request.years_to_maturity,
        curve_tenors=len(dfs),
    )
