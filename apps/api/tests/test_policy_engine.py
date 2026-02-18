"""
Tests for PolicyEngine v2 + Narrative Validator (v3.7+)

Covers:
- Policy allow/block cases
- Tool budget enforcement
- Narrative validator (known/unknown numbers)
- Secret redaction determinism
- Policy apply (sanitize)
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


# ── POST /governance/policy/evaluate ─────────────────────────────────────────

class TestPolicyEvaluate:
    def _eval(self, run_config: dict, mode: str = "DEMO"):
        return client.post("/governance/policy/evaluate", json={"run_config": run_config, "mode": mode})

    def test_allow_demo_tools_within_budget(self):
        r = self._eval({"tools": ["portfolio_analysis", "var_calculation"], "tool_calls_requested": 5})
        assert r.status_code == 200
        assert r.json()["decision"] == "allow"

    def test_block_unknown_tool(self):
        r = self._eval({"tools": ["azure_devops"], "tool_calls_requested": 1})
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "block"
        codes = [rs["code"] for rs in data["reasons"]]
        assert "TOOL_NOT_ALLOWED" in codes

    def test_block_budget_exceeded(self):
        r = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 999})
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "block"
        codes = [rs["code"] for rs in data["reasons"]]
        assert "TOOL_BUDGET_EXCEEDED" in codes

    def test_allow_empty_tools(self):
        r = self._eval({"tools": [], "tool_calls_requested": 0})
        assert r.status_code == 200
        assert r.json()["decision"] == "allow"

    def test_block_response_too_large(self):
        r = self._eval({"tools": [], "tool_calls_requested": 0, "response_bytes": 9999999})
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "block"
        codes = [rs["code"] for rs in data["reasons"]]
        assert "RESPONSE_TOO_LARGE" in codes

    def test_block_secret_in_prompt(self):
        r = self._eval({
            "tools": ["portfolio_analysis"],
            "tool_calls_requested": 1,
            "prompt": "Use api_key=sk-ABCD1234567890abcdef1234567890abcdef1234 for auth.",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["decision"] == "block"
        codes = [rs["code"] for rs in data["reasons"]]
        assert "SECRET_IN_PROMPT" in codes

    def test_policy_hash_stable(self):
        r1 = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 1})
        r2 = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 2})
        # Same mode -> same policy_hash (policy_hash is about mode/allowed_tools/limits, not config)
        assert r1.json()["policy_hash"] == r2.json()["policy_hash"]

    def test_policy_returns_allowed_tools(self):
        r = self._eval({"tools": [], "tool_calls_requested": 0})
        data = r.json()
        assert "allowed_tools" in data
        assert "portfolio_analysis" in data["allowed_tools"]

    def test_mode_local_has_larger_budget(self):
        r = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 25}, mode="LOCAL")
        assert r.json()["decision"] == "allow"
        r2 = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 25}, mode="DEMO")
        # DEMO max is 20, so 25 should block
        assert r2.json()["decision"] == "block"

    def test_unknown_mode_defaults_to_demo(self):
        r = self._eval({"tools": ["portfolio_analysis"], "tool_calls_requested": 5}, mode="INVALID")
        assert r.status_code == 200
        assert r.json()["mode"] == "DEMO"


# ── POST /governance/policy/apply ────────────────────────────────────────────

class TestPolicyApply:
    def _apply(self, run_config: dict, mode: str = "DEMO"):
        return client.post("/governance/policy/apply", json={"run_config": run_config, "mode": mode})

    def test_apply_redacts_secret_in_prompt(self):
        r = self._apply({
            "tools": ["portfolio_analysis"],
            "tool_calls_requested": 1,
            "prompt": "api_key=sk-ABCD1234567890abcdef1234567890abcdef1234",
        })
        assert r.status_code == 200
        data = r.json()
        assert "[REDACTED]" in data["sanitized_config"]["prompt"]

    def test_apply_clips_tool_calls(self):
        r = self._apply({"tools": ["portfolio_analysis"], "tool_calls_requested": 999})
        assert r.status_code == 200
        data = r.json()
        assert data["sanitized_config"]["tool_calls_requested"] == 20  # DEMO max

    def test_apply_removes_disallowed_tools(self):
        r = self._apply({"tools": ["portfolio_analysis", "azure_devops"], "tool_calls_requested": 1})
        assert r.status_code == 200
        data = r.json()
        assert "azure_devops" not in data["sanitized_config"]["tools"]
        assert "portfolio_analysis" in data["sanitized_config"]["tools"]

    def test_apply_clean_config_no_changes(self):
        r = self._apply({"tools": ["portfolio_analysis"], "tool_calls_requested": 5})
        assert r.status_code == 200
        data = r.json()
        assert data["applied_changes"] == []


# ── POST /governance/narrative/validate ──────────────────────────────────────

class TestNarrativeValidate:
    def _validate(self, narrative: str, computed: dict, tolerance: float = 0.01):
        return client.post("/governance/narrative/validate", json={
            "narrative": narrative,
            "computed_results": computed,
            "tolerance": tolerance,
        })

    def test_valid_narrative_known_number(self):
        r = self._validate("The portfolio value is 18250.75 USD.", {"portfolio_value": 18250.75})
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_invalid_narrative_unknown_number(self):
        r = self._validate("The portfolio value is 99999.99 USD.", {"portfolio_value": 18250.75})
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is False
        assert len(data["unknown_numbers"]) > 0

    def test_valid_within_tolerance(self):
        # 18250.00 is within 1% of 18250.75
        r = self._validate("Approx value: 18250.00", {"portfolio_value": 18250.75}, tolerance=0.01)
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_small_integers_exempt(self):
        r = self._validate("The fund has 5 positions and 3 bonds.", {"asset_count": 5})
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_remediation_present_when_invalid(self):
        r = self._validate("VaR is 12345.99", {"var_95": 0.0})
        data = r.json()
        assert data["valid"] is False
        assert data["remediation"] is not None
        assert "12345.99" in data["remediation"]

    def test_empty_narrative_always_valid(self):
        r = self._validate("No numbers here.", {"portfolio_value": 100.0})
        assert r.status_code == 200
        assert r.json()["valid"] is True


# ── Redaction determinism ─────────────────────────────────────────────────────

class TestRedactionDeterminism:
    def test_redaction_idempotent(self):
        from policy_engine import redact_secrets
        text = "api_key=sk-ABCD1234567890abcdef1234567890abcdef1234 call me"
        r1, _ = redact_secrets(text)
        r2, _ = redact_secrets(text)
        assert r1 == r2

    def test_redaction_removes_secret(self):
        from policy_engine import redact_secrets
        text = "password=SuperSecret123!"
        redacted, reasons = redact_secrets(text)
        assert "SuperSecret123!" not in redacted
        assert "[REDACTED]" in redacted

    def test_redaction_preserves_non_secret(self):
        from policy_engine import redact_secrets
        text = "Hello world, no secrets here."
        redacted, reasons = redact_secrets(text)
        assert redacted == text
        assert reasons == []
