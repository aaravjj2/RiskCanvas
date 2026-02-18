"""
Tests for live_run.py (v4.2.0)
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
    from live_run import get_run_status_store
    get_run_status_store().reset()
    get_run_status_store().seed_demo()
    yield


class TestRunStatus:
    def test_seeded_run_done(self):
        r = client.get("/runs/run-demo-001/status")
        assert r.status_code == 200
        data = r.json()
        assert data["stage"] == "DONE"
        assert data["pct"] == 100
        assert data["done"] is True

    def test_unknown_run_not_started(self):
        r = client.get("/runs/unknown-run-xyz/status")
        assert r.status_code == 200
        data = r.json()
        assert data["stage"] == "NOT_STARTED"
        assert data["pct"] == 0
        assert data["done"] is False

    def test_run_status_schema(self):
        r = client.get("/runs/run-demo-001/status")
        data = r.json()
        for key in ("run_id", "stage", "label", "pct", "done", "status_hash"):
            assert key in data, f"Missing key: {key}"

    def test_status_hash_stable(self):
        r1 = client.get("/runs/run-demo-001/status").json()
        r2 = client.get("/runs/run-demo-001/status").json()
        assert r1["status_hash"] == r2["status_hash"]

    def test_set_stage_stores_correctly(self):
        from live_run import get_run_status_store
        store = get_run_status_store()
        rec = store.set_stage("run-test-1", "PRICE", 35, "Pricing options")
        assert rec["stage"] == "PRICE"
        assert rec["pct"] == 35
        retrieved = store.get("run-test-1")
        assert retrieved["stage"] == "PRICE"

    def test_reset_clears_store(self):
        from live_run import get_run_status_store
        store = get_run_status_store()
        store.set_stage("run-extra", "VAR", 60, "Computing VaR")
        store.reset()
        assert store.get("run-extra") is None


class TestSSERunProgress:
    def test_run_progress_endpoint_200(self):
        r = client.get("/events/run-progress?run_id=test-run-sse", headers={"Accept": "text/event-stream"})
        assert r.status_code == 200

    def test_run_progress_content_type(self):
        r = client.get("/events/run-progress?run_id=test-run-sse")
        assert "text/event-stream" in r.headers.get("content-type", "")

    def test_run_progress_contains_stages(self):
        r = client.get("/events/run-progress?run_id=test-run-stages")
        text = r.text
        for stage in ("VALIDATE", "PRICE", "VAR", "REPORT", "DONE"):
            assert stage in text, f"Stage {stage} not found"

    def test_run_progress_contains_pct_100(self):
        r = client.get("/events/run-progress?run_id=test-run-pct")
        assert '"pct": 100' in r.text or '"pct":100' in r.text

    def test_run_progress_done_at_end(self):
        r = client.get("/events/run-progress?run_id=test-run-done")
        # Last event should have DONE
        assert "DONE" in r.text

    def test_run_progress_deterministic(self):
        r1 = client.get("/events/run-progress?run_id=test-run-det")
        r2 = client.get("/events/run-progress?run_id=test-run-det")
        assert r1.text == r2.text


class TestSSEActivity:
    def test_activity_stream_200(self):
        from activity_stream import seed_demo_activity
        seed_demo_activity()
        r = client.get("/events/activity?workspace_id=demo-workspace")
        assert r.status_code == 200

    def test_activity_stream_contains_events(self):
        from activity_stream import seed_demo_activity
        seed_demo_activity()
        r = client.get("/events/activity?workspace_id=demo-workspace")
        assert "activity.event" in r.text

    def test_activity_stream_sentinel(self):
        from activity_stream import seed_demo_activity
        seed_demo_activity()
        r = client.get("/events/activity?workspace_id=demo-workspace")
        assert "activity.connected" in r.text


class TestSSEPresence:
    def test_presence_stream_200(self):
        from presence import seed_demo_presence
        seed_demo_presence()
        r = client.get("/events/presence?workspace_id=demo-workspace")
        assert r.status_code == 200

    def test_presence_stream_contains_updates(self):
        from presence import seed_demo_presence
        seed_demo_presence()
        r = client.get("/events/presence?workspace_id=demo-workspace")
        assert "presence.update" in r.text

    def test_presence_stream_sentinel(self):
        from presence import seed_demo_presence
        seed_demo_presence()
        r = client.get("/events/presence?workspace_id=demo-workspace")
        assert "presence.connected" in r.text
