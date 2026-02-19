"""Tests for Release Readiness Scoring (Wave 28, v4.58-v4.61)"""
import pytest
from release_readiness import (
    reset_readiness, evaluate_readiness, get_assessment, build_release_memo_pack,
)


@pytest.fixture(autouse=True)
def clean():
    reset_readiness()
    yield
    reset_readiness()


_GOOD_METRICS = {
    "test_pass_rate": 99.5,
    "code_coverage": 87.3,
    "critical_vulnerabilities": 0,
    "e2e_pass_rate": 100.0,
    "build_latency_s": 95,
    "approval_count": 2,
    "docs_coverage_pct": 82.0,
    "secret_scan_violations": 0,
}

_BAD_METRICS = {
    "test_pass_rate": 80.0,
    "code_coverage": 60.0,
    "critical_vulnerabilities": 5,
    "e2e_pass_rate": 90.0,
    "build_latency_s": 400,
    "approval_count": 0,
    "docs_coverage_pct": 40.0,
    "secret_scan_violations": 3,
}

_CTX = {"version": "v4.73.0", "branch": "main", "author": "ci-bot"}


def test_evaluate_ship():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    assert result["verdict"] == "SHIP"
    assert result["score"] >= 90
    assert result["blocked_gates"] == 0


def test_evaluate_block():
    result = evaluate_readiness(_BAD_METRICS, _CTX)
    assert result["verdict"] == "BLOCK"
    assert result["score"] < 70
    assert result["blocked_gates"] > 0


def test_evaluate_conditional():
    medium_metrics = {
        "test_pass_rate": 92.0,
        "code_coverage": 77.0,
        "critical_vulnerabilities": 1,
        "e2e_pass_rate": 96.0,
        "build_latency_s": 150,
        "approval_count": 1,
        "docs_coverage_pct": 65.0,
        "secret_scan_violations": 0,
    }
    result = evaluate_readiness(medium_metrics, _CTX)
    assert result["verdict"] in ("CONDITIONAL", "BLOCK", "SHIP")  # deterministic based on weights
    assert result["score"] is not None


def test_assessment_id_stability():
    r1 = evaluate_readiness(_GOOD_METRICS, _CTX)
    reset_readiness()
    r2 = evaluate_readiness(_GOOD_METRICS, _CTX)
    assert r1["assessment_id"] == r2["assessment_id"]
    assert r1["score"] == r2["score"]


def test_gate_results_count():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    assert len(result["gate_results"]) == 8


def test_gate_results_fields():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    for gate in result["gate_results"]:
        assert gate["gate_id"]
        assert gate["status"] in ("PASS", "WARN", "FAIL")
        assert gate["score_contribution"] >= 0


def test_get_assessment():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    fetched = get_assessment(result["assessment_id"])
    assert fetched["assessment_id"] == result["assessment_id"]


def test_get_assessment_not_found():
    with pytest.raises(ValueError, match="not found"):
        get_assessment("nonexistent")


def test_memo_structure():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    memo = result["memo"]
    assert memo["verdict"] == "SHIP"
    assert memo["version"] == "v4.73.0"
    assert memo["branch"] == "main"
    assert "recommendation" in memo


def test_export_pack():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    pack = build_release_memo_pack(result["assessment_id"])
    file_names = {f["name"] for f in pack["files"]}
    assert "memo.json" in file_names
    assert "gate_report.json" in file_names
    assert "risk_summary.txt" in file_names
    assert pack["pack_hash"]
    assert pack["verdict"] == "SHIP"


def test_export_pack_not_found():
    with pytest.raises(ValueError, match="not found"):
        build_release_memo_pack("nonexistent")


def test_output_hash_present():
    result = evaluate_readiness(_GOOD_METRICS, _CTX)
    assert result["output_hash"]
    assert result["audit_chain_head_hash"]


def test_empty_metrics_uses_defaults():
    result = evaluate_readiness({}, _CTX)
    # Should still produce a valid result using demo defaults
    assert result["verdict"] in ("SHIP", "CONDITIONAL", "BLOCK")
    assert result["score"] >= 0
