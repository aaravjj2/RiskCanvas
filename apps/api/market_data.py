"""
RiskCanvas v4.6.0 — Market Data Provider Abstraction

Provides a deterministic interface for market data with three implementations:
1. FixtureMarketDataProvider (DEFAULT, DEMO + tests) — loads from /fixtures/market/
2. LocalMarketDataProvider (OPTIONAL) — reads local cached files, guarded by MARKET_PROVIDER=local
3. StubRemoteProvider (OPTIONAL placeholder) — hard-fails without API keys, NEVER in tests

All responses include: asof, input_hash, output_hash, audit_chain_head_hash
"""
from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ─────────────────────────── Constants ──────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "market"
PROVIDER_ENV = os.getenv("MARKET_PROVIDER", "fixture").lower()  # fixture | local | remote
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


# ─────────────────────────── Helpers ────────────────────────────────────────

def _sha256(data: Any) -> str:
    """Deterministic SHA-256 of canonical JSON."""
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _input_hash(**kwargs: Any) -> str:
    return _sha256(kwargs)


def _chain_head() -> str:
    """Returns deterministic audit chain head (DEMO constant)."""
    return "a1b2c3d4e5f60718"


# ─────────────────────────── Abstract interface ──────────────────────────────

class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""

    provider_id: str = "abstract"

    @abstractmethod
    def get_asof(self) -> Dict[str, Any]:
        """Returns the fixed as-of date/time for this provider."""

    @abstractmethod
    def get_spot(self, symbol: str) -> Dict[str, Any]:
        """Returns deterministic spot price for a symbol."""

    @abstractmethod
    def get_series(self, symbol: str, start: str, end: str, freq: str) -> Dict[str, Any]:
        """Returns deterministic OHLCV series for a symbol."""

    @abstractmethod
    def get_rates_curve(self, curve_id: str) -> Dict[str, Any]:
        """Returns deterministic interest-rate curve points."""


# ─────────────────────────── Fixture Provider (DEFAULT) ──────────────────────

class FixtureMarketDataProvider(MarketDataProvider):
    """
    DEFAULT provider. Loads from /fixtures/market/.
    Stable ordering, canonical JSON, deterministic rounding.
    Safe for DEMO, tests, and CI.
    """
    provider_id = "fixture"

    def __init__(self) -> None:
        if not FIXTURES_DIR.exists():
            raise RuntimeError(f"Market fixtures directory not found: {FIXTURES_DIR}")
        with open(FIXTURES_DIR / "asof.json") as f:
            self._asof_data = json.load(f)
        with open(FIXTURES_DIR / "spot.json") as f:
            self._spot_data = json.load(f)

    def get_asof(self) -> Dict[str, Any]:
        ih = _input_hash(provider=self.provider_id)
        oh = _sha256(self._asof_data)
        return {
            **self._asof_data,
            "asof": self._asof_data["asof"],
            "input_hash": ih,
            "output_hash": oh,
            "audit_chain_head_hash": _chain_head(),
        }

    def get_spot(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        spots = self._spot_data.get("spots", {})
        if symbol not in spots:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found in fixture data")
        price = round(float(spots[symbol]), 8)
        ih = _input_hash(provider=self.provider_id, symbol=symbol)
        oh = _sha256({"symbol": symbol, "price": price})
        return {
            "symbol": symbol,
            "price": price,
            "asof": self._asof_data["asof"],
            "provider": self.provider_id,
            "input_hash": ih,
            "output_hash": oh,
            "audit_chain_head_hash": _chain_head(),
        }

    def get_series(self, symbol: str, start: str, end: str, freq: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        series_file = FIXTURES_DIR / "series" / f"{symbol}.json"
        if not series_file.exists():
            raise HTTPException(status_code=404, detail=f"No fixture series for {symbol}")
        with open(series_file) as f:
            raw = json.load(f)
        # Filter by date range (stable ordering)
        filtered = [
            row for row in raw["series"]
            if start <= row["date"] <= end
        ]
        # Sort deterministically
        filtered.sort(key=lambda r: r["date"])
        ih = _input_hash(provider=self.provider_id, symbol=symbol, start=start, end=end, freq=freq)
        oh = _sha256(filtered)
        return {
            "symbol": symbol,
            "freq": freq,
            "start": start,
            "end": end,
            "provider": self.provider_id,
            "asof": raw["asof"],
            "count": len(filtered),
            "series": filtered,
            "input_hash": ih,
            "output_hash": oh,
            "audit_chain_head_hash": _chain_head(),
        }

    def get_rates_curve(self, curve_id: str) -> Dict[str, Any]:
        curve_file = FIXTURES_DIR / "curves" / f"{curve_id}.json"
        if not curve_file.exists():
            raise HTTPException(status_code=404, detail=f"No fixture curve for {curve_id}")
        with open(curve_file) as f:
            raw = json.load(f)
        # Sort by tenor_years for deterministic ordering
        points = sorted(raw["points"], key=lambda p: float(p["tenor_years"]))
        ih = _input_hash(provider=self.provider_id, curve_id=curve_id)
        oh = _sha256(points)
        return {
            "curve_id": curve_id,
            "currency": raw.get("currency"),
            "index": raw.get("index"),
            "provider": self.provider_id,
            "asof": raw["asof"],
            "count": len(points),
            "points": points,
            "input_hash": ih,
            "output_hash": oh,
            "audit_chain_head_hash": _chain_head(),
        }


# ─────────────────────────── Local Provider (OPTIONAL) ───────────────────────

class LocalMarketDataProvider(MarketDataProvider):
    """
    OPTIONAL local provider. Reads from local cached files.
    Only available when MARKET_PROVIDER=local AND DEMO_MODE=false.
    In tests this is never used.
    """
    provider_id = "local"

    def __init__(self) -> None:
        if DEMO_MODE:
            raise RuntimeError(
                "LocalMarketDataProvider cannot be used in DEMO_MODE. "
                "Set DEMO_MODE=false and MARKET_PROVIDER=local."
            )
        self._local_dir = Path(os.getenv("LOCAL_MARKET_CACHE_DIR", "/tmp/riskcanvas/market"))
        if not self._local_dir.exists():
            raise RuntimeError(
                f"Local market cache dir not found: {self._local_dir}. "
                "Populate it before using local provider."
            )

    def get_asof(self) -> Dict[str, Any]:
        raise NotImplementedError("LocalMarketDataProvider.get_asof not implemented for this demo")

    def get_spot(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("LocalMarketDataProvider.get_spot not implemented for this demo")

    def get_series(self, symbol: str, start: str, end: str, freq: str) -> Dict[str, Any]:
        raise NotImplementedError("LocalMarketDataProvider.get_series not implemented for this demo")

    def get_rates_curve(self, curve_id: str) -> Dict[str, Any]:
        raise NotImplementedError("LocalMarketDataProvider.get_rates_curve not implemented for this demo")


# ─────────────────────────── Stub Remote Provider (PLACEHOLDER) ──────────────

class StubRemoteProvider(MarketDataProvider):
    """
    OPTIONAL placeholder for production remote provider.
    Hard-fails with clear error if enabled without API keys.
    NEVER used in tests.
    """
    provider_id = "remote"

    def __init__(self) -> None:
        api_key = os.getenv("MARKET_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "StubRemoteProvider requires MARKET_API_KEY env var. "
                "This provider is NEVER enabled in tests or DEMO mode."
            )
        raise RuntimeError(
            "StubRemoteProvider is a placeholder only — actual live data integration "
            "requires a licensed market data subscription. This provider is intentionally "
            "disabled to prevent accidental external network calls."
        )

    def get_asof(self) -> Dict[str, Any]:
        raise NotImplementedError

    def get_spot(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_series(self, symbol: str, start: str, end: str, freq: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_rates_curve(self, curve_id: str) -> Dict[str, Any]:
        raise NotImplementedError


# ─────────────────────────── Factory ─────────────────────────────────────────

def get_market_data_provider() -> MarketDataProvider:
    """
    Factory function. Returns the correct provider based on env vars.
    In DEMO_MODE or when MARKET_PROVIDER=fixture → always returns FixtureMarketDataProvider.
    """
    if DEMO_MODE or PROVIDER_ENV == "fixture":
        return FixtureMarketDataProvider()
    if PROVIDER_ENV == "local":
        return LocalMarketDataProvider()
    if PROVIDER_ENV == "remote":
        return StubRemoteProvider()
    # Default: fixture
    return FixtureMarketDataProvider()


# ─────────────────────────── Pydantic Schemas ────────────────────────────────

class MarketSeriesRequest(BaseModel):
    symbol: str
    start: str = "2026-01-01"
    end: str = "2026-01-15"
    freq: str = "1d"


class MarketAsofResponse(BaseModel):
    asof: str
    timezone: Optional[str] = None
    session: Optional[str] = None
    provider: str
    input_hash: str
    output_hash: str
    audit_chain_head_hash: str


class MarketSpotResponse(BaseModel):
    symbol: str
    price: float
    asof: str
    provider: str
    input_hash: str
    output_hash: str
    audit_chain_head_hash: str


class MarketSeriesPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketSeriesResponse(BaseModel):
    symbol: str
    freq: str
    start: str
    end: str
    provider: str
    asof: str
    count: int
    series: List[MarketSeriesPoint]
    input_hash: str
    output_hash: str
    audit_chain_head_hash: str


class CurvePoint(BaseModel):
    tenor: str
    tenor_years: float
    rate: float


class MarketCurveResponse(BaseModel):
    curve_id: str
    currency: Optional[str] = None
    index: Optional[str] = None
    provider: str
    asof: str
    count: int
    points: List[CurvePoint]
    input_hash: str
    output_hash: str
    audit_chain_head_hash: str


# ─────────────────────────── Router ──────────────────────────────────────────

market_router = APIRouter(prefix="/market", tags=["market"])


@market_router.get("/asof")
def market_asof() -> Dict[str, Any]:
    """Returns the as-of date/time for the active market data provider."""
    provider = get_market_data_provider()
    return provider.get_asof()


@market_router.get("/spot")
def market_spot(symbol: str) -> Dict[str, Any]:
    """Returns deterministic spot price for a symbol."""
    provider = get_market_data_provider()
    return provider.get_spot(symbol)


@market_router.post("/series")
def market_series(req: MarketSeriesRequest) -> Dict[str, Any]:
    """Returns deterministic OHLCV series for a symbol."""
    provider = get_market_data_provider()
    return provider.get_series(req.symbol, req.start, req.end, req.freq)


@market_router.get("/curves/{curve_id}")
def market_curve(curve_id: str) -> Dict[str, Any]:
    """Returns deterministic interest-rate curve points."""
    provider = get_market_data_provider()
    return provider.get_rates_curve(curve_id)
