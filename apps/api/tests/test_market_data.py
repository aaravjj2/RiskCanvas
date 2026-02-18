"""Tests for market_data.py — v4.6.0"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DEMO_MODE"] = "true"

from fastapi import HTTPException
from market_data import (
    FixtureMarketDataProvider,
    get_market_data_provider,
    MarketSeriesRequest,
)


class TestFixtureMarketDataProvider:
    def setup_method(self):
        self.provider = FixtureMarketDataProvider()

    def test_provider_id(self):
        assert self.provider.provider_id == "fixture"

    def test_get_asof_deterministic(self):
        a1 = self.provider.get_asof()
        a2 = self.provider.get_asof()
        assert a1 == a2
        assert "asof" in a1

    def test_get_asof_has_required_fields(self):
        result = self.provider.get_asof()
        assert "asof" in result
        assert "timezone" in result
        assert "session" in result
        assert "provider" in result

    def test_get_spot_known_symbol(self):
        result = self.provider.get_spot("AAPL")
        assert result is not None
        assert "price" in result
        assert float(result["price"]) > 0

    def test_get_spot_all_symbols(self):
        for sym in ["AAPL", "MSFT", "SPY", "GOOGL", "AMZN"]:
            result = self.provider.get_spot(sym)
            assert result is not None, f"Missing spot for {sym}"

    def test_get_spot_unknown_symbol_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            self.provider.get_spot("ZZZZ_FAKE")
        assert exc_info.value.status_code == 404

    def test_get_spot_deterministic(self):
        r1 = self.provider.get_spot("MSFT")
        r2 = self.provider.get_spot("MSFT")
        assert r1 == r2

    def test_get_series_aapl(self):
        result = self.provider.get_series("AAPL", "2026-01-01", "2026-01-15", "1d")
        assert "series" in result
        assert len(result["series"]) >= 1
        assert result["symbol"] == "AAPL"

    def test_get_series_ordering_stable(self):
        r1 = self.provider.get_series("AAPL", "2026-01-01", "2026-01-15", "1d")
        r2 = self.provider.get_series("AAPL", "2026-01-01", "2026-01-15", "1d")
        assert r1 == r2

    def test_get_series_date_ordering(self):
        result = self.provider.get_series("AAPL", "2026-01-01", "2026-01-15", "1d")
        dates = [e["date"] for e in result["series"]]
        assert dates == sorted(dates)

    def test_get_rates_curve_usd_sofr(self):
        result = self.provider.get_rates_curve("USD_SOFR")
        assert result is not None
        assert "curve_id" in result
        assert "points" in result
        assert len(result["points"]) >= 1

    def test_get_rates_curve_unknown_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            self.provider.get_rates_curve("FAKE_CURVE")
        assert exc_info.value.status_code == 404

    def test_get_rates_curve_ordering_stable(self):
        r1 = self.provider.get_rates_curve("USD_SOFR")
        r2 = self.provider.get_rates_curve("USD_SOFR")
        assert r1 == r2

    def test_curve_points_ascending_tenor(self):
        result = self.provider.get_rates_curve("USD_SOFR")
        tenors = [p["tenor_years"] for p in result["points"]]
        assert tenors == sorted(tenors)


class TestMarketRouter:
    """Test via FastAPI TestClient."""

    def setup_method(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from market_data import market_router
        app = FastAPI()
        app.include_router(market_router)
        self.client = TestClient(app)

    def test_asof_endpoint(self):
        resp = self.client.get("/market/asof")
        assert resp.status_code == 200
        data = resp.json()
        assert "asof" in data
        assert "input_hash" in data
        assert "output_hash" in data
        assert "audit_chain_head_hash" in data

    def test_spot_endpoint(self):
        resp = self.client.get("/market/spot?symbol=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert "symbol" in data
        assert data["symbol"] == "AAPL"
        assert "price" in data

    def test_spot_unknown_404(self):
        resp = self.client.get("/market/spot?symbol=ZZFAKE")
        assert resp.status_code == 404

    def test_series_endpoint(self):
        resp = self.client.post("/market/series", json={"symbol": "AAPL"})
        assert resp.status_code == 200
        data = resp.json()
        assert "series" in data

    def test_curve_endpoint(self):
        resp = self.client.get("/market/curves/USD_SOFR")
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data

    def test_curve_unknown_404(self):
        resp = self.client.get("/market/curves/FAKE_CURVE")
        assert resp.status_code == 404

    def test_asof_hash_stable(self):
        r1 = self.client.get("/market/asof").json()
        r2 = self.client.get("/market/asof").json()
        assert r1["output_hash"] == r2["output_hash"]

    def test_spot_no_network(self, monkeypatch):
        """Provider must not make network calls."""
        import socket
        def no_network(*args, **kwargs):
            raise RuntimeError("Network access forbidden in tests")
        monkeypatch.setattr(socket, "getaddrinfo", no_network)
        resp = self.client.get("/market/spot?symbol=MSFT")
        assert resp.status_code == 200
