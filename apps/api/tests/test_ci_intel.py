"""Tests for Wave 24: CI Intelligence v2 (v4.46–v4.47)"""
import pytest
from ci_intel import (
    list_pipelines, analyze_pipeline, generate_ci_template,
    _FIXTURE_PIPELINES, _TEMPLATE_FEATURES, FAILURE_CATEGORIES,
)


# ─────────────────── Pipeline List ───────────────────────────────────────────


def test_list_pipelines():
    r = list_pipelines()
    assert "pipelines" in r
    assert r["total"] == len(r["pipelines"])
    assert r["total"] >= 5


def test_list_pipelines_determinism():
    r1 = list_pipelines()
    r2 = list_pipelines()
    assert r1["pipelines"] == r2["pipelines"]


def test_list_pipelines_fields():
    r = list_pipelines()
    for p in r["pipelines"]:
        assert "id" in p
        assert "ref" in p
        assert "status" in p


# ─────────────────── Pipeline Analysis ───────────────────────────────────────


def test_analyze_test_failure():
    r = analyze_pipeline("pipe_001")
    assert r["failure_category"] == "tests"
    assert r["severity"] == "HIGH"
    assert len(r["root_cause_hypotheses"]) > 0
    assert len(r["recommended_actions"]) > 0
    assert "output_hash" in r
    assert "audit_chain_head_hash" in r


def test_analyze_lint_failure():
    r = analyze_pipeline("pipe_002")
    assert r["failure_category"] == "lint"
    assert r["severity"] == "MEDIUM"


def test_analyze_success_pipeline():
    r = analyze_pipeline("pipe_003")
    assert r["status"] == "success"
    assert r["failure_category"] is None
    assert r["severity"] == "NONE"


def test_analyze_build_failure():
    r = analyze_pipeline("pipe_004")
    assert r["failure_category"] == "build"
    assert r["severity"] == "HIGH"


def test_analyze_determinism():
    r1 = analyze_pipeline("pipe_001")
    r2 = analyze_pipeline("pipe_001")
    assert r1["output_hash"] == r2["output_hash"]


def test_analyze_not_found():
    with pytest.raises(ValueError, match="not found"):
        analyze_pipeline("nonexistent_pipe")


def test_failure_categories_complete():
    """All failure categories explicitly tested have runbook entries."""
    from ci_intel import _RUNBOOKS
    for cat in FAILURE_CATEGORIES:
        assert cat in _RUNBOOKS, f"Category '{cat}' missing from runbooks"
        rb = _RUNBOOKS[cat]
        assert len(rb["root_causes"]) > 0
        assert len(rb["recommended_actions"]) > 0


# ─────────────────── Template Generator ──────────────────────────────────────


def test_generate_template_basic():
    r = generate_ci_template(["pytest", "tsc"])
    assert "template" in r
    assert "pytest-backend:" in r["template"]
    assert "typescript-check:" in r["template"]
    assert "stages:" in r["template"]
    assert "template_hash" in r
    assert "audit_chain_head_hash" in r


def test_generate_template_determinism():
    features = ["pytest", "vite_build", "playwright", "lint"]
    r1 = generate_ci_template(features)
    r2 = generate_ci_template(features)
    assert r1["template_hash"] == r2["template_hash"]
    assert r1["template"] == r2["template"]


def test_generate_template_order_independent():
    """Feature order should yield same template (sorted internally)."""
    r1 = generate_ci_template(["pytest", "tsc", "vite_build"])
    r2 = generate_ci_template(["vite_build", "pytest", "tsc"])
    assert r1["template_hash"] == r2["template_hash"]


def test_generate_template_stages_correct():
    r = generate_ci_template(["pytest", "vite_build"])
    assert "test" in r["stages"]
    assert "build" in r["stages"]


def test_generate_template_dedup_features():
    """Duplicate features should be deduplicated."""
    r1 = generate_ci_template(["pytest", "pytest", "tsc"])
    r2 = generate_ci_template(["pytest", "tsc"])
    assert r1["template_hash"] == r2["template_hash"]


def test_generate_template_unknown_feature():
    with pytest.raises(ValueError, match="Unknown features"):
        generate_ci_template(["nonexistent_feature"])


def test_generate_template_full_suite():
    all_features = list(_TEMPLATE_FEATURES.keys())
    r = generate_ci_template(all_features)
    assert r["template"]
    assert r["features_selected"] == sorted(all_features)


def test_generate_template_contains_header():
    r = generate_ci_template(["pytest"])
    assert "RiskCanvas CI Template" in r["template"]
    assert "auto-generated" in r["template"]


def test_generate_template_security_job():
    r = generate_ci_template(["security"])
    assert "secret-scan:" in r["template"]
    assert "security" in r["stages"]


def test_generate_template_hash_changes_with_features():
    r1 = generate_ci_template(["pytest"])
    r2 = generate_ci_template(["pytest", "tsc"])
    assert r1["template_hash"] != r2["template_hash"]
