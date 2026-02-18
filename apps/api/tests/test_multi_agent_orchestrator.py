"""
Tests for multi_agent_orchestrator.py (v3.0)
"""
import os
import pytest
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    """Guarantee DEMO_MODE=true for every test in this module."""
    monkeypatch.setenv("DEMO_MODE", "true")


# ── /orchestrator/plan ────────────────────────────────────────────────────────

class TestOrchestratorPlan:
    def test_plan_returns_200(self):
        r = client.get("/orchestrator/plan")
        assert r.status_code == 200

    def test_plan_has_agents_list(self):
        r = client.get("/orchestrator/plan")
        body = r.json()
        assert "agents" in body
        assert isinstance(body["agents"], list)

    def test_plan_agents_non_empty(self):
        r = client.get("/orchestrator/plan")
        assert len(r.json()["agents"]) >= 3

    def test_plan_has_flow_field(self):
        r = client.get("/orchestrator/plan")
        assert "flow" in r.json()

    def test_plan_each_agent_has_name_and_role(self):
        r = client.get("/orchestrator/plan")
        for agent in r.json()["agents"]:
            assert "name" in agent
            assert "role" in agent

    def test_plan_flow_is_list(self):
        r = client.get("/orchestrator/plan")
        assert isinstance(r.json()["flow"], list)

    def test_plan_response_content_type_json(self):
        r = client.get("/orchestrator/plan")
        assert "application/json" in r.headers["content-type"]


# ── /orchestrator/agents ──────────────────────────────────────────────────────

class TestOrchestratorAgents:
    def test_agents_returns_200(self):
        r = client.get("/orchestrator/agents")
        assert r.status_code == 200

    def test_agents_is_list(self):
        r = client.get("/orchestrator/agents")
        assert isinstance(r.json(), list)

    def test_agents_non_empty(self):
        r = client.get("/orchestrator/agents")
        assert len(r.json()) >= 1

    def test_agents_each_has_name_role(self):
        r = client.get("/orchestrator/agents")
        for a in r.json():
            assert "name" in a
            assert "role" in a


# ── /orchestrator/run ─────────────────────────────────────────────────────────

SAMPLE_PORTFOLIO = {
    "positions": [
        {"symbol": "AAPL", "qty": 100, "price": 150.0, "asset_class": "equity"},
        {"symbol": "MSFT", "qty": 50,  "price": 300.0, "asset_class": "equity"},
    ]
}

class TestOrchestratorRun:
    def test_run_returns_200(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert r.status_code == 200

    def test_run_has_run_id(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert "run_id" in r.json()

    def test_run_id_is_stable(self):
        r1 = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        r2 = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert r1.json()["run_id"] == r2.json()["run_id"]

    def test_run_has_decision_field(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert "decision" in r.json()

    def test_run_has_audit_log(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert "audit_log" in r.json()
        assert isinstance(r.json()["audit_log"], list)

    def test_run_has_sre_checks(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        body = r.json()
        assert "sre_checks" in body

    def test_run_sre_checks_is_list(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert isinstance(r.json()["sre_checks"], list)

    def test_run_sre_checks_non_empty(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert len(r.json()["sre_checks"]) >= 1

    def test_run_audit_log_non_empty(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert len(r.json()["audit_log"]) >= 1

    def test_run_audit_log_entries_have_from_agent_field(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        for entry in r.json()["audit_log"]:
            assert "from_agent" in entry

    def test_run_single_position_portfolio(self):
        portfolio = {"positions": [
            {"symbol": "SPY", "qty": 10, "price": 450.0, "asset_class": "equity"}
        ]}
        r = client.post("/orchestrator/run", json={"portfolio": portfolio})
        assert r.status_code == 200

    def test_run_empty_positions_still_responds(self):
        r = client.post("/orchestrator/run", json={"portfolio": {"positions": []}})
        # Should still respond (may succeed or give validation error — not 500)
        assert r.status_code in (200, 422)

    def test_run_missing_portfolio_field_returns_422(self):
        r = client.post("/orchestrator/run", json={})
        assert r.status_code == 422

    def test_run_timestamp_is_demo_fixed(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        body = r.json()
        # In DEMO_MODE timestamp should be a fixed ISO string
        assert "timestamp" in body
        assert body["timestamp"].startswith("2026-")

    def test_run_has_model_used_field(self):
        r = client.post("/orchestrator/run", json={"portfolio": SAMPLE_PORTFOLIO})
        assert "model_used" in r.json()
