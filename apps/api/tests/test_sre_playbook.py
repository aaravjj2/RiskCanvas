"""
Tests for SRE Playbook Generator (v4.0+)

Covers:
- Empty inputs → follow-up playbook
- Policy-blocked → P0 triage steps
- Pipeline fatal → P0 triage steps
- Playbook hash stability
- Playbook markdown structure
- Distinct inputs → different inputs_hash
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


# ── POST /sre/playbook/generate ──────────────────────────────────────────────

class TestSREPlaybook:
    def _generate(self, payload: dict = None):
        if payload is None:
            payload = {}
        return client.post("/sre/playbook/generate", json=payload)

    def test_empty_inputs_returns_200(self):
        r = self._generate({})
        assert r.status_code == 200

    def test_empty_inputs_all_fields_present(self):
        r = self._generate({})
        data = r.json()
        assert "playbook_hash" in data
        assert "playbook_md" in data
        assert "playbook_json" in data
        assert "inputs_hash" in data

    def test_empty_inputs_produces_follow_up_phase(self):
        r = self._generate({})
        md = r.json()["playbook_md"]
        assert "follow" in md.lower() or "P2" in md or "P3" in md

    def test_blocked_policy_produces_p0_triage(self):
        payload = {
            "policy_gate_result": {"decision": "block", "reasons": [{"code": "TOOL_NOT_ALLOWED"}]}
        }
        r = self._generate(payload)
        assert r.status_code == 200
        md = r.json()["playbook_md"]
        # Should escalate to P0 triage
        assert "P0" in md or "triage" in md.lower()

    def test_pipeline_fatal_produces_p0_triage(self):
        payload = {
            "pipeline_analysis": {"fatal_count": 3, "categories": ["OOM"]}
        }
        r = self._generate(payload)
        assert r.status_code == 200
        md = r.json()["playbook_md"]
        assert "P0" in md or "triage" in md.lower() or "OOM" in md

    def test_playbook_hash_stable_same_inputs(self):
        payload = {
            "policy_gate_result": {"decision": "allow"},
            "platform_health": {"degraded_services": []}
        }
        r1 = self._generate(payload)
        r2 = self._generate(payload)
        assert r1.json()["playbook_hash"] == r2.json()["playbook_hash"]

    def test_different_inputs_different_inputs_hash(self):
        r1 = self._generate({"platform_health": {"degraded_services": []}})
        r2 = self._generate({"platform_health": {"degraded_services": ["db-primary"]}})
        assert r1.json()["inputs_hash"] != r2.json()["inputs_hash"]

    def test_playbook_md_has_headers(self):
        r = self._generate({"policy_gate_result": {"decision": "block", "reasons": []}})
        md = r.json()["playbook_md"]
        assert "##" in md  # markdown section headers

    def test_playbook_json_has_steps(self):
        r = self._generate({})
        pj = r.json()["playbook_json"]
        assert "steps" in pj
        assert len(pj["steps"]) > 0

    def test_platform_health_degraded_triggers_mitigate(self):
        payload = {
            "platform_health": {"degraded_services": ["order-api", "auth-svc"]}
        }
        r = self._generate(payload)
        md = r.json()["playbook_md"]
        assert "mitigate" in md.lower() or "P1" in md

    def test_full_incident_escalates_correctly(self):
        payload = {
            "policy_gate_result": {"decision": "block", "reasons": [{"code": "SECRET_IN_PROMPT"}]},
            "pipeline_analysis": {"fatal_count": 2, "categories": ["OOM", "TIMEOUT"]},
            "platform_health": {"degraded_services": ["db-replica"]}
        }
        r = self._generate(payload)
        data = r.json()
        md = data["playbook_md"]
        pj = data["playbook_json"]
        # Should have all 3 phases
        phases = {s["phase"] for s in pj["steps"]}
        assert "triage" in phases
        assert "mitigate" in phases
        assert "follow_up" in phases

    def test_ts_field_present(self):
        r = self._generate({})
        assert "ts" in r.json()
