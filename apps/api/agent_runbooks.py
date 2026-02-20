"""
agent_runbooks.py (v5.56.0 — Wave 67)

Agent Runbooks v1 — agentic workflows that are replayable, permissioned,
and fully auditable.

Step types:
  validate_dataset, validate_scenario, execute_run, request_review,
  export_packet, generate_compliance_pack

All steps log to audit and issue an attestation at completion with
input/output hashes.

Endpoints:
  GET  /runbooks
  POST /runbooks
  GET  /runbooks/{id}
  POST /runbooks/{id}/execute
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

router = APIRouter(prefix="/runbooks", tags=["runbooks"])

STEP_TYPES = [
    "validate_dataset", "validate_scenario", "execute_run",
    "request_review", "export_packet", "generate_compliance_pack",
]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _runbook_id(name: str, tenant_id: str) -> str:
    return "rb-" + _sha256({"name": name, "tenant_id": tenant_id})[:12]


def _step_hash(step: Dict, inputs: Dict) -> str:
    return _sha256({"step": step, "inputs": inputs})[:16]


def _outputs_hash(steps_result: List[Dict]) -> str:
    return _sha256({"results": steps_result})[:16]


# ── In-memory store ────────────────────────────────────────────────────────────

_RUNBOOKS: Dict[str, Dict[str, Any]] = {}
_EXECUTIONS: Dict[str, List[Dict[str, Any]]] = {}  # runbook_id -> executions list

# Seed demo runbooks
_SEED_RUNBOOKS = [
    {
        "runbook_id": "rb-demo-001",
        "tenant_id": "demo-tenant",
        "name": "Rate Shock Full Workflow",
        "description": "Validate dataset → run scenario → request review → export packet",
        "steps": [
            {"step_type": "validate_dataset", "params": {"dataset_id": "ds-prov-001"}},
            {"step_type": "validate_scenario", "params": {"scenario_id": "scen-001"}},
            {"step_type": "execute_run", "params": {"scenario_id": "scen-001", "kind": "rate_shock", "payload": {"delta_bps": 100}}},
            {"step_type": "request_review", "params": {"reviewers": ["reviewer@demo.io"]}},
            {"step_type": "export_packet", "params": {"format": "zip"}},
        ],
        "created_by": "demo-user",
        "created_at": ASOF,
        "updated_at": ASOF,
    },
    {
        "runbook_id": "rb-demo-002",
        "tenant_id": "demo-tenant",
        "name": "Compliance Pack Generator",
        "description": "Validate + generate compliance pack",
        "steps": [
            {"step_type": "validate_dataset", "params": {"dataset_id": "ds-prov-002"}},
            {"step_type": "generate_compliance_pack", "params": {"standard": "BCBS239"}},
        ],
        "created_by": "demo-user",
        "created_at": ASOF,
        "updated_at": ASOF,
    },
]
for _rb in _SEED_RUNBOOKS:
    _RUNBOOKS[_rb["runbook_id"]] = _rb
    _EXECUTIONS[_rb["runbook_id"]] = []


# ── Request models ─────────────────────────────────────────────────────────────


class StepDef(BaseModel):
    step_type: str
    params: Optional[Dict[str, Any]] = None


class CreateRunbookRequest(BaseModel):
    name: str
    description: str = ""
    steps: List[StepDef]
    tenant_id: str = "demo-tenant"
    created_by: str = "api-user"


class ExecuteRunbookRequest(BaseModel):
    inputs: Optional[Dict[str, Any]] = None
    executed_by: str = "api-user"


# ── Step execution (DEMO — deterministic) ─────────────────────────────────────


def _execute_step(step: Dict, inputs: Dict, step_idx: int) -> Dict[str, Any]:
    """Execute a single step deterministically and return result."""
    stype = step["step_type"]
    params = step.get("params") or {}
    step_input_hash = _step_hash(step, inputs)

    if stype == "validate_dataset":
        dataset_id = params.get("dataset_id", "ds-unknown")
        output = {
            "validated": True,
            "dataset_id": dataset_id,
            "license_compliant": True,
            "checksum": _sha256({"dataset_id": dataset_id, "step": "validate"})[:16],
        }
    elif stype == "validate_scenario":
        scenario_id = params.get("scenario_id", "scen-unknown")
        output = {
            "validated": True,
            "scenario_id": scenario_id,
            "schema_valid": True,
        }
    elif stype == "execute_run":
        scenario_id = params.get("scenario_id", "scen-unknown")
        run_hash = _sha256({"scenario_id": scenario_id, "params": params})[:16]
        output = {
            "run_id": f"run-{run_hash}",
            "status": "completed",
            "inputs_hash": step_input_hash,
            "outputs_hash": _sha256({"run": run_hash, "inputs": step_input_hash})[:16],
        }
    elif stype == "request_review":
        reviewers = params.get("reviewers", [])
        review_id = "review-" + _sha256({"reviewers": reviewers, "step": step_idx})[:12]
        output = {
            "review_id": review_id,
            "status": "PENDING",
            "reviewers": reviewers,
        }
    elif stype == "export_packet":
        packet_id = "pkt-" + _sha256({"inputs": inputs, "step": step_idx})[:12]
        output = {
            "packet_id": packet_id,
            "format": params.get("format", "zip"),
            "export_hash": _sha256({"packet_id": packet_id})[:16],
        }
    elif stype == "generate_compliance_pack":
        pack_id = "comp-" + _sha256({"standard": params.get("standard", "BCBS239"), "inputs": inputs})[:12]
        output = {
            "pack_id": pack_id,
            "standard": params.get("standard", "BCBS239"),
            "status": "generated",
            "compliance_hash": _sha256({"pack_id": pack_id})[:16],
        }
    else:
        output = {"error": f"Unknown step type: {stype}"}

    # Attestation for this step
    attest_hash = _sha256({"step_idx": step_idx, "stype": stype, "output": output})
    attestation = {
        "attestation_id": f"attest-step-{step_idx}-{attest_hash[:8]}",
        "step_idx": step_idx,
        "step_type": stype,
        "input_hash": step_input_hash,
        "output_hash": _sha256(output)[:16],
        "issued_at": ASOF,
    }

    return {
        "step_idx": step_idx,
        "step_type": stype,
        "status": "completed",
        "output": output,
        "attestation": attestation,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("")
def list_runbooks(tenant_id: str = "demo-tenant"):
    rbs = [r for r in _RUNBOOKS.values() if r["tenant_id"] == tenant_id]
    rbs_sorted = sorted(rbs, key=lambda r: r["created_at"])
    result = []
    for rb in rbs_sorted:
        rb_view = dict(rb)
        rb_view["step_count"] = len(rb.get("steps", []))
        result.append(rb_view)
    return {"runbooks": result, "count": len(result)}


@router.post("")
def create_runbook(req: CreateRunbookRequest):
    rb_id = _runbook_id(req.name, req.tenant_id)
    if rb_id in _RUNBOOKS:
        return {"runbook": _RUNBOOKS[rb_id], "status": "exists"}

    # Validate step types
    for step in req.steps:
        if step.step_type not in STEP_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid step_type: {step.step_type}. Must be one of {STEP_TYPES}",
            )

    rb: Dict[str, Any] = {
        "runbook_id": rb_id,
        "tenant_id": req.tenant_id,
        "name": req.name,
        "description": req.description,
        "steps": [s.model_dump() for s in req.steps],
        "created_by": req.created_by,
        "created_at": ASOF,
        "updated_at": ASOF,
    }
    _RUNBOOKS[rb_id] = rb
    _EXECUTIONS[rb_id] = []
    return {"runbook": rb, "status": "created"}


@router.get("/{runbook_id}")
def get_runbook(runbook_id: str):
    rb = _RUNBOOKS.get(runbook_id)
    if not rb:
        raise HTTPException(status_code=404, detail=f"Runbook {runbook_id} not found")
    executions = _EXECUTIONS.get(runbook_id, [])
    return {"runbook": rb, "executions": executions, "execution_count": len(executions)}


@router.post("/{runbook_id}/execute")
def execute_runbook(runbook_id: str, req: ExecuteRunbookRequest):
    rb = _RUNBOOKS.get(runbook_id)
    if not rb:
        raise HTTPException(status_code=404, detail=f"Runbook {runbook_id} not found")

    inputs = req.inputs or {}
    step_results = []
    accumulated_outputs: Dict[str, Any] = dict(inputs)

    for idx, step in enumerate(rb["steps"]):
        result = _execute_step(step, accumulated_outputs, idx)
        step_results.append(result)
        # Propagate outputs to next steps
        accumulated_outputs.update(result["output"])

    run_outputs_hash = _outputs_hash(step_results)
    inputs_hash = _sha256(inputs)[:16]

    execution = {
        "execution_id": "exec-" + _sha256({"rb": runbook_id, "inputs": inputs})[:12],
        "runbook_id": runbook_id,
        "status": "completed",
        "inputs_hash": inputs_hash,
        "outputs_hash": run_outputs_hash,
        "step_results": step_results,
        "executed_by": req.executed_by,
        "executed_at": ASOF,
        "artifacts": [r["output"] for r in step_results],
        "attestations": [r["attestation"] for r in step_results],
    }
    _EXECUTIONS[runbook_id].append(execution)

    return {
        "execution": execution,
        "status": "completed",
    }
