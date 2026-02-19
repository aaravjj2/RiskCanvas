"""Tests for Search V2 (Wave 31, v4.70-v4.71)"""
import pytest
from search_v2 import get_index_stats, query_search, SUPPORTED_TYPES


def test_index_stats():
    stats = get_index_stats()
    assert stats["total_docs"] == 16
    assert stats["index_hash"]
    assert "mr_review" in stats["by_type"]
    assert "incident_drill" in stats["by_type"]
    assert "workflow" in stats["by_type"]
    assert "policy_v2" in stats["by_type"]
    assert "pipeline" in stats["by_type"]
    assert "risk_model" in stats["by_type"]


def test_supported_types():
    assert "mr_review" in SUPPORTED_TYPES
    assert "incident_drill" in SUPPORTED_TYPES
    assert "workflow" in SUPPORTED_TYPES
    assert "policy_v2" in SUPPORTED_TYPES
    assert "pipeline" in SUPPORTED_TYPES
    assert "risk_model" in SUPPORTED_TYPES


def test_query_empty_returns_all():
    result = query_search("", page_size=100)
    assert result["total"] == 16
    assert result["result_count"] == 16


def test_query_mr_review():
    result = query_search("MR-101")
    assert result["total"] >= 1
    assert any("MR-101" in r["title"] for r in result["results"])


def test_query_eval():
    result = query_search("eval")
    assert result["total"] >= 1
    doc_titles = [r["title"] for r in result["results"]]
    assert any("MR-102" in t or "eval" in t.lower() for t in doc_titles)


def test_query_type_filter_mr_review():
    result = query_search("", doc_type="mr_review", page_size=100)
    assert result["total"] == 4
    assert all(r["type"] == "mr_review" for r in result["results"])


def test_query_type_filter_pipeline():
    result = query_search("", doc_type="pipeline", page_size=100)
    assert result["total"] == 3
    assert all(r["type"] == "pipeline" for r in result["results"])


def test_query_type_filter_incident_drill():
    result = query_search("", doc_type="incident_drill", page_size=100)
    assert result["total"] == 3
    assert all(r["type"] == "incident_drill" for r in result["results"])


def test_query_type_filter_workflow():
    result = query_search("", doc_type="workflow", page_size=100)
    assert result["total"] == 2


def test_query_latency():
    result = query_search("latency")
    assert result["total"] >= 1
    assert any("latency" in r["title"].lower() or "latency" in r["body"].lower() for r in result["results"])


def test_query_security():
    result = query_search("security")
    assert result["total"] >= 1


def test_pagination():
    result1 = query_search("", page=1, page_size=5)
    result2 = query_search("", page=2, page_size=5)
    assert result1["page"] == 1
    assert result2["page"] == 2
    assert result1["result_count"] == 5
    ids1 = {r["id"] for r in result1["results"]}
    ids2 = {r["id"] for r in result2["results"]}
    assert ids1.isdisjoint(ids2)


def test_index_hash_stability():
    s1 = get_index_stats()
    s2 = get_index_stats()
    assert s1["index_hash"] == s2["index_hash"]


def test_query_approve():
    result = query_search("approve")
    assert result["total"] >= 1
    for r in result["results"]:
        assert "approve" in r["body"].lower() or "approve" in r["title"].lower() or any("approve" in t for t in r.get("tags", []))


def test_query_nonexistent():
    result = query_search("zzz_nonexistent_qqq_xyz")
    assert result["total"] == 0
    assert result["result_count"] == 0


def test_query_result_fields():
    result = query_search("risk")
    assert result["total"] >= 1
    for r in result["results"]:
        assert r["id"]
        assert r["type"]
        assert r["title"]
        assert r["body"]
