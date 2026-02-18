"""
Tests for Eval Harness v2 (v3.8+)

Covers:
- Suite discovery (3 built-in suites)
- Deterministic run_id
- Scorecard md/json stability
- Suite pass-rate
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


# ── GET /governance/evals/suites ─────────────────────────────────────────────

class TestListSuites:
    def test_returns_three_builtin_suites(self):
        r = client.get("/governance/evals/suites")
        assert r.status_code == 200
        data = r.json()
        assert len(data["suites"]) >= 3

    def test_suite_ids_present(self):
        r = client.get("/governance/evals/suites")
        ids = [s["suite_id"] for s in r.json()["suites"]]
        assert "governance_policy_suite" in ids
        assert "rates_curve_suite" in ids
        assert "stress_library_suite" in ids

    def test_suite_list_sorted(self):
        r = client.get("/governance/evals/suites")
        ids = [s["suite_id"] for s in r.json()["suites"]]
        assert ids == sorted(ids)

    def test_suite_has_case_count(self):
        r = client.get("/governance/evals/suites")
        gov = next(s for s in r.json()["suites"] if s["suite_id"] == "governance_policy_suite")
        assert gov["case_count"] >= 5


# ── POST /governance/evals/run-suite ─────────────────────────────────────────

class TestRunSuite:
    def _run(self, suite_id: str):
        return client.post("/governance/evals/run-suite", json={"suite_id": suite_id})

    def test_governance_suite_runs(self):
        r = self._run("governance_policy_suite")
        assert r.status_code == 200
        data = r.json()
        assert "run_id" in data
        assert data["suite_id"] == "governance_policy_suite"
        assert data["pass_rate"]  # non-empty string like "100.0%"

    def test_rates_curve_suite_runs(self):
        r = self._run("rates_curve_suite")
        assert r.status_code == 200
        assert r.json()["suite_id"] == "rates_curve_suite"

    def test_stress_library_suite_runs(self):
        r = self._run("stress_library_suite")
        assert r.status_code == 200
        assert r.json()["suite_id"] == "stress_library_suite"

    def test_run_id_deterministic(self):
        r1 = self._run("governance_policy_suite")
        r2 = self._run("governance_policy_suite")
        assert r1.json()["run_id"] == r2.json()["run_id"]

    def test_run_id_is_hex_string_32_chars(self):
        r = self._run("governance_policy_suite")
        run_id = r.json()["run_id"]
        assert len(run_id) == 32
        assert all(c in "0123456789abcdef" for c in run_id)

    def test_unknown_suite_returns_404(self):
        r = self._run("does_not_exist")
        assert r.status_code == 404

    def test_cases_present_in_result(self):
        r = self._run("governance_policy_suite")
        data = r.json()
        assert "cases" in data
        assert len(data["cases"]) >= 5

    def test_all_cases_have_passed_field(self):
        r = self._run("governance_policy_suite")
        for case in r.json()["cases"]:
            assert "passed" in case
            assert isinstance(case["passed"], bool)


# ── GET /governance/evals/results/{run_id} ───────────────────────────────────

class TestGetEvalResult:
    def _run_and_get_id(self, suite_id="governance_policy_suite"):
        r = client.post("/governance/evals/run-suite", json={"suite_id": suite_id})
        return r.json()["run_id"]

    def test_get_result_by_run_id(self):
        run_id = self._run_and_get_id()
        r = client.get(f"/governance/evals/results/{run_id}")
        assert r.status_code == 200
        assert r.json()["run_id"] == run_id

    def test_unknown_run_id_404(self):
        r = client.get("/governance/evals/results/deadbeefdeadbeefdeadbeefdeadbeef")
        assert r.status_code == 404


# ── Scorecard md + json ───────────────────────────────────────────────────────

class TestScorecardExport:
    def _run_and_get_id(self):
        r = client.post("/governance/evals/run-suite", json={"suite_id": "governance_policy_suite"})
        return r.json()["run_id"]

    def test_scorecard_md_contains_table(self):
        run_id = self._run_and_get_id()
        r = client.get(f"/governance/evals/scorecard/{run_id}/md")
        assert r.status_code == 200
        text = r.text  # PlainTextResponse
        assert "|" in text  # markdown table

    def test_scorecard_md_stable(self):
        run_id = self._run_and_get_id()
        r1 = client.get(f"/governance/evals/scorecard/{run_id}/md")
        r2 = client.get(f"/governance/evals/scorecard/{run_id}/md")
        assert r1.text == r2.text

    def test_scorecard_json_has_hash(self):
        run_id = self._run_and_get_id()
        r = client.get(f"/governance/evals/scorecard/{run_id}/json")
        assert r.status_code == 200
        data = r.json()
        assert "scorecard_hash" in data

    def test_scorecard_json_hash_stable(self):
        run_id = self._run_and_get_id()
        r1 = client.get(f"/governance/evals/scorecard/{run_id}/json")
        r2 = client.get(f"/governance/evals/scorecard/{run_id}/json")
        assert r1.json()["scorecard_hash"] == r2.json()["scorecard_hash"]
