"""Tests for Incident Drills (Wave 27, v4.54-v4.57)"""
import pytest
from incident_drills import (
    reset_drills, list_scenarios, run_drill, get_run, build_incident_pack,
)


@pytest.fixture(autouse=True)
def clean():
    reset_drills()
    yield
    reset_drills()


def test_list_scenarios():
    scenarios = list_scenarios()
    assert len(scenarios) == 4
    ids = {s["id"] for s in scenarios}
    assert ids == {"api_latency_spike", "db_lock_contention", "storage_partial_outage", "auth_token_fail"}


def test_scenario_fields():
    for s in list_scenarios():
        assert s["id"]
        assert s["name"]
        assert s["category"]
        assert s["severity"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def test_run_api_latency():
    run = run_drill("api_latency_spike", {})
    assert run["scenario_id"] == "api_latency_spike"
    assert run["status"] == "completed"
    assert run["severity"] == "HIGH"
    phases = {s["phase"] for s in run["timeline"]}
    assert phases == {"inject", "detect", "remediate", "verify"}


def test_run_db_lock():
    run = run_drill("db_lock_contention", {})
    assert run["status"] == "completed"
    assert run["severity"] == "CRITICAL"
    assert run["outputs_hash"]


def test_run_storage_outage():
    run = run_drill("storage_partial_outage", {})
    assert run["status"] == "completed"
    assert run["metrics"]["slo_met"] is True


def test_run_auth_fail():
    run = run_drill("auth_token_fail", {})
    assert run["status"] == "completed"
    assert run["severity"] == "CRITICAL"


def test_run_not_found():
    with pytest.raises(ValueError, match="not found"):
        run_drill("nonexistent_scenario", {})


def test_get_run():
    run = run_drill("api_latency_spike", {})
    fetched = get_run(run["run_id"])
    assert fetched["run_id"] == run["run_id"]


def test_get_run_not_found():
    with pytest.raises(ValueError, match="not found"):
        get_run("nonexistent_run_id")


def test_metrics_structure():
    run = run_drill("api_latency_spike", {})
    m = run["metrics"]
    assert "ttr_s" in m
    assert "ttd_s" in m
    assert "ttm_s" in m
    assert "slo_met" in m
    assert "slo_target" in m


def test_timeline_ordering():
    run = run_drill("api_latency_spike", {})
    t_offsets = [s["t_offset_s"] for s in run["timeline"]]
    assert t_offsets == sorted(t_offsets)


def test_export_pack():
    run = run_drill("db_lock_contention", {})
    pack = build_incident_pack(run["run_id"])
    file_names = {f["name"] for f in pack["files"]}
    assert file_names == {"runbook.json", "timeline.json", "metrics.json"}
    assert pack["pack_hash"]
    assert pack["output_hash"]


def test_export_pack_not_found():
    with pytest.raises(ValueError, match="not found"):
        build_incident_pack("nonexistent")


def test_determinism():
    run1 = run_drill("api_latency_spike", {})
    reset_drills()
    run2 = run_drill("api_latency_spike", {})
    assert run1["run_id"] == run2["run_id"]
    assert run1["outputs_hash"] == run2["outputs_hash"]


def test_all_scenarios_runnable():
    for scenario_id in ["api_latency_spike", "db_lock_contention", "storage_partial_outage", "auth_token_fail"]:
        reset_drills()
        run = run_drill(scenario_id, {})
        assert run["status"] == "completed"
        assert run["audit_chain_head_hash"]
