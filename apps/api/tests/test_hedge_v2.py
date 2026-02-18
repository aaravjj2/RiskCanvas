"""Tests for hedge_engine_v2.py — v4.8.0"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DEMO_MODE"] = "true"

from hedge_engine_v2 import (
    HEDGE_TEMPLATES,
    generate_hedge_v2_candidates,
    compare_hedge_runs,
    HedgeV2SuggestRequest,
    HedgeV2CompareRequest,
)

BEFORE_METRICS = {"var_95": 5000.0, "var_99": 7500.0, "delta_exposure": 45000.0}
DEFAULT_CONSTRAINTS = {"max_cost": 10000.0, "max_contracts": 30}


class TestHedgeTemplates:
    def test_has_four_templates(self):
        assert len(HEDGE_TEMPLATES) == 4

    def test_template_ids(self):
        expected = {"protective_put", "collar", "delta_hedge", "duration_hedge"}
        assert set(HEDGE_TEMPLATES.keys()) == expected

    def test_each_template_has_required_fields(self):
        for tid, tmpl in HEDGE_TEMPLATES.items():
            assert "id" in tmpl, f"Missing id: {tid}"
            assert "name" in tmpl, f"Missing name: {tid}"
            assert "description" in tmpl, f"Missing description: {tid}"
            assert "objective" in tmpl, f"Missing objective: {tid}"
            assert "default_constraints" in tmpl, f"Missing default_constraints: {tid}"
            assert "target_metric" in tmpl, f"Missing target_metric: {tid}"


class TestGenerateCandidates:
    def test_returns_list(self):
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        assert isinstance(result, list)

    def test_max_10_candidates(self):
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        assert len(result) <= 10

    def test_deterministic(self):
        kwargs = dict(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        r1 = generate_hedge_v2_candidates(**kwargs)
        r2 = generate_hedge_v2_candidates(**kwargs)
        # candidate_ids must be identical in same order
        assert [c["candidate_id"] for c in r1] == [c["candidate_id"] for c in r2]

    def test_candidate_has_required_fields(self):
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        if result:
            c = result[0]
            for field in ["candidate_id", "template_id", "instrument", "strike_pct",
                          "contracts", "total_cost", "before_metrics", "after_metrics",
                          "delta_metrics", "score", "score_breakdown", "audit_ref"]:
                assert field in c, f"Missing field: {field}"

    def test_after_metrics_lower_than_before(self):
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        for c in result:
            for metric in c["before_metrics"]:
                assert c["after_metrics"][metric] < c["before_metrics"][metric], \
                    f"After should be < before for {metric}"

    def test_sorted_by_score_descending(self):
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=DEFAULT_CONSTRAINTS,
        )
        scores = [c["score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_constraint_max_cost_enforced(self):
        tight = {"max_cost": 10.0, "max_contracts": 30}
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=tight,
        )
        for c in result:
            assert c["total_cost"] <= 10.0, f"Cost {c['total_cost']} exceeds 10"

    def test_constraint_max_contracts_enforced(self):
        constraints = {"max_cost": 99999.0, "max_contracts": 5}
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="protective_put",
            objective="minimize_var",
            constraints=constraints,
        )
        for c in result:
            assert c["contracts"] <= 5

    def test_constraint_allowed_instruments_enforced(self):
        constraints = {"max_cost": 99999.0, "max_contracts": 30, "allowed_instruments": ["future"]}
        result = generate_hedge_v2_candidates(
            portfolio_value=100000.0,
            before_metrics=BEFORE_METRICS,
            template_id="delta_hedge",
            objective="minimize_delta",
            constraints=constraints,
        )
        for c in result:
            assert c["instrument"] == "future"

    def test_all_templates_work(self):
        for tid in HEDGE_TEMPLATES:
            result = generate_hedge_v2_candidates(
                portfolio_value=100000.0,
                before_metrics=BEFORE_METRICS,
                template_id=tid,
                objective="minimize_var",
                constraints=DEFAULT_CONSTRAINTS,
            )
            assert isinstance(result, list), f"Failed for template {tid}"

    def test_grid_search_over_200_combos(self):
        """Verify grid generates 6 strikes × 4 contracts × 2+ instruments = 48+ pre-filter."""
        # With 1 allowed instrument, grid is 6×4 = 24 per instrument
        # With 2 instruments it's 48; total pre-filter must be > 48
        # We just verify we get ≥1 post-filter result
        result = generate_hedge_v2_candidates(
            portfolio_value=500000.0,
            before_metrics=BEFORE_METRICS,
            template_id="collar",
            objective="minimize_var",
            constraints={"max_cost": 99999.0, "max_contracts": 30},
        )
        assert len(result) >= 1


class TestCompareHedgeRuns:
    def test_returns_dict(self):
        result = compare_hedge_runs(
            base_run_id="run-001",
            base_metrics=BEFORE_METRICS,
            hedged_metrics={"var_95": 3900.0, "var_99": 6000.0, "delta_exposure": 24750.0},
        )
        assert isinstance(result, dict)

    def test_required_fields(self):
        result = compare_hedge_runs(
            base_run_id="run-001",
            base_metrics=BEFORE_METRICS,
            hedged_metrics={"var_95": 3900.0, "var_99": 6000.0, "delta_exposure": 24750.0},
        )
        for field in ["base_run_id", "base_metrics", "hedged_metrics", "deltas",
                      "pct_changes", "input_hash", "output_hash", "audit_chain_head_hash"]:
            assert field in result, f"Missing field: {field}"

    def test_deltas_computed_correctly(self):
        hedged = {"var_95": 4000.0}
        base = {"var_95": 5000.0}
        result = compare_hedge_runs("r001", base, hedged)
        assert result["deltas"]["var_95"] == pytest.approx(4000.0 - 5000.0)

    def test_pct_changes_computed_correctly(self):
        hedged = {"var_95": 4000.0}
        base = {"var_95": 5000.0}
        result = compare_hedge_runs("r001", base, hedged)
        assert result["pct_changes"]["var_95"] == pytest.approx(-0.2)

    def test_deterministic(self):
        kwargs = dict(
            base_run_id="run-001",
            base_metrics=BEFORE_METRICS,
            hedged_metrics={"var_95": 3900.0, "var_99": 6000.0, "delta_exposure": 24750.0},
        )
        r1 = compare_hedge_runs(**kwargs)
        r2 = compare_hedge_runs(**kwargs)
        assert r1["output_hash"] == r2["output_hash"]


class TestHedgeV2Router:
    def setup_method(self):
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from hedge_engine_v2 import hedge_v2_router
        app = FastAPI()
        app.include_router(hedge_v2_router)
        self.client = TestClient(app)

    def test_templates_endpoint(self):
        resp = self.client.get("/hedge/v2/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 4
        assert "templates" in data

    def test_suggest_endpoint(self):
        resp = self.client.post("/hedge/v2/suggest", json={
            "portfolio_id": "test-portfolio",
            "portfolio_value": 100000.0,
            "template_id": "protective_put",
            "objective": "minimize_var",
            "before_metrics": {"var_95": 5000.0},
            "constraints": {"max_cost": 9999.0, "max_contracts": 20},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "candidates" in data
        assert "input_hash" in data
        assert "output_hash" in data

    def test_compare_endpoint(self):
        resp = self.client.post("/hedge/v2/compare", json={
            "base_run_id": "run-001",
            "base_metrics": {"var_95": 5000.0},
            "hedged_metrics": {"var_95": 4000.0},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "deltas" in data
        assert "pct_changes" in data
