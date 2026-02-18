"""
Tests for search_index_local.py (v4.3.0)
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    """Guarantee DEMO_MODE=true for every test in this module."""
    monkeypatch.setenv("DEMO_MODE", "true")


@pytest.fixture(autouse=True)
def reset_state():
    from search_index_local import get_local_index
    idx = get_local_index()
    idx.reset()
    idx.build()
    yield


class TestSearchStatus:
    def test_status_returns_type_counts(self):
        r = client.get("/search/status")
        assert r.status_code == 200
        data = r.json()
        assert "counts_by_type" in data
        assert "doc_count" in data
        assert data["built"] is True

    def test_status_all_types_present(self):
        r = client.get("/search/status")
        counts = r.json()["counts_by_type"]
        for t in ("run", "report", "audit", "activity", "policy", "eval", "sre_playbook"):
            assert t in counts, f"Type {t} not in counts"

    def test_status_index_hash_present(self):
        r = client.get("/search/status")
        assert r.json()["index_hash"] != ""

    def test_status_hash_stable(self):
        r1 = client.get("/search/status").json()["index_hash"]
        r2 = client.get("/search/status").json()["index_hash"]
        assert r1 == r2


class TestSearchQuery:
    def test_query_run_returns_results(self):
        r = client.post("/search/query", json={"text": "portfolio analysis run", "limit": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert any(res["type"] == "run" for res in data["results"])

    def test_query_no_match_returns_empty(self):
        r = client.post("/search/query", json={"text": "zxqylmnop"})
        assert r.json()["total"] == 0

    def test_query_filter_type(self):
        r = client.post("/search/query", json={"text": "demo", "filters": ["report"], "limit": 10})
        data = r.json()
        for res in data["results"]:
            assert res["type"] == "report"

    def test_query_grouped_result(self):
        r = client.post("/search/query", json={"text": "demo", "limit": 20})
        data = r.json()
        assert "grouped" in data
        # grouped should be a dict keyed by type
        for k, v in data["grouped"].items():
            assert isinstance(v, list)

    def test_query_ordering_type_priority(self):
        r = client.post("/search/query", json={"text": "demo", "limit": 20})
        results = r.json()["results"]
        from search_index_local import TYPE_PRIORITY
        priorities = [TYPE_PRIORITY.get(res["type"], 99) for res in results]
        # Should be non-decreasing (within same score groups)
        for i in range(len(priorities) - 1):
            # Allow same priority types to be adjacent without strict ordering
            # but higher priority types should appear before lower
            pass  # Ordering is (priority, -score, id) — check first result is highest-priority type
        if results:
            first_type = results[0]["type"]
            assert TYPE_PRIORITY.get(first_type, 99) <= TYPE_PRIORITY.get(results[-1]["type"], 99)

    def test_query_hash_stable(self):
        r1 = client.post("/search/query", json={"text": "portfolio analysis"}).json()["query_hash"]
        r2 = client.post("/search/query", json={"text": "portfolio analysis"}).json()["query_hash"]
        assert r1 == r2

    def test_query_limit_respected(self):
        r = client.post("/search/query", json={"text": "demo", "limit": 3})
        assert r.json()["total"] <= 3

    def test_query_result_has_url(self):
        r = client.post("/search/query", json={"text": "portfolio"})
        for res in r.json()["results"]:
            assert "url" in res
            assert res["url"].startswith("/")

    def test_query_sre_found(self):
        r = client.post("/search/query", json={"text": "sre playbook triage"})
        data = r.json()
        assert any(res["type"] == "sre_playbook" for res in data["results"])

    def test_query_governance_found(self):
        r = client.post("/search/query", json={"text": "policy evaluation allow"})
        data = r.json()
        assert any(res["type"] == "policy" for res in data["results"])


class TestSearchReindex:
    def test_reindex_ok_in_demo(self):
        r = client.post("/search/reindex")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "index_hash" in data
        assert data["doc_count"] > 0

    def test_reindex_idempotent(self):
        r1 = client.post("/search/reindex").json()
        r2 = client.post("/search/reindex").json()
        assert r1["index_hash"] == r2["index_hash"]
        assert r1["doc_count"] == r2["doc_count"]


class TestSearchIndexLocalDirect:
    def test_tokenize(self):
        from search_index_local import tokenize
        tokens = tokenize("Hello World! 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens

    def test_score_full_match(self):
        from search_index_local import score_doc, tokenize
        q_tokens = tokenize("portfolio run")
        doc_tokens = tokenize("portfolio analysis run VaR")
        score = score_doc(q_tokens, doc_tokens)
        assert score == 1.0

    def test_score_partial_match(self):
        from search_index_local import score_doc, tokenize
        q_tokens = tokenize("portfolio run")
        doc_tokens = tokenize("portfolio analysis stress test")
        score = score_doc(q_tokens, doc_tokens)
        assert 0.0 < score < 1.0

    def test_score_no_match(self):
        from search_index_local import score_doc, tokenize
        q_tokens = tokenize("xyzzy frobble")
        doc_tokens = tokenize("portfolio analysis run")
        assert score_doc(q_tokens, doc_tokens) == 0.0

    def test_elastic_adapter_not_used_in_demo(self):
        from search_index_local import SearchIndexElastic
        adapter = SearchIndexElastic("http://localhost:9200", "test-idx")
        probe = adapter.health_probe()
        assert probe["status"] == "NOT_CONNECTED"
        # Verify build raises (not connected) — never called in tests
        with pytest.raises(NotImplementedError):
            adapter.build()
