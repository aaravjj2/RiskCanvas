"""
Tests for v4.14.0-v4.16.0 Scenario DSL + Diff + Pack (Wave 16)
Verifies: id determinism, validation, diff stability, pack hashing.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_store():
    """Reset scenario store before each test."""
    from scenario_dsl import reset_scenario_store
    reset_scenario_store()
    yield
    reset_scenario_store()


SAMPLE_SCENARIO = {
    "name": "Stress Test Q1",
    "description": "Tech sell-off scenario",
    "tags": ["stress", "tech"],
    "spot_shocks": [
        {"symbols": ["AAPL", "MSFT"], "shock_type": "relative", "shock_value": -0.10}
    ],
    "vol_shocks": [
        {"symbols": [], "shock_type": "relative", "shock_value": 0.20}
    ],
    "rates_shocks": [],
    "curve_node_shocks": [],
    "parameters": {"horizon": "1W"},
}

SAMPLE_SCENARIO_B = {
    "name": "Rates Shock",
    "description": "Parallel shift scenario",
    "tags": ["rates"],
    "spot_shocks": [],
    "vol_shocks": [],
    "rates_shocks": [
        {"curve_id": "USD_SOFR", "shock_type": "parallel", "shock_bps": 50.0}
    ],
    "curve_node_shocks": [],
    "parameters": {},
}


def test_scenario_id_determinism():
    """Same DSL → same scenario_id."""
    from scenario_dsl import store_scenario

    r1 = store_scenario(SAMPLE_SCENARIO)
    r2 = store_scenario(SAMPLE_SCENARIO)
    assert r1["scenario_id"] == r2["scenario_id"]


def test_scenario_id_content_based():
    """Different DSL → different scenario_id."""
    from scenario_dsl import _make_scenario_id, _canonical_scenario

    id_a = _make_scenario_id(_canonical_scenario(SAMPLE_SCENARIO))
    id_b = _make_scenario_id(_canonical_scenario(SAMPLE_SCENARIO_B))
    assert id_a != id_b


def test_scenario_validation_valid():
    """Valid DSL passes validation."""
    from scenario_dsl import validate_scenario_dsl

    errors = validate_scenario_dsl(SAMPLE_SCENARIO)
    assert errors == []


def test_scenario_validation_missing_name():
    """Empty name fails validation."""
    from scenario_dsl import validate_scenario_dsl

    bad = {**SAMPLE_SCENARIO, "name": ""}
    errors = validate_scenario_dsl(bad)
    assert any("name" in e for e in errors)


def test_scenario_validation_bad_shock_type():
    """Invalid shock_type fails validation."""
    from scenario_dsl import validate_scenario_dsl

    bad = {
        **SAMPLE_SCENARIO,
        "spot_shocks": [{"symbols": [], "shock_type": "invalid_type", "shock_value": -0.1}],
    }
    errors = validate_scenario_dsl(bad)
    assert any("shock_type" in e for e in errors)


def test_scenario_validation_deterministic():
    """Same invalid DSL → same errors (stable ordering)."""
    from scenario_dsl import validate_scenario_dsl

    bad = {**SAMPLE_SCENARIO, "name": "", "spot_shocks": [{"shock_type": "bad", "shock_value": 1}]}
    e1 = validate_scenario_dsl(bad)
    e2 = validate_scenario_dsl(bad)
    assert e1 == e2


def test_scenario_store_and_retrieve():
    """Store then retrieve returns same record."""
    from scenario_dsl import store_scenario, get_scenario

    record = store_scenario(SAMPLE_SCENARIO)
    sid = record["scenario_id"]
    retrieved = get_scenario(sid)
    assert retrieved is not None
    assert retrieved["scenario_id"] == sid
    assert retrieved["canonical"]["name"] == SAMPLE_SCENARIO["name"]


def test_scenario_list_ordered():
    """Listed scenarios are in stable id order."""
    from scenario_dsl import store_scenario, list_scenarios

    store_scenario(SAMPLE_SCENARIO)
    store_scenario(SAMPLE_SCENARIO_B)
    items = list_scenarios()
    ids = [i["scenario_id"] for i in items]
    assert ids == sorted(ids)


def test_scenario_diff_deterministic():
    """Diff between two scenarios is deterministic."""
    from scenario_dsl import store_scenario, diff_scenarios

    ra = store_scenario(SAMPLE_SCENARIO)
    rb = store_scenario(SAMPLE_SCENARIO_B)

    d1 = diff_scenarios(ra["scenario_id"], rb["scenario_id"])
    d2 = diff_scenarios(ra["scenario_id"], rb["scenario_id"])
    assert d1["output_hash"] == d2["output_hash"]


def test_scenario_diff_detects_changes():
    """Diff detects name change."""
    from scenario_dsl import store_scenario, diff_scenarios

    ra = store_scenario(SAMPLE_SCENARIO)
    rb = store_scenario(SAMPLE_SCENARIO_B)
    diff = diff_scenarios(ra["scenario_id"], rb["scenario_id"])
    assert diff["change_count"] > 0


def test_scenario_diff_same_is_empty():
    """Diff of same scenario has 0 changes."""
    from scenario_dsl import store_scenario, diff_scenarios

    ra = store_scenario(SAMPLE_SCENARIO)
    diff = diff_scenarios(ra["scenario_id"], ra["scenario_id"])
    assert diff["change_count"] == 0


def test_scenario_pack_determinism():
    """Pack hash is deterministic."""
    from scenario_dsl import store_scenario, build_scenario_pack

    ra = store_scenario(SAMPLE_SCENARIO)
    rb = store_scenario(SAMPLE_SCENARIO_B)
    ids = [ra["scenario_id"], rb["scenario_id"]]

    p1 = build_scenario_pack(ids)
    p2 = build_scenario_pack(ids)
    assert p1["manifest"]["manifest_hash"] == p2["manifest"]["manifest_hash"]


def test_scenario_pack_stable_ordering():
    """Pack order is stable regardless of input order."""
    from scenario_dsl import store_scenario, build_scenario_pack

    ra = store_scenario(SAMPLE_SCENARIO)
    rb = store_scenario(SAMPLE_SCENARIO_B)

    p1 = build_scenario_pack([ra["scenario_id"], rb["scenario_id"]])
    p2 = build_scenario_pack([rb["scenario_id"], ra["scenario_id"]])  # reversed
    assert p1["manifest"]["manifest_hash"] == p2["manifest"]["manifest_hash"]


def test_scenario_pack_missing_raises():
    """Pack with missing ID raises ValueError."""
    from scenario_dsl import build_scenario_pack

    with pytest.raises(ValueError, match="not found"):
        build_scenario_pack(["nonexistent_id"])


def test_scenario_api_validate():
    """Validate API returns errors for invalid DSL."""
    from main import app

    client = TestClient(app)
    payload = {"scenario": {**SAMPLE_SCENARIO, "name": ""}}
    resp = client.post("/scenarios/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert data["error_count"] > 0


def test_scenario_api_create():
    """Create API stores scenario and returns id."""
    from main import app

    client = TestClient(app)
    payload = {"scenario": SAMPLE_SCENARIO}
    resp = client.post("/scenarios/create", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "scenario_id" in data
    assert len(data["scenario_id"]) == 32


def test_scenario_api_list():
    """List API returns stored scenarios."""
    from main import app

    client = TestClient(app)
    client.post("/scenarios/create", json={"scenario": SAMPLE_SCENARIO})
    resp = client.get("/scenarios/list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 1


def test_scenario_api_diff():
    """Diff API works between two created scenarios."""
    from main import app

    client = TestClient(app)
    ra = client.post("/scenarios/create", json={"scenario": SAMPLE_SCENARIO}).json()
    rb = client.post("/scenarios/create", json={"scenario": SAMPLE_SCENARIO_B}).json()

    resp = client.post("/scenarios/diff", json={"a_id": ra["scenario_id"], "b_id": rb["scenario_id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "change_count" in data
    assert "output_hash" in data


def test_scenario_api_export_pack():
    """Export pack API returns manifest hash."""
    from main import app

    client = TestClient(app)
    ra = client.post("/scenarios/create", json={"scenario": SAMPLE_SCENARIO}).json()
    rb = client.post("/scenarios/create", json={"scenario": SAMPLE_SCENARIO_B}).json()

    resp = client.post(
        "/exports/scenario-pack",
        json={"scenario_ids": [ra["scenario_id"], rb["scenario_id"]]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "pack_hash" in data
    assert data["manifest"]["manifest_hash"] is not None
