"""
mcp_tools_v2.py (v5.59.0 — Depth Wave)

MCP Tools v2: deterministic DEMO tool surface callable via POST /mcp/v2/tools/call.

Tools:
  ingest_dataset, create_scenario, execute_run, replay_run,
  request_review, approve_review, export_packet,
  run_eval

All tools:
  - require no external API keys
  - produce deterministic outputs in DEMO mode
  - emit audit entries + attestations

Endpoints:
  GET  /mcp/v2/tools                  — list tools (stable ordering)
  POST /mcp/v2/tools/call             — call a tool
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

router = APIRouter(prefix="/mcp/v2", tags=["mcp-v2"])

# ── Audit log in-memory ────────────────────────────────────────────────────────

MCP_AUDIT_LOG: List[Dict[str, Any]] = []


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _log(tool: str, inputs: Dict, result: Dict) -> None:
    entry = {
        "step": len(MCP_AUDIT_LOG) + 1,
        "tool": tool,
        "inputs": inputs,
        "result_hash": _sha(result)[:16],
        "timestamp": ASOF,
    }
    MCP_AUDIT_LOG.append(entry)


# ── Tool definitions ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "ingest_dataset",
        "description": "Ingest a portfolio dataset and return sha256 hash",
        "params": {
            "name": "string",
            "kind": "portfolio|rates_curve|stress_preset",
            "payload": "object",
            "created_by": "string",
        },
        "returns": "dataset",
    },
    {
        "name": "create_scenario",
        "description": "Create a named stress/whatif scenario",
        "params": {
            "name": "string",
            "kind": "stress|whatif|shock_ladder",
            "payload": "object",
            "created_by": "string",
        },
        "returns": "scenario",
    },
    {
        "name": "execute_run",
        "description": "Execute a scenario run and return output_hash",
        "params": {"scenario_id": "string", "triggered_by": "string"},
        "returns": "run",
    },
    {
        "name": "replay_run",
        "description": "Replay a scenario run and verify output_hash matches",
        "params": {"scenario_id": "string", "triggered_by": "string"},
        "returns": "run",
    },
    {
        "name": "request_review",
        "description": "Open a review in DRAFT state for an entity",
        "params": {
            "subject_type": "dataset|scenario|policy_check",
            "subject_id": "string",
            "created_by": "string",
            "notes": "string",
        },
        "returns": "review",
    },
    {
        "name": "approve_review",
        "description": "Move review through IN_REVIEW → APPROVED with decision",
        "params": {
            "review_id": "string",
            "submitted_by": "string",
            "decided_by": "string",
            "decision": "APPROVE|REJECT",
            "rationale": "string",
        },
        "returns": "review",
    },
    {
        "name": "export_packet",
        "description": "Generate a verifiable decision packet with manifest_hash",
        "params": {
            "subject_type": "string",
            "subject_id": "string",
            "requested_by": "string",
        },
        "returns": "packet",
    },
    {
        "name": "run_eval",
        "description": "Run calibration/drift/stability eval on a set of runs",
        "params": {"run_ids": "array[string]"},
        "returns": "eval",
    },
]


def _call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call. Each is deterministic."""

    if tool_name == "ingest_dataset":
        from datasets import ingest_dataset, DATASET_STORE
        tenant = params.get("tenant_id", "demo-tenant")
        ds, errors = ingest_dataset(
            tenant,
            params.get("kind", "portfolio"),
            params.get("name", "MCP Dataset"),
            params.get("payload", {"positions": [
                {"ticker": "AAPL", "quantity": 100, "cost_basis": 178.5},
                {"ticker": "MSFT", "quantity": 50,  "cost_basis": 415.0},
            ]}),
            params.get("created_by", "mcp@demo"),
        )
        if errors:
            raise HTTPException(status_code=422, detail=str(errors))
        return {"dataset": ds}

    elif tool_name == "create_scenario":
        from scenarios_v2 import create_scenario
        sc = create_scenario(
            tenant_id=params.get("tenant_id", "demo-tenant"),
            name=params.get("name", "MCP Scenario"),
            kind=params.get("kind", "stress"),
            payload=params.get("payload", {"shock_pct": 0.20, "apply_to": ["equity"]}),
            created_by=params.get("created_by", "mcp@demo"),
        )
        return {"scenario": sc}

    elif tool_name == "execute_run":
        from scenarios_v2 import run_scenario
        run = run_scenario(
            scenario_id=params["scenario_id"],
            triggered_by=params.get("triggered_by", "mcp@demo"),
        )
        # Compute outcome
        try:
            from run_outcomes import get_or_create_outcome
            from scenarios_v2 import SCENARIO_STORE
            sc = SCENARIO_STORE.get(params["scenario_id"], {})
            outcome = get_or_create_outcome(
                run_id=run["run_id"],
                scenario_id=params["scenario_id"],
                kind=sc.get("kind", "stress"),
                output_hash=run.get("output_hash", run["run_id"]),
            )
            run["outcome"] = outcome
        except Exception:
            pass
        return {"run": run}

    elif tool_name == "replay_run":
        from scenarios_v2 import replay_scenario
        run = replay_scenario(
            scenario_id=params["scenario_id"],
            triggered_by=params.get("triggered_by", "mcp@demo"),
        )
        return {"run": run}

    elif tool_name == "request_review":
        from reviews import create_review
        rv = create_review(
            tenant_id=params.get("tenant_id", "demo-tenant"),
            subject_type=params.get("subject_type", "dataset"),
            subject_id=params["subject_id"],
            created_by=params.get("created_by", "mcp@demo"),
            notes=params.get("notes", "MCP-created review"),
        )
        return {"review": rv}

    elif tool_name == "approve_review":
        from reviews import submit_review, decide_review
        rv = submit_review(
            review_id=params["review_id"],
            submitted_by=params.get("submitted_by", "mcp@demo"),
        )
        rv = decide_review(
            review_id=params["review_id"],
            decided_by=params.get("decided_by", "mcp@demo"),
            decision=params.get("decision", "APPROVE"),
            rationale=params.get("rationale", "MCP auto-approval"),
        )
        return {"review": rv}

    elif tool_name == "export_packet":
        from decision_packet import generate_decision_packet
        pkt = generate_decision_packet(
            tenant_id=params.get("tenant_id", "demo-tenant"),
            subject_type=params.get("subject_type", "dataset"),
            subject_id=params["subject_id"],
            requested_by=params.get("requested_by", "mcp@demo"),
        )
        return {"packet": pkt}

    elif tool_name == "run_eval":
        from eval_harness_v3 import _eval_run_ids, EVAL_STORE
        run_ids = params.get("run_ids", [])
        if not run_ids:
            raise HTTPException(status_code=422, detail="run_ids required")
        ev = _eval_run_ids(run_ids)
        EVAL_STORE[ev["eval_id"]] = ev
        return {"eval": ev}

    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")


# ── Pydantic ───────────────────────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    tool: str
    params: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    tool: str
    result: Dict[str, Any]
    audit_entry: Dict[str, Any]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/tools")
def list_mcp_v2_tools():
    return {"tools": TOOLS, "count": len(TOOLS)}


@router.post("/tools/call", response_model=ToolCallResponse)
def call_mcp_v2_tool(body: ToolCallRequest):
    result = _call_tool(body.tool, body.params)
    audit = {
        "step": len(MCP_AUDIT_LOG) + 1,
        "tool": body.tool,
        "params_hash": _sha(body.params)[:16],
        "result_hash": _sha(result)[:16],
        "timestamp": ASOF,
    }
    MCP_AUDIT_LOG.append(audit)
    return {"tool": body.tool, "result": result, "audit_entry": audit}


@router.get("/audit")
def get_mcp_v2_audit():
    return {"entries": MCP_AUDIT_LOG, "total": len(MCP_AUDIT_LOG)}
