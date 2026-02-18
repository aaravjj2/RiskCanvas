"""
Tests for Rates Curve API (v3.4+)

Covers:
- Schema validation
- Deterministic hashes
- Fixtures endpoint
- Bond price with curve
"""

import os
import pytest

os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app
from sqlmodel import SQLModel
from database import db

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    SQLModel.metadata.create_all(db.engine)
    yield


SIMPLE_INSTRUMENTS = [
    {"type": "deposit", "tenor": 0.25, "rate": 0.04},
    {"type": "deposit", "tenor": 0.5,  "rate": 0.042},
    {"type": "deposit", "tenor": 1.0,  "rate": 0.045},
    {"type": "swap",    "tenor": 2.0,  "rate": 0.048, "periods_per_year": 2},
    {"type": "swap",    "tenor": 5.0,  "rate": 0.052, "periods_per_year": 2},
]


class TestRatesFixtureEndpoint:
    def test_fixture_returns_instruments(self):
        r = client.get("/rates/fixtures/simple")
        assert r.status_code == 200
        data = r.json()
        assert "instruments" in data
        assert len(data["instruments"]) >= 3

    def test_fixture_instrument_schema(self):
        r = client.get("/rates/fixtures/simple")
        instrs = r.json()["instruments"]
        for instr in instrs:
            assert "type" in instr
            assert "tenor" in instr
            assert "rate" in instr


class TestRatesBootstrap:
    def test_bootstrap_returns_200(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        assert r.status_code == 200

    def test_bootstrap_returns_curve_hash(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        data = r.json()
        assert "curve_hash" in data
        assert len(data["curve_hash"]) == 64

    def test_bootstrap_zero_rates_count(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        data = r.json()
        assert len(data["zero_rates"]) == len(SIMPLE_INSTRUMENTS)

    def test_bootstrap_df_count(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        data = r.json()
        assert len(data["discount_factors"]) == len(SIMPLE_INSTRUMENTS)

    def test_bootstrap_determinism(self):
        r1 = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        r2 = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        assert r1.json()["curve_hash"] == r2.json()["curve_hash"]

    def test_bootstrap_df_monotone(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        dfs = [item["df"] for item in r.json()["discount_factors"]]
        for i in range(len(dfs) - 1):
            assert dfs[i] >= dfs[i + 1], f"DF not decreasing at index {i}"

    def test_bootstrap_tenors_ascending(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        tenors = [item["tenor"] for item in r.json()["zero_rates"]]
        assert tenors == sorted(tenors)

    def test_bootstrap_empty_instruments_422(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": []})
        assert r.status_code == 422

    def test_bootstrap_instruments_count_in_response(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        assert r.json()["instruments_count"] == len(SIMPLE_INSTRUMENTS)

    def test_bootstrap_unknown_type_422(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": [
            {"type": "futures", "tenor": 1.0, "rate": 0.04}
        ]})
        assert r.status_code == 422


class TestBondPriceWithCurve:
    def _get_dfs(self):
        r = client.post("/rates/curve/bootstrap", json={"instruments": SIMPLE_INSTRUMENTS})
        return r.json()["discount_factors"]

    def test_bond_price_curve_returns_200(self):
        dfs = self._get_dfs()
        r = client.post("/rates/bond/price-curve", json={
            "face_value": 1000.0,
            "coupon_rate": 0.05,
            "years_to_maturity": 3.0,
            "periods_per_year": 2,
            "discount_factors": dfs,
        })
        assert r.status_code == 200

    def test_bond_price_curve_positive(self):
        dfs = self._get_dfs()
        r = client.post("/rates/bond/price-curve", json={
            "face_value": 1000.0,
            "coupon_rate": 0.05,
            "years_to_maturity": 3.0,
            "periods_per_year": 2,
            "discount_factors": dfs,
        })
        assert r.json()["price"] > 0

    def test_bond_price_curve_determinism(self):
        dfs = self._get_dfs()
        payload = {
            "face_value": 1000.0, "coupon_rate": 0.05,
            "years_to_maturity": 3.0, "periods_per_year": 2,
            "discount_factors": dfs,
        }
        p1 = client.post("/rates/bond/price-curve", json=payload).json()["price"]
        p2 = client.post("/rates/bond/price-curve", json=payload).json()["price"]
        assert p1 == p2

    def test_bond_price_empty_dfs_422(self):
        r = client.post("/rates/bond/price-curve", json={
            "face_value": 1000.0, "coupon_rate": 0.05,
            "years_to_maturity": 3.0, "periods_per_year": 2,
            "discount_factors": [],
        })
        assert r.status_code == 422
