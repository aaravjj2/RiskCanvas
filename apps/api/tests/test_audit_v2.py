"""
Tests for AuditV2 + Provenance (v3.3+)

Covers:
- Chain determinism
- Tamper detection
- Reset idempotency (DEMO only)
- Provenance fields on key endpoints
- Canonicalization stable (byte-for-byte)
"""

import hashlib
import json
import os
import pytest

os.environ["DEMO_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app
from sqlmodel import SQLModel
from database import db

client = TestClient(app)


# ── autouse: ensure DEMO_MODE stays set + DB tables exist ────────────────────

@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    SQLModel.metadata.create_all(db.engine)
    yield


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reset_audit():
    r = client.post("/audit/v2/reset")
    assert r.status_code == 200


# ── AuditV2 Tests ─────────────────────────────────────────────────────────────

class TestAuditV2Events:
    def test_list_events_initially_empty_after_reset(self):
        _reset_audit()
        r = client.get("/audit/v2/events")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["events"] == []

    def test_events_endpoint_returns_chain_head(self):
        _reset_audit()
        r = client.get("/audit/v2/events")
        assert "chain_head" in r.json()

    def test_events_include_newly_emitted(self):
        _reset_audit()
        # Trigger a runs/execute to emit an audit event
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        r = client.get("/audit/v2/events")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_event_schema_fields(self):
        _reset_audit()
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        r = client.get("/audit/v2/events")
        ev = r.json()["events"][0]
        for field in ("event_id", "ts_norm", "actor", "action", "resource_type",
                      "payload_hash", "prev_hash", "chain_hash"):
            assert field in ev, f"Missing field: {field}"

    def test_event_payload_hash_is_sha256(self):
        _reset_audit()
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        ev = client.get("/audit/v2/events").json()["events"][0]
        assert len(ev["payload_hash"]) == 64
        int(ev["payload_hash"], 16)  # must be hex

    def test_event_ts_normalized_in_demo_mode(self):
        _reset_audit()
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        ev = client.get("/audit/v2/events").json()["events"][0]
        assert ev["ts_norm"] == "2026-01-01T00:00:00+00:00"

    def test_first_event_prev_hash_is_genesis(self):
        _reset_audit()
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        ev = client.get("/audit/v2/events").json()["events"][0]
        assert ev["prev_hash"] == "0" * 64

    def test_since_event_id_filter(self):
        _reset_audit()
        for _ in range(3):
            client.post("/runs/execute", json={"portfolio": {"assets": [
                {"symbol": "AAPL", "type": "stock", "quantity": 1,
                 "price": 150.0, "current_price": 150.0}
            ]}})
        # since_event_id=1 → only events with id > 1
        r = client.get("/audit/v2/events?since_event_id=1")
        events = r.json()["events"]
        assert all(e["event_id"] > 1 for e in events)

    def test_limit_parameter(self):
        _reset_audit()
        for _ in range(5):
            client.post("/runs/execute", json={"portfolio": {"assets": [
                {"symbol": "AAPL", "type": "stock", "quantity": 1,
                 "price": 150.0, "current_price": 150.0}
            ]}})
        r = client.get("/audit/v2/events?limit=2")
        assert len(r.json()["events"]) <= 2


class TestAuditV2Reset:
    def test_reset_returns_ok(self):
        r = client.post("/audit/v2/reset")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_reset_clears_store(self):
        # Add an event first
        client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        client.post("/audit/v2/reset")
        r = client.get("/audit/v2/events")
        assert r.json()["total"] == 0

    def test_reset_idempotent(self):
        """Multiple resets → always returns ok."""
        for _ in range(3):
            r = client.post("/audit/v2/reset")
            assert r.json()["ok"] is True


class TestAuditV2Verify:
    def test_verify_empty_chain_ok(self):
        _reset_audit()
        r = client.get("/audit/v2/verify")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["events_checked"] == 0
        assert data["first_bad_event_id"] is None

    def test_verify_intact_chain_ok(self):
        _reset_audit()
        for _ in range(3):
            client.post("/runs/execute", json={"portfolio": {"assets": [
                {"symbol": "AAPL", "type": "stock", "quantity": 1,
                 "price": 150.0, "current_price": 150.0}
            ]}})
        r = client.get("/audit/v2/verify")
        assert r.json()["ok"] is True

    def test_verify_tampered_chain_detects_bad_event(self):
        """Directly tamper an event and verify catches it."""
        _reset_audit()
        from audit_v2 import _store, emit_audit_v2
        emit_audit_v2(actor="alice", action="test.action", resource_type="test", resource_id="r1")
        emit_audit_v2(actor="bob", action="test.action2", resource_type="test", resource_id="r2")
        # Tamper event 0's chain_hash
        _store[0]["chain_hash"] = "deadbeef" + "0" * 56
        r = client.get("/audit/v2/verify")
        data = r.json()
        assert data["ok"] is False
        assert data["first_bad_event_id"] == 0

    def test_verify_returns_chain_head(self):
        _reset_audit()
        r = client.get("/audit/v2/verify")
        assert "chain_head" in r.json()


class TestAuditChainDeterminism:
    def test_same_events_same_chain_hash(self):
        """Two stores built with identical events → identical chain hashes."""
        from audit_v2 import reset_store, emit_audit_v2, get_chain_head

        reset_store()
        emit_audit_v2(actor="alice", action="test.run", resource_type="run", resource_id="r1",
                      payload={"portfolio_id": "p1"})
        emit_audit_v2(actor="bob", action="policy.evaluate", resource_type="policy", resource_id="pol1",
                      payload={"decision": "allow"})
        head1 = get_chain_head()

        reset_store()
        emit_audit_v2(actor="alice", action="test.run", resource_type="run", resource_id="r1",
                      payload={"portfolio_id": "p1"})
        emit_audit_v2(actor="bob", action="policy.evaluate", resource_type="policy", resource_id="pol1",
                      payload={"decision": "allow"})
        head2 = get_chain_head()

        assert head1 == head2

    def test_canonical_json_is_stable(self):
        """_canonical({...}) always produces the same bytes."""
        from audit_v2 import _canonical
        obj = {"b": 2, "a": 1, "c": [3, 1, 2]}
        s1 = _canonical(obj)
        s2 = _canonical(obj)
        assert s1 == s2
        # Keys must be sorted
        assert s1.index('"a"') < s1.index('"b"') < s1.index('"c"')


class TestProvenanceEndpoint:
    def test_provenance_for_run(self):
        _reset_audit()
        # Reset provenance store too
        from provenance import reset_provenance_store
        reset_provenance_store()

        r = client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        assert r.status_code == 200
        run_id = r.json()["run_id"]

        rp = client.get(f"/provenance/run/{run_id}")
        assert rp.status_code == 200
        data = rp.json()
        assert data["kind"] == "run"
        assert data["resource_id"] == run_id
        assert len(data["input_hash"]) == 64
        assert len(data["output_hash"]) == 64
        assert len(data["audit_chain_head_hash"]) == 64

    def test_provenance_unknown_run_404(self):
        r = client.get("/provenance/run/nonexistent-id")
        assert r.status_code == 404

    def test_provenance_invalid_kind_422(self):
        r = client.get("/provenance/badkind/someid")
        assert r.status_code == 422

    def test_runs_execute_includes_audit_chain_head(self):
        r = client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        assert r.status_code == 200
        assert "audit_chain_head" in r.json()
        assert len(r.json()["audit_chain_head"]) == 64

    def test_provenance_hashes_are_sha256(self):
        from provenance import reset_provenance_store
        reset_provenance_store()
        r = client.post("/runs/execute", json={"portfolio": {"assets": [
            {"symbol": "AAPL", "type": "stock", "quantity": 1,
             "price": 150.0, "current_price": 150.0}
        ]}})
        run_id = r.json()["run_id"]
        rp = client.get(f"/provenance/run/{run_id}")
        data = rp.json()
        for h in (data["input_hash"], data["output_hash"], data["audit_chain_head_hash"]):
            assert len(h) == 64
            int(h, 16)  # valid hex
