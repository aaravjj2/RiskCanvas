"""
Tests for activity_stream.py (v4.1.0)
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    """Guarantee DEMO_MODE=true for every test in this module."""
    monkeypatch.setenv("DEMO_MODE", "true")


@pytest.fixture(autouse=True)
def reset_state():
    """Seed demo activity before each test."""
    from activity_stream import seed_demo_activity
    seed_demo_activity()
    yield


# ─────────────────────────────────────────────
# TestActivityList
# ─────────────────────────────────────────────

class TestActivityList:
    def test_list_returns_events(self):
        r = client.get("/activity")
        assert r.status_code == 200
        data = r.json()
        assert "events" in data
        assert data["count"] == len(data["events"])

    def test_list_seeded_count(self):
        r = client.get("/activity")
        assert r.json()["count"] == 8  # DEMO_SEED has 8 entries

    def test_list_event_schema(self):
        r = client.get("/activity")
        ev = r.json()["events"][0]
        for key in ("event_id", "workspace_id", "actor", "type", "message", "ts", "event_hash"):
            assert key in ev, f"Missing key: {key}"

    def test_list_filter_by_workspace(self):
        r = client.get("/activity?workspace_id=demo-workspace")
        assert r.json()["count"] == 8

    def test_list_filter_unknown_workspace(self):
        r = client.get("/activity?workspace_id=does-not-exist")
        assert r.json()["count"] == 0

    def test_list_limit_respected(self):
        r = client.get("/activity?limit=3")
        assert r.json()["count"] <= 3

    def test_list_since_event_id(self):
        r = client.get("/activity?since_event_id=4")
        events = r.json()["events"]
        for ev in events:
            assert ev["event_id"] > 4

    def test_list_ordering_newest_first(self):
        r = client.get("/activity")
        ids = [ev["event_id"] for ev in r.json()["events"]]
        assert ids == sorted(ids, reverse=True)


# ─────────────────────────────────────────────
# TestActivityReset
# ─────────────────────────────────────────────

class TestActivityReset:
    def test_reset_returns_seeded_count(self):
        r = client.post("/activity/reset")
        assert r.status_code == 200
        assert r.json()["seeded"] == 8

    def test_reset_idempotent(self):
        r1 = client.post("/activity/reset")
        r2 = client.post("/activity/reset")
        assert r1.json()["seeded"] == r2.json()["seeded"]

    def test_reset_restores_full_list(self):
        # Emit extra event
        from activity_stream import emit_activity
        emit_activity(workspace_id="demo-workspace", actor="test", event_type="run.execute", message="extra")
        r_before = client.get("/activity")
        count_before = r_before.json()["count"]
        # Reset
        client.post("/activity/reset")
        r_after = client.get("/activity")
        assert r_after.json()["count"] == 8


# ─────────────────────────────────────────────
# TestActivityDeterminism
# ─────────────────────────────────────────────

class TestActivityDeterminism:
    def test_event_hash_stable(self):
        r1 = client.post("/activity/reset")
        r2 = client.post("/activity/reset")
        ev1 = client.get("/activity").json()["events"]
        ev2 = client.get("/activity").json()["events"]
        hashes1 = [e["event_hash"] for e in ev1]
        hashes2 = [e["event_hash"] for e in ev2]
        assert hashes1 == hashes2

    def test_event_ids_sequential(self):
        client.post("/activity/reset")
        events = client.get("/activity").json()["events"]
        ids = sorted([e["event_id"] for e in events])
        assert ids == list(range(1, len(events) + 1))

    def test_ts_field_present(self):
        events = client.get("/activity").json()["events"]
        for ev in events:
            assert ev["ts"].startswith("2026-")

    def test_event_types_valid(self):
        from activity_stream import EVENT_TYPES
        events = client.get("/activity").json()["events"]
        for ev in events:
            assert ev["type"] in EVENT_TYPES
