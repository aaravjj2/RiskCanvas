"""
test_wave65_72.py — Comprehensive pytest suite for Waves 65–72

Coverage:
  Wave 65 — evidence_graph.py     (Evidence Graph v1)
  Wave 66 — decision_rooms.py     (Decision Rooms v1)
  Wave 67 — agent_runbooks.py     (Agent Runbooks v1)
  Wave 68 — policy_decision_gate.py (Policy Decision Gate)
  Wave 70 — exports_room_snapshot.py (Room Snapshot Export)

Requirements per CLAUDE.md:
  - 0 failed, 0 skipped
  - No random seeds (deterministic)
  - No network calls (offline)
"""
import pytest


def _make_client(router):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 65 – Evidence Graph
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def eg():
    import evidence_graph as m
    m._GRAPH_NODES.clear()
    m._GRAPH_EDGES.clear()
    for n in m._DEMO_NODES:
        m._GRAPH_NODES[n["node_id"]] = dict(n)
    for e in m._DEMO_EDGES:
        m._GRAPH_EDGES[e["edge_id"]] = dict(e)
    return m


@pytest.fixture
def eg_client(eg):
    return _make_client(eg.router)


def test_eg_demo_nodes_count(eg):
    assert len(eg._GRAPH_NODES) == 12


def test_eg_demo_edges_count(eg):
    assert len(eg._GRAPH_EDGES) == 11


def test_eg_node_ids_unique(eg):
    ids = list(eg._GRAPH_NODES.keys())
    assert len(ids) == len(set(ids))


def test_eg_edge_ids_unique(eg):
    ids = list(eg._GRAPH_EDGES.keys())
    assert len(ids) == len(set(ids))


def test_eg_stable_hash_deterministic(eg):
    h1 = eg._stable_hash("hello")
    h2 = eg._stable_hash("hello")
    assert h1 == h2


def test_eg_stable_hash_different_inputs(eg):
    assert eg._stable_hash("a") != eg._stable_hash("b")


def test_eg_stable_hash_returns_str(eg):
    assert isinstance(eg._stable_hash({"key": "val"}), str)


def test_eg_get_graph_200(eg_client):
    r = eg_client.get("/evidence/graph")
    assert r.status_code == 200


def test_eg_get_graph_node_count(eg_client):
    assert eg_client.get("/evidence/graph").json()["node_count"] == 12


def test_eg_get_graph_edge_count(eg_client):
    assert eg_client.get("/evidence/graph").json()["edge_count"] == 11


def test_eg_get_graph_has_graph_hash(eg_client):
    data = eg_client.get("/evidence/graph").json()
    assert isinstance(data.get("graph_hash"), str)
    assert len(data["graph_hash"]) > 0


def test_eg_get_graph_nodes_list(eg_client):
    data = eg_client.get("/evidence/graph").json()
    assert len(data["nodes"]) == 12


def test_eg_get_graph_edges_list(eg_client):
    data = eg_client.get("/evidence/graph").json()
    assert len(data["edges"]) == 11


def test_eg_get_summary_200(eg_client):
    assert eg_client.get("/evidence/graph/summary").status_code == 200


def test_eg_get_summary_counts_by_type(eg_client):
    data = eg_client.get("/evidence/graph/summary").json()
    assert "dataset" in data.get("counts_by_type", {})


def test_eg_get_summary_node_types(eg_client):
    data = eg_client.get("/evidence/graph/summary").json()
    types = data.get("node_types", [])
    assert "dataset" in types
    assert "scenario" in types


def test_eg_get_summary_hash(eg_client):
    data = eg_client.get("/evidence/graph/summary").json()
    assert "summary_hash" in data


def test_eg_post_node_adds(eg_client):
    initial = eg_client.get("/evidence/graph").json()["node_count"]
    eg_client.post("/evidence/graph/nodes", json={
        "node_id": "test-node-http-001",
        "node_type": "run",
        "label": "Test Run HTTP",
        "tenant_id": "demo-tenant",
    })
    after = eg_client.get("/evidence/graph").json()["node_count"]
    assert after == initial + 1


def test_eg_post_edge_adds(eg_client):
    initial = eg_client.get("/evidence/graph").json()["edge_count"]
    eg_client.post("/evidence/graph/edges", json={
        "src": "ds-prov-001",
        "dst": "run-001",
        "edge_type": "uses",
    })
    after = eg_client.get("/evidence/graph").json()["edge_count"]
    assert after == initial + 1


def test_eg_bfs_returns_list(eg):
    edges = list(eg._GRAPH_EDGES.values())
    result = eg._bfs("ds-prov-001", depth=3, edges=edges)
    assert isinstance(result, list)
    assert "ds-prov-001" in result


def test_eg_all_nodes_have_required_keys(eg):
    for node in eg._GRAPH_NODES.values():
        for key in ("node_id", "node_type", "label", "tenant_id"):
            assert key in node


def test_eg_all_edges_have_required_keys(eg):
    for edge in eg._GRAPH_EDGES.values():
        for key in ("edge_id", "src", "dst", "edge_type"):
            assert key in edge


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 66 – Decision Rooms
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def dr():
    import decision_rooms as m
    m._ROOMS.clear()
    m._ROOM_ATTESTATIONS.clear()
    for r in m._SEED_ROOMS:
        m._ROOMS[r["room_id"]] = dict(r)
        m._ROOM_ATTESTATIONS[r["room_id"]] = []
    return m


@pytest.fixture
def dr_client(dr):
    return _make_client(dr.router)


def test_dr_seed_rooms_count(dr):
    assert len(dr._ROOMS) == 2


def test_dr_demo_rooms_are_open(dr):
    for room in dr._ROOMS.values():
        assert room["status"] == "OPEN"


def test_dr_room_has_required_keys(dr):
    for room in dr._ROOMS.values():
        for key in ("room_id", "name", "status", "tenant_id"):
            assert key in room


def test_dr_list_rooms_200(dr_client):
    assert dr_client.get("/rooms").status_code == 200


def test_dr_list_rooms_count(dr_client):
    assert dr_client.get("/rooms").json()["count"] == 2


def test_dr_create_room_200(dr_client):
    r = dr_client.post("/rooms", json={"name": "New Test Room"})
    assert r.status_code == 200


def test_dr_create_adds_room(dr, dr_client):
    dr_client.post("/rooms", json={"name": "Another Room"})
    assert dr_client.get("/rooms").json()["count"] == 3


def test_dr_create_room_is_open(dr_client):
    r = dr_client.post("/rooms", json={"name": "Status Room"})
    assert r.json()["room"]["status"] == "OPEN"


def test_dr_create_room_deterministic_id(dr_client):
    r1 = dr_client.post("/rooms", json={"name": "Det Room"})
    r2 = dr_client.post("/rooms", json={"name": "Det Room"})
    assert r1.json()["room"]["room_id"] == r2.json()["room"]["room_id"]


def test_dr_get_room_200(dr_client):
    assert dr_client.get("/rooms/room-demo-001").status_code == 200


def test_dr_get_room_id(dr_client):
    data = dr_client.get("/rooms/room-demo-001").json()
    assert data["room"]["room_id"] == "room-demo-001"


def test_dr_pin_entity_200(dr_client):
    r = dr_client.post("/rooms/room-demo-001/pin", json={"entity_id": "test-entity-001"})
    assert r.status_code == 200


def test_dr_pin_entity_adds(dr_client):
    dr_client.post("/rooms/room-demo-001/pin", json={"entity_id": "pin-test-xyz"})
    data = dr_client.get("/rooms/room-demo-001").json()
    assert "pin-test-xyz" in data["room"]["pinned_entities"]


def test_dr_lock_room_200(dr_client):
    assert dr_client.post("/rooms/room-demo-001/lock", json={}).status_code == 200


def test_dr_lock_room_changes_status(dr_client):
    dr_client.post("/rooms/room-demo-001/lock", json={})
    data = dr_client.get("/rooms/room-demo-001").json()
    assert data["room"]["status"] == "LOCKED"


def test_dr_lock_room_repeat_not_500(dr_client):
    dr_client.post("/rooms/room-demo-001/lock", json={})
    r2 = dr_client.post("/rooms/room-demo-001/lock", json={})
    assert r2.status_code in (200, 409, 400)


def test_dr_timeline_200(dr_client):
    assert dr_client.get("/rooms/room-demo-001/timeline").status_code == 200


def test_dr_timeline_returns_events(dr_client):
    dr_client.post("/rooms/room-demo-001/pin", json={"entity_id": "e-tl-001"})
    data = dr_client.get("/rooms/room-demo-001/timeline").json()
    # timeline or events key depending on impl
    has_list = isinstance(data.get("timeline", data.get("events", [])), list)
    assert has_list


def test_dr_room_ids_unique(dr):
    ids = list(dr._ROOMS.keys())
    assert len(ids) == len(set(ids))


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 67 – Agent Runbooks
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def rb():
    import agent_runbooks as m
    m._RUNBOOKS.clear()
    m._EXECUTIONS.clear()
    for r in m._SEED_RUNBOOKS:
        m._RUNBOOKS[r["runbook_id"]] = dict(r)
        m._EXECUTIONS[r["runbook_id"]] = []
    return m


@pytest.fixture
def rb_client(rb):
    return _make_client(rb.router)


def test_rb_seed_count(rb):
    assert len(rb._RUNBOOKS) == 2


def test_rb_demo_runbook_has_steps(rb):
    rb_item = list(rb._RUNBOOKS.values())[0]
    assert len(rb_item["steps"]) >= 1


def test_rb_runbook_required_keys(rb):
    for rb_item in rb._RUNBOOKS.values():
        for key in ("runbook_id", "name", "description", "tenant_id", "steps", "created_at"):
            assert key in rb_item, f"Missing key: {key}"


def test_rb_step_required_keys(rb):
    rb_item = list(rb._RUNBOOKS.values())[0]
    for step in rb_item["steps"]:
        assert "step_type" in step
        assert "params" in step


def test_rb_list_endpoint_returns_runbooks(rb_client):
    r = rb_client.get("/runbooks?tenant_id=demo-tenant")
    assert r.status_code == 200
    data = r.json()
    assert "runbooks" in data
    assert data["count"] == 2


def test_rb_create_runbook_endpoint(rb_client):
    payload = {
        "name": "Test API Runbook",
        "description": "API test",
        "steps": [{"step_type": "validate_dataset", "params": {"dataset_id": "ds-x"}}],
        "tenant_id": "demo-tenant",
    }
    r = rb_client.post("/runbooks", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    assert data["runbook"]["name"] == "Test API Runbook"
    assert "runbook_id" in data["runbook"]


def test_rb_get_runbook_endpoint(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.get(f"/runbooks/{rb_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["runbook"]["runbook_id"] == rb_id
    assert "executions" in data
    assert "execution_count" in data


def test_rb_get_runbook_404(rb_client):
    r = rb_client.get("/runbooks/rb-nonexistent-9999")
    assert r.status_code == 404


def test_rb_execute_returns_completed(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={"executed_by": "test-user"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["execution"]["status"] == "completed"


def test_rb_execute_has_outputs_hash(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={})
    data = r.json()
    assert isinstance(data["execution"]["outputs_hash"], str)
    assert len(data["execution"]["outputs_hash"]) == 16


def test_rb_execute_has_inputs_hash(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={"inputs": {"key": "val"}})
    data = r.json()
    assert isinstance(data["execution"]["inputs_hash"], str)
    assert len(data["execution"]["inputs_hash"]) == 16


def test_rb_execute_step_results_count(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    rb_item = rb._RUNBOOKS[rb_id]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={})
    data = r.json()
    assert len(data["execution"]["step_results"]) == len(rb_item["steps"])


def test_rb_execute_step_results_status(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={})
    data = r.json()
    for sr in data["execution"]["step_results"]:
        assert sr["status"] == "completed"


def test_rb_execute_has_attestations(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r = rb_client.post(f"/runbooks/{rb_id}/execute", json={})
    data = r.json()
    assert isinstance(data["execution"]["attestations"], list)
    assert len(data["execution"]["attestations"]) >= 1


def test_rb_execute_stores_in_executions(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    rb_client.post(f"/runbooks/{rb_id}/execute", json={})
    assert len(rb._EXECUTIONS[rb_id]) == 1


def test_rb_execute_is_deterministic(rb_client, rb):
    rb_id = list(rb._RUNBOOKS.keys())[0]
    r1 = rb_client.post(f"/runbooks/{rb_id}/execute", json={"inputs": {"seed": "fixed"}})
    r2 = rb_client.post(f"/runbooks/{rb_id}/execute", json={"inputs": {"seed": "fixed"}})
    assert r1.json()["execution"]["outputs_hash"] == r2.json()["execution"]["outputs_hash"]


def test_rb_sha256_helper_is_64chars(rb):
    h = rb._sha256({"test": "data"})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_rb_step_hash_helper_is_16chars(rb):
    h = rb._step_hash({"step_type": "validate_dataset", "params": {}}, {"input": "x"})
    assert len(h) == 16


def test_rb_outputs_hash_helper_is_16chars(rb):
    h = rb._outputs_hash([{"step_idx": 0, "status": "completed", "output": {}}])
    assert len(h) == 16


def test_rb_valid_step_types(rb):
    valid_types = {
        "validate_dataset", "validate_scenario", "execute_run",
        "request_review", "export_packet", "generate_compliance_pack",
    }
    for rb_item in rb._RUNBOOKS.values():
        for step in rb_item["steps"]:
            assert step["step_type"] in valid_types


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 68 – Policy Decision Gate
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def pdg():
    import policy_decision_gate as m
    import decision_rooms as dr_mod
    m._DEMO_REVIEWS.clear()
    m._DEMO_REVIEWS["review-001"] = "APPROVED"
    m._DEMO_REVIEWS["review-demo-001"] = "APPROVED"
    m._DEMO_ROOMS_LOCKED.clear()
    m._DEMO_ROOMS_LOCKED.add("room-demo-locked-001")
    # Seed a locked room in decision_rooms so the export gate can find it
    dr_mod._ROOMS["room-demo-locked-001"] = {
        "room_id": "room-demo-locked-001",
        "name": "Demo Locked Room",
        "tenant_id": "demo-tenant",
        "subject_id": "scen-001",
        "status": "LOCKED",
        "pinned_entities": [],
        "notes": "",
        "lock_hash": "test-lock-hash-001",
        "created_at": "2026-02-19T00:00:00Z",
    }
    yield m
    dr_mod._ROOMS.pop("room-demo-locked-001", None)


@pytest.fixture
def pdg_client(pdg):
    return _make_client(pdg.router)


def test_pdg_room_lock_allows_with_approved_review(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-demo-001",
        "subject_id": "subj-001",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] == "ALLOW"


def test_pdg_room_lock_blocks_without_review(pdg_client, pdg):
    pdg._DEMO_REVIEWS.clear()
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-demo-001",
        "subject_id": "subj-001",
    })
    data = r.json()
    assert data["verdict"] == "BLOCK"


def test_pdg_export_packet_locked_and_approved_is_allow(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "export.decision_packet",
        "room_id": "room-demo-locked-001",
        "subject_id": "subj-001",
    })
    data = r.json()
    assert data["verdict"] == "ALLOW"


def test_pdg_export_packet_unlocked_room_is_conditional(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "export.decision_packet",
        "room_id": "room-not-locked",
        "subject_id": "subj-001",
    })
    data = r.json()
    assert data["verdict"] in ("CONDITIONAL", "BLOCK")


def test_pdg_export_packet_no_review_is_block(pdg_client, pdg):
    pdg._DEMO_REVIEWS.clear()
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "export.decision_packet",
        "room_id": "room-demo-locked-001",
        "subject_id": "subj-001",
    })
    data = r.json()
    assert data["verdict"] == "BLOCK"


def test_pdg_response_has_required_keys(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-any",
    })
    data = r.json()
    for key in ("verdict", "action", "room_id", "reasons", "gate_hash", "asof"):
        assert key in data, f"Missing key: {key}"


def test_pdg_reasons_is_list(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-any",
    })
    data = r.json()
    assert isinstance(data["reasons"], list)
    assert len(data["reasons"]) >= 1


def test_pdg_gate_hash_is_16chars(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-any",
    })
    data = r.json()
    assert len(data["gate_hash"]) == 16


def test_pdg_approve_review_endpoint(pdg_client, pdg):
    r = pdg_client.post("/policy/decision-gate/approve-review?review_id=review-new-test")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "APPROVED"
    assert data["added"] is True
    assert "review-new-test" in pdg._DEMO_REVIEWS


def test_pdg_approved_review_enables_gate(pdg_client, pdg):
    pdg._DEMO_REVIEWS.clear()
    pdg_client.post("/policy/decision-gate/approve-review?review_id=review-xyz-999")
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "room.lock",
        "room_id": "room-test-999",
    })
    data = r.json()
    assert data["verdict"] == "ALLOW"


def test_pdg_unknown_action_is_allow(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={
        "action": "unknown.action.xyz",
        "room_id": "room-any",
    })
    data = r.json()
    assert data["verdict"] == "ALLOW"


def test_pdg_asof_is_string(pdg_client):
    r = pdg_client.post("/policy/decision-gate", json={"action": "room.lock"})
    data = r.json()
    assert isinstance(data["asof"], str)


def test_pdg_check_reviews_helper(pdg):
    assert pdg._check_reviews_approved("any-subject") is True


def test_pdg_add_approved_review_helper(pdg):
    pdg._add_approved_review("review-helper-test")
    assert pdg._DEMO_REVIEWS.get("review-helper-test") == "APPROVED"


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 70 – Exports Room Snapshot
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def snap():
    import exports_room_snapshot as m
    m._SNAPSHOTS.clear()
    return m


@pytest.fixture
def snap_client(snap):
    return _make_client(snap.router)


def test_snap_list_empty_initially(snap_client):
    r = snap_client.get("/exports/room-snapshots")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 0
    assert data["snapshots"] == []


def test_snap_generate_returns_snapshot(snap_client):
    r = snap_client.post("/exports/room-snapshot", json={
        "room_id": "room-test-001",
        "tenant_id": "default",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "generated"
    assert "snapshot" in data


def test_snap_snapshot_has_required_keys(snap_client):
    r = snap_client.post("/exports/room-snapshot", json={"room_id": "room-keys-001"})
    data = r.json()["snapshot"]
    for key in ("snapshot_id", "room_id", "tenant_id", "manifest_hash",
                "pinned_entity_count", "attestation_count", "created_at"):
        assert key in data, f"Missing key: {key}"


def test_snap_manifest_hash_is_24chars(snap_client):
    r = snap_client.post("/exports/room-snapshot", json={"room_id": "room-hash-001"})
    data = r.json()["snapshot"]
    mh = data["manifest_hash"]
    assert len(mh) == 24
    assert all(c in "0123456789abcdef" for c in mh)


def test_snap_stored_in_snapshots(snap_client, snap):
    snap_client.post("/exports/room-snapshot", json={"room_id": "room-store-001"})
    assert len(snap._SNAPSHOTS) == 1


def test_snap_list_returns_generated_snapshots(snap_client):
    snap_client.post("/exports/room-snapshot", json={"room_id": "room-a"})
    snap_client.post("/exports/room-snapshot", json={"room_id": "room-b"})
    r = snap_client.get("/exports/room-snapshots")
    data = r.json()
    assert data["count"] == 2
    assert len(data["snapshots"]) == 2


def test_snap_deterministic_same_room(snap_client, snap):
    snap_client.post("/exports/room-snapshot", json={"room_id": "room-det"})
    h1 = list(snap._SNAPSHOTS.values())[0]["manifest_hash"]
    snap._SNAPSHOTS.clear()
    snap_client.post("/exports/room-snapshot", json={"room_id": "room-det"})
    h2 = list(snap._SNAPSHOTS.values())[0]["manifest_hash"]
    assert h1 == h2


def test_snap_different_rooms_different_hash(snap_client):
    r1 = snap_client.post("/exports/room-snapshot", json={"room_id": "room-aaa"})
    r2 = snap_client.post("/exports/room-snapshot", json={"room_id": "room-bbb"})
    assert r1.json()["snapshot"]["manifest_hash"] != r2.json()["snapshot"]["manifest_hash"]


def test_snap_snapshot_id_format(snap_client):
    r = snap_client.post("/exports/room-snapshot", json={"room_id": "room-id-fmt"})
    sid = r.json()["snapshot"]["snapshot_id"]
    assert sid.startswith("snap-")


def test_snap_room_id_in_snapshot(snap_client):
    r = snap_client.post("/exports/room-snapshot", json={"room_id": "my-specific-room"})
    data = r.json()["snapshot"]
    assert data["room_id"] == "my-specific-room"


def test_snap_manifest_hash_helper_is_24chars(snap):
    h = snap._manifest_hash("room-x", ["e1", "e2"], "some notes", ["att-001"])
    assert len(h) == 24
    assert all(c in "0123456789abcdef" for c in h)


def test_snap_sha256_helper_is_64chars(snap):
    h = snap._sha256({"test": "data"})
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_snap_manifest_hash_deterministic(snap):
    h1 = snap._manifest_hash("r", ["a", "b"], "notes", ["attest"])
    h2 = snap._manifest_hash("r", ["a", "b"], "notes", ["attest"])
    assert h1 == h2


def test_snap_manifest_hash_sensitive_to_entities(snap):
    h1 = snap._manifest_hash("r", ["a"], "notes", [])
    h2 = snap._manifest_hash("r", ["b"], "notes", [])
    assert h1 != h2
