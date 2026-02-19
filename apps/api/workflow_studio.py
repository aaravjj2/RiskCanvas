"""
RiskCanvas v4.62.0-v4.65.0 — Workflow Studio (Wave 29)

Provides:
- DSL v2: trigger, steps (parallel|sequential|condition), outputs
- Deterministic generator from user spec → workflow YAML-like dict
- Activator: transition draft → active (immutable once active)
- Simulator: dry-run execution trace — each step with status/output_hash
- In-memory runs store
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
VERSION = "v4.65.0"
ASOF = "2026-02-19T10:30:00Z"


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _compact(data: Any) -> str:
    return _sha(data)[:16]


def _chain_head() -> str:
    return "workflow_chain_d4e5f6a7"


# ─────────────────── DSL Templates ───────────────────────────────────────────

_STEP_TEMPLATES = {
    "run_tests": {"type": "sequential", "action": "run_tests", "outputs": ["test_report", "coverage_pct"], "can_fail": False},
    "security_scan": {"type": "sequential", "action": "security_scan", "outputs": ["vuln_count", "scan_report"], "can_fail": False},
    "build_image": {"type": "sequential", "action": "build_image", "outputs": ["image_tag", "image_hash"], "can_fail": False},
    "deploy_staging": {"type": "sequential", "action": "deploy_to_env", "params": {"env": "staging"}, "outputs": ["deploy_url"], "can_fail": False},
    "e2e_tests": {"type": "sequential", "action": "run_e2e", "outputs": ["e2e_pass_rate"], "can_fail": False},
    "readiness_check": {"type": "condition", "action": "evaluate_readiness", "condition": "score >= 90", "outputs": ["verdict"], "can_fail": False},
    "deploy_production": {"type": "sequential", "action": "deploy_to_env", "params": {"env": "production"}, "outputs": ["deploy_url", "version"], "can_fail": False},
    "notify_slack": {"type": "sequential", "action": "send_notification", "params": {"channel": "#deployments"}, "outputs": ["notification_id"], "can_fail": True},
    "create_release": {"type": "sequential", "action": "create_github_release", "outputs": ["release_url"], "can_fail": True},
    "policy_check": {"type": "condition", "action": "check_policy", "condition": "all_gates_pass", "outputs": ["policy_result"], "can_fail": False},
}


def _generate_workflow(spec: Dict[str, Any]) -> Dict[str, Any]:
    name = spec.get("name", "generated-workflow")
    trigger_type = spec.get("trigger", "push")
    requested_steps = spec.get("steps", ["run_tests", "build_image", "deploy_staging"])
    description = spec.get("description", f"Auto-generated workflow: {name}")

    steps_out = []
    for i, step_name in enumerate(requested_steps):
        tpl = _STEP_TEMPLATES.get(step_name, {
            "type": "sequential", "action": step_name, "outputs": ["result"], "can_fail": False
        })
        steps_out.append({
            "id": f"step_{i+1}",
            "name": step_name,
            "order": i + 1,
            "type": tpl["type"],
            "action": tpl["action"],
            "params": tpl.get("params", {}),
            "outputs": tpl["outputs"],
            "can_fail": tpl.get("can_fail", False),
            "condition": tpl.get("condition"),
        })

    trigger = {
        "type": trigger_type,
        "branches": spec.get("branches", ["main"]),
        "events": spec.get("events", [trigger_type]),
    }

    canonical = {"name": name, "trigger": trigger, "steps": steps_out}
    wf_id = _sha(canonical)[:24]

    return {
        "workflow_id": wf_id,
        "name": name,
        "description": description,
        "trigger": trigger,
        "steps": steps_out,
        "step_count": len(steps_out),
        "status": "draft",
        "dsl_version": "v2",
        "spec_hash": _sha(spec),
        "output_hash": _sha(canonical),
        "audit_chain_head_hash": _chain_head(),
        "created_at": ASOF,
    }


def _simulate_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
    sim_steps = []
    for step in workflow["steps"]:
        payload = {"workflow_id": workflow["workflow_id"], "step": step["id"]}
        if step.get("condition") and not DEMO_MODE:
            result_status = "passed"
        else:
            result_status = "passed"
        outputs = {o: _compact({"wf": workflow["workflow_id"], "step": step["id"], "out": o}) for o in step["outputs"]}
        sim_steps.append({
            "step_id": step["id"],
            "step_name": step["name"],
            "status": result_status,
            "outputs": outputs,
            "outputs_hash": _compact(payload),
            "t_offset_s": (step["order"] - 1) * 30,
        })

    run_payload = {"workflow_id": workflow["workflow_id"], "sim_steps": sim_steps}
    run_id = _sha(run_payload)[:24]

    return {
        "run_id": run_id,
        "workflow_id": workflow["workflow_id"],
        "workflow_name": workflow["name"],
        "simulation": True,
        "steps": sim_steps,
        "step_count": len(sim_steps),
        "passed": sum(1 for s in sim_steps if s["status"] == "passed"),
        "failed": sum(1 for s in sim_steps if s["status"] == "failed"),
        "status": "completed",
        "outputs_hash": _sha(run_payload),
        "audit_chain_head_hash": _chain_head(),
        "simulated_at": ASOF,
    }


# ─────────────────── In-memory store ─────────────────────────────────────────

_WORKFLOWS: Dict[str, Dict[str, Any]] = {}
_WORKFLOW_RUNS: Dict[str, Dict[str, Any]] = {}


def reset_workflows() -> None:
    _WORKFLOWS.clear()
    _WORKFLOW_RUNS.clear()


# ─────────────────── Public API ───────────────────────────────────────────────

def generate_workflow(spec: Dict[str, Any]) -> Dict[str, Any]:
    wf = _generate_workflow(spec)
    _WORKFLOWS[wf["workflow_id"]] = wf
    return wf


def activate_workflow(workflow_id: str) -> Dict[str, Any]:
    wf = _WORKFLOWS.get(workflow_id)
    if not wf:
        raise ValueError(f"Workflow not found: {workflow_id}")
    if wf["status"] == "active":
        return wf
    updated = {**wf, "status": "active", "activated_at": ASOF,
                "activation_hash": _compact({"id": workflow_id, "action": "activate"})}
    _WORKFLOWS[workflow_id] = updated
    return updated


def list_workflows() -> List[Dict[str, Any]]:
    return [
        {"workflow_id": wf["workflow_id"], "name": wf["name"], "status": wf["status"],
         "step_count": wf["step_count"], "created_at": wf["created_at"]}
        for wf in _WORKFLOWS.values()
    ]


def simulate_workflow(workflow_id: str) -> Dict[str, Any]:
    wf = _WORKFLOWS.get(workflow_id)
    if not wf:
        raise ValueError(f"Workflow not found: {workflow_id}")
    run = _simulate_workflow(wf)
    _WORKFLOW_RUNS[run["run_id"]] = run
    return run


def list_runs(workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
    runs = list(_WORKFLOW_RUNS.values())
    if workflow_id:
        runs = [r for r in runs if r["workflow_id"] == workflow_id]
    return runs


# ─────────────────── Router ──────────────────────────────────────────────────

workflow_studio_router = APIRouter(tags=["workflow_studio"])


class GenerateRequest(BaseModel):
    name: str = Field(default="release-pipeline")
    trigger: str = Field(default="push")
    branches: List[str] = Field(default_factory=lambda: ["main"])
    steps: List[str] = Field(default_factory=lambda: ["run_tests", "security_scan", "build_image", "deploy_staging", "e2e_tests", "readiness_check", "deploy_production"])
    description: str = Field(default="")


class ActivateRequest(BaseModel):
    workflow_id: str


class SimulateRequest(BaseModel):
    workflow_id: str


class ListRunsRequest(BaseModel):
    workflow_id: Optional[str] = None


@workflow_studio_router.post("/workflows/generate")
def api_generate(req: GenerateRequest):
    return generate_workflow(req.dict())


@workflow_studio_router.post("/workflows/activate")
def api_activate(req: ActivateRequest):
    try:
        return activate_workflow(req.workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workflow_studio_router.get("/workflows/list")
def api_list():
    return {"workflows": list_workflows()}


@workflow_studio_router.post("/workflows/simulate")
def api_simulate(req: SimulateRequest):
    try:
        return simulate_workflow(req.workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@workflow_studio_router.get("/workflows/runs")
def api_runs(workflow_id: Optional[str] = None):
    return {"runs": list_runs(workflow_id)}
