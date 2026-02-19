"""
Tests for v4.18.0-v4.20.0 Replay Store + Golden Suites + Repro Report (Wave 17)
Verifies: store/verify determinism, tamper detection, suites, scorecard.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_replay():
    """Reset replay store before each test."""
    from replay_store import reset_replay_store
    reset_replay_store()
    yield
    reset_replay_store()


SAMPLE_REQUEST = {"symbol": "AAPL", "start": "2025-01-01", "end": "2025-12-31"}
SAMPLE_RESPONSE = {
    "symbol": "AAPL",
    "series": [{"date": "2025-01-02", "close": 150.0}],
    "output_hash": "abc123",
    "audit_chain_head_hash": "replaye8f9a0b1c2d3",
}


def test_replay_id_determinism():
    """Same request → same replay_id."""
    from replay_store import make_replay_id

    r1 = make_replay_id({"endpoint": "/market/series", "request": SAMPLE_REQUEST})
    r2 = make_replay_id({"endpoint": "/market/series", "request": SAMPLE_REQUEST})
    assert r1 == r2
    assert len(r1) == 32


def test_replay_id_content_based():
    """Different requests → different replay_id."""
    from replay_store import make_replay_id

    r1 = make_replay_id({"endpoint": "/market/series", "request": SAMPLE_REQUEST})
    r2 = make_replay_id({"endpoint": "/market/spot", "request": {"symbol": "MSFT"}})
    assert r1 != r2


def test_replay_store_and_verify():
    """Store then verify returns verified=True."""
    from replay_store import store_replay_entry, verify_replay

    record = store_replay_entry("/market/series", SAMPLE_REQUEST, SAMPLE_RESPONSE)
    result = verify_replay(record["replay_id"])

    assert result["verified"] is True
    assert result["mismatch_count"] == 0


def test_replay_verify_deterministic():
    """Verify is deterministic across calls."""
    from replay_store import store_replay_entry, verify_replay

    record = store_replay_entry("/market/series", SAMPLE_REQUEST, SAMPLE_RESPONSE)

    r1 = verify_replay(record["replay_id"])
    r2 = verify_replay(record["replay_id"])
    assert r1["verified"] == r2["verified"]
    assert r1["response_hash"] == r2["response_hash"]


def test_replay_tamper_detection():
    """Tampered response should fail verification."""
    from replay_store import store_replay_entry, verify_replay, _replay_store

    record = store_replay_entry("/market/series", SAMPLE_REQUEST, SAMPLE_RESPONSE)
    replay_id = record["replay_id"]

    # Tamper with stored response
    _replay_store[replay_id]["response_payload"]["symbol"] = "TAMPERED"

    result = verify_replay(replay_id)
    # The stored response_hash no longer matches the tampered payload
    assert result["verified"] is False or result["mismatch_count"] > 0


def test_replay_verify_not_found():
    """Verify non-existent replay raises ValueError."""
    from replay_store import verify_replay

    with pytest.raises(ValueError, match="not found"):
        verify_replay("nonexistent_replay_id_00000000000000")


def test_replay_suites_list():
    """List suites returns stable list."""
    from replay_store import list_replay_suites

    s1 = list_replay_suites()
    s2 = list_replay_suites()
    assert s1 == s2
    assert len(s1) >= 3
    ids = [s["suite_id"] for s in s1]
    assert ids == sorted(ids)


def test_replay_suite_run_deterministic():
    """Same suite → same scorecard output_hash."""
    from replay_store import run_replay_suite

    sc1 = run_replay_suite("suite_market_data_v1")
    sc2 = run_replay_suite("suite_market_data_v1")
    assert sc1["output_hash"] == sc2["output_hash"]


def test_replay_suite_all_pass():
    """Demo suites should all pass in fixture mode."""
    from replay_store import run_replay_suite, list_replay_suites

    for suite in list_replay_suites():
        scorecard = run_replay_suite(suite["suite_id"])
        assert scorecard["failed"] == 0
        assert scorecard["pass_rate"] == 100.0


def test_replay_suite_not_found():
    """Running non-existent suite raises ValueError."""
    from replay_store import run_replay_suite

    with pytest.raises(ValueError, match="not found"):
        run_replay_suite("nonexistent_suite_xyz")


def test_repro_report_deterministic():
    """Reproducibility report hash is stable."""
    from replay_store import build_repro_report

    r1 = build_repro_report("suite_pnl_attr_v1")
    r2 = build_repro_report("suite_pnl_attr_v1")
    assert r1["scorecard"]["output_hash"] == r2["scorecard"]["output_hash"]
    assert r1["manifest"]["manifest_hash"] == r2["manifest"]["manifest_hash"]


def test_replay_api_store():
    """Store API endpoint persists entry."""
    from main import app

    client = TestClient(app)
    payload = {
        "endpoint": "/market/series",
        "request_payload": SAMPLE_REQUEST,
        "response_payload": SAMPLE_RESPONSE,
    }
    resp = client.post("/replay/store", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["stored"] is True
    assert "replay_id" in data


def test_replay_api_verify():
    """Verify API returns verified=True for stored entry."""
    from main import app

    client = TestClient(app)
    store_resp = client.post("/replay/store", json={
        "endpoint": "/market/spot",
        "request_payload": {"symbol": "MSFT"},
        "response_payload": {"symbol": "MSFT", "price": 300.0},
    })
    replay_id = store_resp.json()["replay_id"]

    verify_resp = client.post("/replay/verify", json={"replay_id": replay_id})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True


def test_replay_api_suites_list():
    """Suites list API endpoint works."""
    from main import app

    client = TestClient(app)
    resp = client.get("/replay/suites/list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 3


def test_replay_api_run_suite():
    """Run suite API returns scorecard."""
    from main import app

    client = TestClient(app)
    resp = client.post("/replay/run-suite", json={"suite_id": "suite_market_data_v1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "passed" in data
    assert "failed" in data
    assert data["failed"] == 0


def test_replay_api_repro_report():
    """Repro report export API works."""
    from main import app

    client = TestClient(app)
    resp = client.post("/exports/repro-report-pack", json={"suite_id": "suite_pnl_attr_v1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "manifest" in data
    assert data["manifest"]["manifest_hash"] is not None
