"""
Tests for devops_policy.py (v3.1)
"""
import os
import json
import pytest
os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    """Guarantee DEMO_MODE=true for every test in this module."""
    monkeypatch.setenv("DEMO_MODE", "true")


CLEAN_DIFF = """\
+def calculate_var(portfolio, confidence=0.95):
+    returns = portfolio.get_returns()
+    return np.percentile(returns, (1 - confidence) * 100)
"""

DIRTY_DIFF = """\
+def debug_portfolio():
+    console.log("debug start")
+    password = "s3cr3tP@ssw0rd"
+    api_key = "sk-1234567890abcdef"
+    # TODO: fix this later
+    import *
+    except:
+        pass
"""


# ── /devops/policy/evaluate ───────────────────────────────────────────────────

class TestPolicyEvaluate:
    def test_clean_diff_allows(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert r.status_code == 200
        assert r.json()["decision"] == "allow"

    def test_dirty_diff_blocks(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": DIRTY_DIFF})
        assert r.status_code == 200
        assert r.json()["decision"] == "block"

    def test_response_has_run_id(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert "run_id" in r.json()

    def test_run_id_stable_across_calls(self):
        r1 = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        r2 = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert r1.json()["run_id"] == r2.json()["run_id"]

    def test_response_has_score(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert "score" in r.json()
        assert 0 <= r.json()["score"] <= 100

    def test_response_has_reasons(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert "reasons" in r.json()
        assert isinstance(r.json()["reasons"], list)

    def test_response_has_remediation(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert "remediation" in r.json()

    def test_response_has_summary(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert "summary" in r.json()

    def test_dirty_diff_has_blocker_reasons(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": DIRTY_DIFF})
        blockers = [x for x in r.json()["reasons"] if x["severity"] == "blocker"]
        assert len(blockers) >= 1

    def test_score_higher_for_dirty_diff(self):
        r_clean = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        r_dirty = client.post("/devops/policy/evaluate", json={"diff_text": DIRTY_DIFF})
        assert r_dirty.json()["score"] > r_clean.json()["score"]

    def test_timestamp_fixed_in_demo(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": CLEAN_DIFF})
        assert r.json()["timestamp"].startswith("2026-")

    def test_risk_delta_blocker(self):
        r = client.post("/devops/policy/evaluate", json={
            "diff_text": CLEAN_DIFF,
            "risk_delta": 0.35  # 35% > 20% threshold
        })
        assert r.json()["decision"] == "block"

    def test_risk_delta_below_threshold_allows(self):
        r = client.post("/devops/policy/evaluate", json={
            "diff_text": CLEAN_DIFF,
            "risk_delta": 0.10  # 10% < 20% threshold
        })
        assert r.json()["decision"] == "allow"

    def test_coverage_decrease_warning(self):
        r = client.post("/devops/policy/evaluate", json={
            "diff_text": CLEAN_DIFF,
            "coverage_delta": -0.10  # -10% drop
        })
        warnings = [x for x in r.json()["reasons"] if x["severity"] == "warning"]
        assert any(x["code"] == "coverage_decrease" for x in warnings)

    def test_missing_diff_text_returns_422(self):
        r = client.post("/devops/policy/evaluate", json={})
        assert r.status_code == 422

    def test_empty_diff_allows(self):
        r = client.post("/devops/policy/evaluate", json={"diff_text": ""})
        assert r.status_code == 200
        assert r.json()["decision"] == "allow"


# ── /devops/policy/export ─────────────────────────────────────────────────────

class TestPolicyExport:
    def test_export_returns_200(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        assert r.status_code == 200

    def test_export_has_mr_comment_markdown(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        assert "mr_comment_markdown" in r.json()

    def test_export_has_reliability_report(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        assert "reliability_report_markdown" in r.json()

    def test_export_has_policy_decision_json(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        assert "policy_decision_json" in r.json()

    def test_export_decision_json_is_valid_json(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        parsed = json.loads(r.json()["policy_decision_json"])
        assert "decision" in parsed

    def test_export_mr_comment_contains_decision_badge(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        md = r.json()["mr_comment_markdown"]
        assert "ALLOWED" in md or "BLOCKED" in md

    def test_export_dirty_diff_mr_comment_shows_blocked(self):
        r = client.post("/devops/policy/export", json={"diff_text": DIRTY_DIFF})
        md = r.json()["mr_comment_markdown"]
        assert "BLOCKED" in md

    def test_export_reliability_report_has_header(self):
        r = client.post("/devops/policy/export", json={"diff_text": CLEAN_DIFF})
        text = r.json()["reliability_report_markdown"]
        assert "Reliability Report" in text


# ── /devops/policy/rules ──────────────────────────────────────────────────────

class TestPolicyRules:
    def test_rules_returns_200(self):
        r = client.get("/devops/policy/rules")
        assert r.status_code == 200

    def test_rules_is_list(self):
        r = client.get("/devops/policy/rules")
        assert isinstance(r.json(), list)

    def test_rules_non_empty(self):
        r = client.get("/devops/policy/rules")
        assert len(r.json()) >= 1

    def test_rules_each_has_code_severity_description(self):
        r = client.get("/devops/policy/rules")
        for rule in r.json():
            assert "code" in rule
            assert "severity" in rule
            assert "description" in rule

    def test_rules_has_blocker_entries(self):
        r = client.get("/devops/policy/rules")
        blockers = [x for x in r.json() if x["severity"] == "blocker"]
        assert len(blockers) >= 1

    def test_rules_has_warning_entries(self):
        r = client.get("/devops/policy/rules")
        warnings = [x for x in r.json() if x["severity"] == "warning"]
        assert len(warnings) >= 1
