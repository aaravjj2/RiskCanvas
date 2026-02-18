"""
Tests for presence.py (v4.1.0)
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
    from presence import seed_demo_presence
    seed_demo_presence()
    yield


class TestPresenceList:
    def test_get_presence_returns_records(self):
        r = client.get("/presence")
        assert r.status_code == 200
        data = r.json()
        assert "presence" in data
        assert data["count"] == 4  # DEMO has 4 actors

    def test_presence_schema(self):
        r = client.get("/presence")
        rec = r.json()["presence"][0]
        for key in ("workspace_id", "actor", "display", "status", "last_seen_norm", "presence_hash"):
            assert key in rec, f"Missing key: {key}"

    def test_presence_filter_by_workspace(self):
        r = client.get("/presence?workspace_id=demo-workspace")
        assert r.json()["count"] == 4

    def test_presence_filter_unknown_workspace(self):
        r = client.get("/presence?workspace_id=no-such-ws")
        assert r.json()["count"] == 0

    def test_online_count(self):
        r = client.get("/presence")
        assert r.json()["online_count"] == 2  # alice + bob online

    def test_idle_count(self):
        r = client.get("/presence")
        assert r.json()["idle_count"] == 1  # carol idle

    def test_ordering_online_first(self):
        r = client.get("/presence")
        records = r.json()["presence"]
        statuses = [rec["status"] for rec in records]
        # online before idle before offline
        seen_online = False
        seen_idle = False
        seen_offline = False
        for s in statuses:
            if s == "online":
                assert not seen_idle and not seen_offline
                seen_online = True
            elif s == "idle":
                assert not seen_offline
                seen_idle = True
            elif s == "offline":
                seen_offline = True


class TestPresenceUpdate:
    def test_update_demo_noop(self):
        r = client.post("/presence/update", json={
            "workspace_id": "demo-workspace",
            "actor": "alice@demo",
            "status": "idle",
        })
        assert r.status_code == 200
        resp = r.json()
        assert resp["demo_mode"] is True or "status" in resp

    def test_update_new_actor_in_demo(self):
        r = client.post("/presence/update", json={
            "workspace_id": "demo-workspace",
            "actor": "newuser@demo",
            "status": "online",
            "display": "New User",
        })
        assert r.status_code == 200

    def test_presence_hash_stable(self):
        from presence import seed_demo_presence
        seed_demo_presence()
        r1 = client.get("/presence").json()["presence"]
        seed_demo_presence()
        r2 = client.get("/presence").json()["presence"]
        hashes1 = [rec["presence_hash"] for rec in r1]
        hashes2 = [rec["presence_hash"] for rec in r2]
        assert hashes1 == hashes2

    def test_last_seen_deterministic(self):
        from presence import _demo_last_seen
        ls1 = _demo_last_seen("alice@demo")
        ls2 = _demo_last_seen("alice@demo")
        assert ls1 == ls2

    def test_display_name_derived(self):
        r = client.get("/presence")
        for rec in r.json()["presence"]:
            # display should be non-empty
            assert rec["display"]
            assert len(rec["display"]) > 0
