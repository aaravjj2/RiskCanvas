"""
Tests for Stress Library + Compare API (v3.5+)

Covers:
- Preset list + get endpoints
- Apply preset endpoint
- Compare runs delta computation
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


EQUITY_PORTFOLIO = {
    "assets": [
        {"symbol": "AAPL", "type": "stock", "quantity": 10,
         "price": 150.0, "current_price": 150.0},
        {"symbol": "MSFT", "type": "stock", "quantity": 5,
         "price": 300.0, "current_price": 300.0},
    ]
}


class TestStressPresets:
    def test_list_presets_200(self):
        r = client.get("/stress/presets")
        assert r.status_code == 200

    def test_list_presets_count(self):
        r = client.get("/stress/presets")
        assert r.json()["count"] == 5

    def test_list_presets_ids(self):
        r = client.get("/stress/presets")
        ids = {p["preset_id"] for p in r.json()["presets"]}
        assert "rates_up_200bp" in ids
        assert "equity_down_10pct" in ids

    def test_list_presets_each_has_hash(self):
        r = client.get("/stress/presets")
        for p in r.json()["presets"]:
            assert "preset_hash" in p
            assert len(p["preset_hash"]) == 64

    def test_list_presets_deterministic(self):
        h1 = {p["preset_id"]: p["preset_hash"] for p in client.get("/stress/presets").json()["presets"]}
        h2 = {p["preset_id"]: p["preset_hash"] for p in client.get("/stress/presets").json()["presets"]}
        assert h1 == h2

    def test_get_preset_200(self):
        r = client.get("/stress/presets/rates_up_200bp")
        assert r.status_code == 200
        assert r.json()["preset_id"] == "rates_up_200bp"

    def test_get_preset_404(self):
        r = client.get("/stress/presets/nonexistent")
        assert r.status_code == 404

    def test_preset_shocks_correct_type(self):
        r = client.get("/stress/presets/equity_down_10pct")
        shocks = r.json()["shocks"]
        assert shocks["equity_shift_pct"] == -0.10


class TestStressApply:
    def test_apply_equity_down_200(self):
        r = client.post("/stress/apply", json={
            "preset_id": "equity_down_10pct",
            "portfolio": EQUITY_PORTFOLIO,
        })
        assert r.status_code == 200

    def test_apply_returns_stressed_portfolio(self):
        r = client.post("/stress/apply", json={
            "preset_id": "equity_down_10pct",
            "portfolio": EQUITY_PORTFOLIO,
        })
        data = r.json()
        assert "stressed_portfolio" in data
        assert "assets" in data["stressed_portfolio"]

    def test_apply_equity_down_reduces_price(self):
        r = client.post("/stress/apply", json={
            "preset_id": "equity_down_10pct",
            "portfolio": EQUITY_PORTFOLIO,
        })
        stressed = r.json()["stressed_portfolio"]["assets"]
        for i, asset in enumerate(stressed):
            orig = EQUITY_PORTFOLIO["assets"][i]["current_price"]
            assert asset["current_price"] < orig

    def test_apply_returns_hashes(self):
        r = client.post("/stress/apply", json={
            "preset_id": "equity_down_10pct",
            "portfolio": EQUITY_PORTFOLIO,
        })
        data = r.json()
        assert len(data["input_hash"]) == 64
        assert len(data["stressed_input_hash"]) == 64
        assert data["input_hash"] != data["stressed_input_hash"]

    def test_apply_deterministic(self):
        payload = {"preset_id": "equity_down_10pct", "portfolio": EQUITY_PORTFOLIO}
        r1 = client.post("/stress/apply", json=payload).json()
        r2 = client.post("/stress/apply", json=payload).json()
        assert r1["input_hash"] == r2["input_hash"]
        assert r1["stressed_input_hash"] == r2["stressed_input_hash"]

    def test_apply_unknown_preset_422(self):
        r = client.post("/stress/apply", json={
            "preset_id": "not_a_real_preset",
            "portfolio": EQUITY_PORTFOLIO,
        })
        assert r.status_code == 422

    def test_apply_shocks_in_response(self):
        r = client.post("/stress/apply", json={
            "preset_id": "equity_down_10pct",
            "portfolio": EQUITY_PORTFOLIO,
        })
        assert r.json()["shocks_applied"]["equity_shift_pct"] == -0.10


class TestCompareRuns:
    def test_compare_returns_200(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa", "portfolio_value": 1000.0, "total_pnl": 50.0, "var_95": 25.0},
            "run_b": {"run_id": "run-bbb", "portfolio_value": 950.0,  "total_pnl": 30.0, "var_95": 30.0},
        })
        assert r.status_code == 200

    def test_compare_delta_pnl(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa", "total_pnl": 50.0},
            "run_b": {"run_id": "run-bbb", "total_pnl": 30.0},
        })
        data = r.json()
        assert data["delta_pnl"] == pytest.approx(-20.0, abs=1e-6)

    def test_compare_delta_var_95(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa", "var_95": 25.0},
            "run_b": {"run_id": "run-bbb", "var_95": 30.0},
        })
        assert r.json()["delta_var_95"] == pytest.approx(5.0, abs=1e-6)

    def test_compare_delta_portfolio_value(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa", "portfolio_value": 10000.0},
            "run_b": {"run_id": "run-bbb", "portfolio_value": 9500.0},
        })
        assert r.json()["delta_portfolio_value"] == pytest.approx(-500.0, abs=1e-6)

    def test_compare_run_ids_in_response(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa"},
            "run_b": {"run_id": "run-bbb"},
        })
        data = r.json()
        assert data["run_id_a"] == "run-aaa"
        assert data["run_id_b"] == "run-bbb"

    def test_compare_summary_present(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa", "total_pnl": 50.0, "var_95": 25.0},
            "run_b": {"run_id": "run-bbb", "total_pnl": 30.0, "var_95": 30.0},
        })
        assert "summary" in r.json()
        assert len(r.json()["summary"]) > 0

    def test_compare_null_fields_when_missing(self):
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "run-aaa"},
            "run_b": {"run_id": "run-bbb"},
        })
        data = r.json()
        assert data["delta_pnl"] is None
        assert data["delta_var_95"] is None

    def test_compare_sign_correct_var_increase(self):
        """b.var > a.var → delta_var > 0 (risk increased)."""
        r = client.post("/compare/runs", json={
            "run_a": {"run_id": "a", "var_95": 100.0},
            "run_b": {"run_id": "b", "var_95": 150.0},
        })
        assert r.json()["delta_var_95"] > 0

    def test_compare_deterministic(self):
        payload = {
            "run_a": {"run_id": "run-aaa", "portfolio_value": 1000.0, "total_pnl": 50.0},
            "run_b": {"run_id": "run-bbb", "portfolio_value": 900.0, "total_pnl": 40.0},
        }
        r1 = client.post("/compare/runs", json=payload).json()
        r2 = client.post("/compare/runs", json=payload).json()
        assert r1["delta_pnl"] == r2["delta_pnl"]
        assert r1["delta_portfolio_value"] == r2["delta_portfolio_value"]
