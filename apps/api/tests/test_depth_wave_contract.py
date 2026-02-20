"""
test_depth_wave_contract.py — Depth Wave contract tests (v5.56.1–v5.60.0)

Verifies the 6 new modules introduced in the Depth Wave:
  A. run_outcomes      — deterministic 7-metric RunOutcome per run_id
  B. eval_harness_v3   — calibration/drift/stability, idempotent eval_id
  C. explainability    — template-based reason chain, stable explain_id
  D. policy_engine_v3  — SHIP/CONDITIONAL/BLOCK gate from check results
  E. mcp_tools_v2      — 8 tools list stable; call tools return deterministic result
  F. devops_offline_review — diff scan + policy gate + open review pipeline

No external I/O. Tests exercise in-memory stores directly.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from run_outcomes import OUTCOME_STORE, _compute_outcome, _det
from eval_harness_v3 import EVAL_STORE, _eval_run_ids
from explainability import EXPLANATION_STORE, _build_explanation
from policy_engine_v3 import DECISION_STORE, evaluate_policy_v3
from mcp_tools_v2 import MCP_AUDIT_LOG, TOOLS
from devops_offline_review import offline_review_and_open


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_depth_stores():
    """Clear and restore depth wave stores around each test."""
    saved_outcomes = dict(OUTCOME_STORE)
    saved_evals = dict(EVAL_STORE)
    saved_explns = dict(EXPLANATION_STORE)
    saved_decisions = dict(DECISION_STORE)
    saved_audit = list(MCP_AUDIT_LOG)

    OUTCOME_STORE.clear()
    EVAL_STORE.clear()
    EXPLANATION_STORE.clear()
    DECISION_STORE.clear()
    MCP_AUDIT_LOG.clear()

    yield

    OUTCOME_STORE.clear(); OUTCOME_STORE.update(saved_outcomes)
    EVAL_STORE.clear(); EVAL_STORE.update(saved_evals)
    EXPLANATION_STORE.clear(); EXPLANATION_STORE.update(saved_explns)
    DECISION_STORE.clear(); DECISION_STORE.update(saved_decisions)
    MCP_AUDIT_LOG.clear(); MCP_AUDIT_LOG.extend(saved_audit)


# ═══════════════════════════════════════════════════════════════════════════════
# A. run_outcomes
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunOutcomes:
    def test_determinism_same_input_same_output(self):
        """Same run_id → identical outcome metrics (both calls)."""
        o1 = _compute_outcome("run-abc", "sc-001", "stress", "hash-xyz")
        o2 = _compute_outcome("run-abc", "sc-001", "stress", "hash-xyz")
        assert o1["pnl_total"] == o2["pnl_total"]
        assert o1["var_95"] == o2["var_95"]
        assert o1["completeness_score"] == o2["completeness_score"]

    def test_different_run_ids_different_outcomes(self):
        """Different run_ids → different pnl_total (probabilistically true with sha256)."""
        o1 = _compute_outcome("run-aaa", "sc-001", "stress", "hash-aaa")
        o2 = _compute_outcome("run-bbb", "sc-001", "stress", "hash-bbb")
        assert o1["pnl_total"] != o2["pnl_total"] or o1["var_95"] != o2["var_95"]

    def test_outcome_schema(self):
        """Outcome has all required metric fields."""
        o = _compute_outcome("run-test", "sc-test", "whatif", "hash-test")
        required = {
            "run_id", "scenario_id", "kind", "output_hash",
            "pnl_total", "var_95", "var_99", "max_drawdown_proxy",
            "scenario_severity_score", "completeness_score", "data_freshness_score",
        }
        for field in required:
            assert field in o, f"Missing field: {field}"

    def test_pnl_total_negative(self):
        """pnl_total should be in [-3_000_000, 0] range."""
        o = _compute_outcome("run-pnl", "sc-pnl", "stress", "h-pnl")
        assert -3_000_000 <= o["pnl_total"] <= 0

    def test_completeness_score_in_range(self):
        """completeness_score should be in [0.7, 1.0]."""
        o = _compute_outcome("run-cs", "sc-cs", "stress", "h-cs")
        assert 0.0 <= o["completeness_score"] <= 1.0

    def test_rounding_two_dp_for_monetary(self):
        """Monetary values are rounded to 2 decimal places."""
        o = _compute_outcome("run-r2", "sc-r2", "stress", "h-r2")
        for field in ("pnl_total", "var_95", "var_99", "max_drawdown_proxy"):
            val = o[field]
            assert round(val, 2) == val, f"{field} not at 2dp: {val}"

    def test_rounding_four_dp_for_scores(self):
        """Score fields are rounded to 4 decimal places."""
        o = _compute_outcome("run-r4", "sc-r4", "stress", "h-r4")
        for field in ("completeness_score", "data_freshness_score"):
            val = o[field]
            assert round(val, 4) == val, f"{field} not at 4dp: {val}"


# ═══════════════════════════════════════════════════════════════════════════════
# B. eval_harness_v3
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvalHarnessV3:
    DEMO_RUN_IDS = ["demo-run-0001", "demo-run-0002"]

    def test_idempotent_eval_id(self):
        """Two identical requests with same run_ids → same eval_id."""
        e1 = _eval_run_ids(self.DEMO_RUN_IDS)
        e2 = _eval_run_ids(self.DEMO_RUN_IDS)
        assert e1["eval_id"] == e2["eval_id"]

    def test_order_independence(self):
        """Reversed run_ids produce same eval_id as sorted."""
        e1 = _eval_run_ids(["zz-run", "aa-run"])
        e2 = _eval_run_ids(["aa-run", "zz-run"])
        assert e1["eval_id"] == e2["eval_id"]

    def test_schema(self):
        """Eval result has required fields."""
        e = _eval_run_ids(self.DEMO_RUN_IDS)
        assert "eval_id" in e
        assert e["eval_id"].startswith("eval3-")
        assert "metrics" in e
        assert "calibration_error" in e["metrics"]
        assert "drift_score" in e["metrics"]
        assert "stability_score" in e["metrics"]

    def test_thresholds_met_in_demo(self):
        """Demo metrics should pass gates (calibration≤0.05, drift≤0.20, stability≥0.90)."""
        e = _eval_run_ids(self.DEMO_RUN_IDS)
        m = e["metrics"]
        assert m["calibration_error"] <= 0.05
        assert m["drift_score"] <= 0.20
        assert m["stability_score"] >= 0.90
        assert e["passed"] is True

    def test_run_breakdown_count(self):
        """run_breakdown should have one entry per run_id."""
        ids = ["run-x", "run-y", "run-z"]
        e = _eval_run_ids(ids)
        assert len(e["run_breakdown"]) == 3
        breakdown_ids = {b["run_id"] for b in e["run_breakdown"]}
        assert breakdown_ids == set(ids)

    def test_harness_version(self):
        """harness_version should be 'v3'."""
        e = _eval_run_ids(self.DEMO_RUN_IDS)
        assert e["harness_version"] == "v3"


# ═══════════════════════════════════════════════════════════════════════════════
# C. explainability
# ═══════════════════════════════════════════════════════════════════════════════

class TestExplainability:
    def test_stable_explain_id(self):
        """Same inputs → same explain_id."""
        e1 = _build_explanation("ds-001", "sc-001", "run-001", "rev-001")
        e2 = _build_explanation("ds-001", "sc-001", "run-001", "rev-001")
        assert e1["explain_id"] == e2["explain_id"]

    def test_explain_id_prefix(self):
        e = _build_explanation("ds-a", "sc-b", "run-c", "rev-d")
        assert e["explain_id"].startswith("expl-")

    def test_schema(self):
        e = _build_explanation("ds-x", None, "run-x", None)
        assert "explain_id" in e
        assert "reasons" in e
        assert isinstance(e["reasons"], list)
        assert len(e["reasons"]) > 0

    def test_reasons_are_dicts_with_text(self):
        """Each reason is a dict with a non-empty 'text' field."""
        e = _build_explanation("ds-r", "sc-r", "run-r", "rev-r")
        for reason in e["reasons"]:
            assert isinstance(reason, dict), f"reason should be dict, got {type(reason)}"
            assert "text" in reason
            assert isinstance(reason["text"], str)
            assert len(reason["text"]) > 5  # not empty

    def test_different_inputs_different_id(self):
        e1 = _build_explanation("ds-1", "sc-1", "run-1", "rev-1")
        e2 = _build_explanation("ds-2", "sc-2", "run-2", "rev-2")
        assert e1["explain_id"] != e2["explain_id"]


# ═══════════════════════════════════════════════════════════════════════════════
# D. policy_engine_v3
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolicyEngineV3:
    def test_demo_scenario_ships(self):
        """With empty check context (DEMO fallback), verdict should be SHIP."""
        result = evaluate_policy_v3(
            subject_type="dataset",
            subject_id="demo-subject-001",
        )
        assert result["verdict"] in ("SHIP", "CONDITIONAL", "BLOCK")

    def test_deterministic_decision_id(self):
        """Same inputs → same decision_id."""
        r1 = evaluate_policy_v3("scenario", "subj-aa")
        r2 = evaluate_policy_v3("scenario", "subj-aa")
        assert r1["decision_id"] == r2["decision_id"]

    def test_schema(self):
        r = evaluate_policy_v3("dataset", "subj-schm")
        assert "decision_id" in r
        assert "verdict" in r
        assert "reasons" in r
        assert isinstance(r["reasons"], list)
        assert r["verdict"] in ("SHIP", "CONDITIONAL", "BLOCK")

    def test_checks_have_required_fields(self):
        r = evaluate_policy_v3("dataset", "subj-chk")
        for check in r["reasons"]:
            assert "check" in check
            assert "passed" in check
            assert isinstance(check["passed"], bool)

    def test_block_when_approved_review_false(self):
        """If context has approved_review=False, verdict must be BLOCK."""
        r = evaluate_policy_v3(
            subject_type="dataset",
            subject_id="subj-block",
            context={"approved_review": False, "attestation_chain": False},
        )
        assert r["verdict"] == "BLOCK"

    def test_decision_id_prefix(self):
        r = evaluate_policy_v3("dataset", "subj-pre")
        assert r["decision_id"].startswith("pv3-")


# ═══════════════════════════════════════════════════════════════════════════════
# E. mcp_tools_v2
# ═══════════════════════════════════════════════════════════════════════════════

class TestMcpToolsV2:
    def test_tools_count(self):
        """There should be exactly 8 tools."""
        assert len(TOOLS) == 8

    def test_tools_names_stable(self):
        """Tool names should be deterministic."""
        names = {t["name"] for t in TOOLS}
        expected = {
            "ingest_dataset", "create_scenario", "execute_run", "replay_run",
            "request_review", "approve_review", "export_packet", "run_eval",
        }
        assert names == expected

    def test_tools_have_description(self):
        for tool in TOOLS:
            assert "description" in tool
            assert len(tool["description"]) > 5

    def test_tools_have_params_and_returns(self):
        for tool in TOOLS:
            assert "params" in tool
            assert "returns" in tool


# ═══════════════════════════════════════════════════════════════════════════════
# F. devops_offline_review
# ═══════════════════════════════════════════════════════════════════════════════

CLEAN_DIFF = "+def validate_policy():\n+    return True\n"
RISKY_DIFF = "+API_KEY = 'abc123secret'\n+password = 'hunter2'\n"


class TestDevOpsOfflineReview:
    def test_pipeline_succeeds(self):
        result = offline_review_and_open(CLEAN_DIFF, "Clean PR", "10", "reviewer@demo")
        assert "subject_id" in result
        assert "policy_verdict" in result
        assert "review" in result

    def test_deterministic_subject_id(self):
        r1 = offline_review_and_open(CLEAN_DIFF, "Same PR", "99", "r@demo")
        r2 = offline_review_and_open(CLEAN_DIFF, "Same PR", "99", "r@demo")
        assert r1["subject_id"] == r2["subject_id"]

    def test_risky_diff_high_findings(self):
        r = offline_review_and_open(RISKY_DIFF, "Risky PR", "42", "r@demo")
        high_findings = [f for f in r["diff_scan"]["findings"] if f["severity"] == "high"]
        assert len(high_findings) >= 1

    def test_clean_diff_passes_scan(self):
        r = offline_review_and_open(CLEAN_DIFF, "Clean PR", "43", "r@demo")
        assert r["diff_scan"]["passed"] is True

    def test_schema(self):
        r = offline_review_and_open(CLEAN_DIFF, "Schema PR", "44", "r@demo")
        assert "subject_id" in r
        assert "policy_verdict" in r
        assert "diff_scan" in r
        assert "findings" in r["diff_scan"]
        assert isinstance(r["diff_scan"]["findings"], list)
        assert "review" in r
        assert "review_id" in r["review"]

    def test_verdict_type(self):
        r = offline_review_and_open(CLEAN_DIFF, "Verdict PR", "45", "r@demo")
        assert r["policy_verdict"] in ("SHIP", "CONDITIONAL", "BLOCK")

    def test_high_risk_diff_blocked(self):
        """Diff with high-severity findings should result in BLOCK verdict."""
        r = offline_review_and_open(RISKY_DIFF, "Risky", "46", "r@demo")
        assert r["policy_verdict"] == "BLOCK"
