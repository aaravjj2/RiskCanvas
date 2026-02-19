"""Tests for Workflow Studio (Wave 29, v4.62-v4.65)"""
import pytest
from workflow_studio import (
    reset_workflows, generate_workflow, activate_workflow,
    list_workflows, simulate_workflow, list_runs,
)


@pytest.fixture(autouse=True)
def clean():
    reset_workflows()
    yield
    reset_workflows()


_SPEC = {
    "name": "release-pipeline",
    "trigger": "push",
    "branches": ["main"],
    "steps": ["run_tests", "security_scan", "build_image", "deploy_staging", "e2e_tests", "readiness_check", "deploy_production"],
    "description": "Standard release pipeline",
}


def test_generate_workflow():
    wf = generate_workflow(_SPEC)
    assert wf["name"] == "release-pipeline"
    assert wf["status"] == "draft"
    assert wf["step_count"] == 7
    assert wf["dsl_version"] == "v2"
    assert len(wf["workflow_id"]) == 24


def test_generate_workflow_determinism():
    wf1 = generate_workflow(_SPEC)
    reset_workflows()
    wf2 = generate_workflow(_SPEC)
    assert wf1["workflow_id"] == wf2["workflow_id"]
    assert wf1["output_hash"] == wf2["output_hash"]


def test_activate_workflow():
    wf = generate_workflow(_SPEC)
    activated = activate_workflow(wf["workflow_id"])
    assert activated["status"] == "active"
    assert activated["activation_hash"]


def test_activate_not_found():
    with pytest.raises(ValueError, match="not found"):
        activate_workflow("nonexistent_id")


def test_activate_idempotent():
    wf = generate_workflow(_SPEC)
    a1 = activate_workflow(wf["workflow_id"])
    a2 = activate_workflow(wf["workflow_id"])
    assert a1["status"] == "active"
    assert a2["status"] == "active"


def test_list_workflows():
    generate_workflow(_SPEC)
    workflows = list_workflows()
    assert len(workflows) == 1
    assert workflows[0]["name"] == "release-pipeline"


def test_list_workflows_multiple():
    generate_workflow(_SPEC)
    generate_workflow({**_SPEC, "name": "hotfix-pipeline", "steps": ["run_tests", "build_image"]})
    workflows = list_workflows()
    assert len(workflows) == 2


def test_simulate_workflow():
    wf = generate_workflow(_SPEC)
    run = simulate_workflow(wf["workflow_id"])
    assert run["simulation"] is True
    assert run["step_count"] == 7
    assert run["status"] == "completed"
    assert run["passed"] == 7
    assert run["failed"] == 0


def test_simulate_not_found():
    with pytest.raises(ValueError, match="not found"):
        simulate_workflow("nonexistent_id")


def test_simulate_step_fields():
    wf = generate_workflow(_SPEC)
    run = simulate_workflow(wf["workflow_id"])
    for step in run["steps"]:
        assert step["step_id"]
        assert step["step_name"]
        assert step["status"] in ("passed", "failed", "skipped")
        assert "outputs" in step
        assert step["outputs_hash"]


def test_list_runs_empty():
    wf = generate_workflow(_SPEC)
    runs = list_runs(wf["workflow_id"])
    assert runs == []


def test_list_runs_after_simulate():
    wf = generate_workflow(_SPEC)
    run = simulate_workflow(wf["workflow_id"])
    runs = list_runs(wf["workflow_id"])
    assert len(runs) == 1
    assert runs[0]["run_id"] == run["run_id"]


def test_list_runs_global():
    wf = generate_workflow(_SPEC)
    simulate_workflow(wf["workflow_id"])
    simulate_workflow(wf["workflow_id"])
    # Runs may be deduplicated or unique based on content
    all_runs = list_runs()
    assert len(all_runs) >= 1


def test_workflow_step_order():
    wf = generate_workflow(_SPEC)
    run = simulate_workflow(wf["workflow_id"])
    t_offsets = [s["t_offset_s"] for s in run["steps"]]
    assert t_offsets == sorted(t_offsets)


def test_step_outputs_deterministic():
    wf = generate_workflow(_SPEC)
    r1 = simulate_workflow(wf["workflow_id"])
    reset_workflows()
    wf2 = generate_workflow(_SPEC)
    r2 = simulate_workflow(wf2["workflow_id"])
    assert r1["outputs_hash"] == r2["outputs_hash"]
