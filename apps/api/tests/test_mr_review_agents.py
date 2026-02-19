"""Tests for MR Review Agents (Wave 26, v4.50-v4.53)"""
import pytest
from mr_review_agents import (
    reset_reviews, plan_mr_review, run_mr_review, get_mr_review,
    list_mr_fixtures, generate_comment_preview, post_comments_demo,
    build_mr_review_pack,
)


@pytest.fixture(autouse=True)
def clean():
    reset_reviews()
    yield
    reset_reviews()


def test_list_fixtures():
    fixtures = list_mr_fixtures()
    assert len(fixtures) == 4
    ids = {f["mr_id"] for f in fixtures}
    assert ids == {"MR-101", "MR-102", "MR-103", "MR-104"}


def test_plan_mr_review_basic():
    plan = plan_mr_review("MR-101", {})
    assert plan["mr_id"] == "MR-101"
    assert plan["status"] == "ready"
    assert len(plan["plan_id"]) == 24
    assert "checklist" in plan
    assert "scan_secrets" in plan["checklist"]


def test_plan_missing_mr():
    with pytest.raises(ValueError, match="not found"):
        plan_mr_review("MR-999", {})


def test_run_review_mr101():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    assert review["mr_id"] == "MR-101"
    assert review["verdict"] == "BLOCK"  # AWS key in diff
    assert review["critical_count"] > 0
    assert len(review["findings"]) > 0
    assert review["output_hash"]
    assert review["audit_chain_head_hash"]


def test_run_review_mr103_approve():
    plan = plan_mr_review("MR-103", {})
    review = run_mr_review(plan["plan_id"])
    assert review["mr_id"] == "MR-103"
    assert review["verdict"] == "APPROVE"
    assert review["critical_count"] == 0


def test_run_review_mr104_approve():
    plan = plan_mr_review("MR-104", {})
    review = run_mr_review(plan["plan_id"])
    assert review["mr_id"] == "MR-104"
    assert review["verdict"] == "APPROVE"


def test_run_review_mr102_block():
    plan = plan_mr_review("MR-102", {})
    review = run_mr_review(plan["plan_id"])
    assert review["verdict"] == "BLOCK"
    assert review["critical_count"] > 0


def test_get_review():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    fetched = get_mr_review(review["review_id"])
    assert fetched["review_id"] == review["review_id"]


def test_get_review_not_found():
    with pytest.raises(ValueError, match="not found"):
        get_mr_review("nonexistent_review_id")


def test_run_review_plan_not_found():
    with pytest.raises(ValueError, match="not found"):
        run_mr_review("nonexistent_plan_id")


def test_comment_preview():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    comments = generate_comment_preview(review["review_id"])
    assert len(comments) == len(review["recommendations"])
    for c in comments:
        assert "[RiskCanvas Review Bot]" in c["body"]
        assert c["posted"] is False


def test_comment_preview_no_review():
    with pytest.raises(ValueError):
        generate_comment_preview("nonexistent")


def test_post_comments():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    preview = generate_comment_preview(review["review_id"])
    result = post_comments_demo(review["review_id"], preview)
    assert result["posted_count"] == len(preview)
    assert result["demo_mode"] is True
    assert all(c["posted"] for c in result["comments"])


def test_export_pack():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    pack = build_mr_review_pack(review["review_id"])
    file_names = {f["name"] for f in pack["files"]}
    assert file_names == {"trace.json", "findings.json", "recommendations.json", "diff.txt"}
    assert pack["verdict"] == "BLOCK"
    assert pack["pack_hash"]
    assert pack["output_hash"]


def test_determinism():
    plan1 = plan_mr_review("MR-101", {})
    run1 = run_mr_review(plan1["plan_id"])
    reset_reviews()
    plan2 = plan_mr_review("MR-101", {})
    run2 = run_mr_review(plan2["plan_id"])
    assert plan1["plan_id"] == plan2["plan_id"]
    assert run1["output_hash"] == run2["output_hash"]


def test_trace_structure():
    plan = plan_mr_review("MR-101", {})
    review = run_mr_review(plan["plan_id"])
    trace = review["trace"]
    assert len(trace["steps"]) == 3
    assert trace["tool_calls"] == ["PlannerAgent", "ScannerAgent", "RecommenderAgent"]
    assert trace["inputs_hash"]
    assert trace["outputs_hash"]


def test_all_mr_fixtures_reviewable():
    for mr_id in ["MR-101", "MR-102", "MR-103", "MR-104"]:
        reset_reviews()
        plan = plan_mr_review(mr_id, {})
        review = run_mr_review(plan["plan_id"])
        assert review["verdict"] in ("BLOCK", "REVIEW", "APPROVE")
