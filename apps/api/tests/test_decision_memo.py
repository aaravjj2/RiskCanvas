"""Tests for decision_memo.py — v4.9.0"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DEMO_MODE"] = "true"

from decision_memo import DecisionMemoBuilder, DecisionMemoRequest


SAMPLE_HEDGE_RESULT = {
    "portfolio_id": "test-portfolio",
    "template_id": "protective_put",
    "objective": "minimize_var",
    "input_hash": "abc123",
    "output_hash": "def456",
    "candidates": [
        {
            "candidate_id": "cand001aabbccdd",
            "template_id": "protective_put",
            "instrument": "put",
            "strike_pct": 0.95,
            "contracts": 10,
            "total_cost": 500.0,
            "before_metrics": {"var_95": 5000.0},
            "after_metrics": {"var_95": 3900.0},
            "delta_metrics": {"var_95": 1100.0},
            "score": 0.00154,
            "score_breakdown": {"improvement_score": 1100.0, "cost_efficiency": 2.2},
            "audit_ref": "hedge_v2_cand001a",
        }
    ],
}

SAMPLE_COMPARE = {
    "base_run_id": "run-001",
    "base_metrics": {"var_95": 5000.0, "var_99": 7500.0},
    "hedged_metrics": {"var_95": 3900.0, "var_99": 6000.0},
    "deltas": {"var_95": -1100.0, "var_99": -1500.0},
    "pct_changes": {"var_95": -0.22, "var_99": -0.20},
    "input_hash": "inp789",
    "output_hash": "out012",
    "audit_chain_head_hash": "abcdef01",
}


class TestDecisionMemoBuilder:
    def setup_method(self):
        self.builder = DecisionMemoBuilder()

    def test_returns_three_keys(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={"extra_hash": "xyz"},
        )
        assert "memo_md" in result
        assert "memo_json" in result
        assert "memo_hash" in result

    def test_memo_hash_deterministic(self):
        r1 = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        r2 = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert r1["memo_hash"] == r2["memo_hash"]

    def test_memo_json_has_required_fields(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        mj = result["memo_json"]
        for field in ["version", "asof", "portfolio_id", "template_id", "objective",
                      "best_candidate", "before_metrics", "after_metrics",
                      "delta_metrics", "pct_changes", "provenance", "memo_hash"]:
            assert field in mj, f"Missing field: {field}"

    def test_memo_md_is_string(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert isinstance(result["memo_md"], str)
        assert len(result["memo_md"]) > 100

    def test_memo_md_contains_portfolio_id(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert "test-portfolio" in result["memo_md"]

    def test_memo_md_contains_template_id(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert "protective_put" in result["memo_md"]

    def test_memo_md_contains_metrics_table(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert "Before vs After" in result["memo_md"]
        assert "var_95" in result["memo_md"]

    def test_memo_md_contains_provenance_section(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={"extra_key": "val1"},
        )
        assert "Provenance" in result["memo_md"]
        assert "extra_key" in result["memo_md"]

    def test_memo_json_numbers_from_data(self):
        """Verify memo_json numbers come from compare_deltas — no invented values."""
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        mj = result["memo_json"]
        assert mj["before_metrics"]["var_95"] == 5000.0
        assert mj["after_metrics"]["var_95"] == 3900.0
        assert mj["delta_metrics"]["var_95"] == -1100.0
        assert mj["pct_changes"]["var_95"] == -0.22

    def test_analyst_notes_included(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
            analyst_notes="Approved by risk committee.",
        )
        assert "Approved by risk committee." in result["memo_md"]
        assert result["memo_json"]["analyst_notes"] == "Approved by risk committee."

    def test_version_is_correct(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        assert result["memo_json"]["version"] == "v4.9.0"

    def test_asof_is_demo_value(self):
        result = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        # In DEMO_MODE, asof must equal DEMO_ASOF constant
        assert result["memo_json"]["asof"] == "2026-01-15T16:00:00"

    def test_memo_hash_changes_on_different_input(self):
        r1 = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=SAMPLE_COMPARE,
            provenance_hashes={},
        )
        modified = dict(SAMPLE_COMPARE, pct_changes={"var_95": -0.99, "var_99": -0.20})
        r2 = self.builder.build(
            hedge_result=SAMPLE_HEDGE_RESULT,
            compare_deltas=modified,
            provenance_hashes={},
        )
        assert r1["memo_hash"] != r2["memo_hash"]


class TestDecisionMemoRouter:
    def setup_method(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from decision_memo import decision_memo_router, exports_router
        app = FastAPI()
        app.include_router(decision_memo_router)
        app.include_router(exports_router)
        self.client = TestClient(app)

    def test_memo_endpoint(self):
        resp = self.client.post("/hedge/v2/memo", json={
            "hedge_result": SAMPLE_HEDGE_RESULT,
            "compare_deltas": SAMPLE_COMPARE,
            "provenance_hashes": {},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "memo_md" in data
        assert "memo_hash" in data

    def test_export_pack_endpoint(self):
        resp = self.client.post("/exports/hedge-decision-pack", json={
            "memo_request": {
                "hedge_result": SAMPLE_HEDGE_RESULT,
                "compare_deltas": SAMPLE_COMPARE,
                "provenance_hashes": {},
            },
            "include_candidates": True,
            "include_compare": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "memo_hash" in data
        assert "memo_md" in data
        assert "pack_hash" in data
        assert "candidates" in data
        assert "compare_deltas" in data

    def test_export_pack_without_extras(self):
        resp = self.client.post("/exports/hedge-decision-pack", json={
            "memo_request": {
                "hedge_result": {},
                "compare_deltas": {},
                "provenance_hashes": {},
            },
            "include_candidates": False,
            "include_compare": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "candidates" not in data
        assert "compare_deltas" not in data
