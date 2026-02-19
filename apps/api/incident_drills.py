"""
RiskCanvas v4.54.0-v4.57.0 — Incident Drills (Wave 27)

Provides:
- 4 scenario templates (api_latency_spike, db_lock_contention, storage_partial_outage, auth_token_fail)
- Runbook engine: deterministic inject → detect → remediate → verify chain
- Run timeline: steps[] with timestamps, outputs_hash per step
- Export: incident-pack (runbook.json + timeline.json + metrics.json)
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
VERSION = "v4.57.0"
ASOF = "2026-02-19T09:30:00Z"


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _compact(data: Any) -> str:
    return _sha(data)[:16]


# ─────────────────── Scenario Fixtures ───────────────────────────────────────

_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "api_latency_spike": {
        "id": "api_latency_spike",
        "name": "API Latency Spike",
        "description": "P99 latency exceeds 2000ms for /pricing endpoints. Simulate sudden CPU contention and connection pool exhaustion.",
        "category": "performance",
        "severity": "HIGH",
        "inject_steps": [
            {"action": "set_cpu_limit", "params": {"limit_pct": 95}},
            {"action": "exhaust_conn_pool", "params": {"pool_size": 0}},
        ],
        "detect_signals": ["latency_p99_ms > 2000", "error_rate_pct > 5"],
        "remediate_steps": [
            {"action": "scale_replicas", "params": {"count": 3}},
            {"action": "restart_unhealthy_pods"},
            {"action": "flush_conn_pool"},
        ],
        "verify_signals": ["latency_p99_ms < 200", "error_rate_pct < 1"],
        "slo_target": {"latency_p99_ms": 200, "error_rate_pct": 1.0},
        "expected_ttd_s": 45,
        "expected_ttm_s": 120,
    },
    "db_lock_contention": {
        "id": "db_lock_contention",
        "name": "DB Lock Contention",
        "description": "Long-running transactions lock key rows in the positions table, causing write timeouts.",
        "category": "database",
        "severity": "CRITICAL",
        "inject_steps": [
            {"action": "start_long_txn", "params": {"table": "positions", "lock_ms": 30000}},
            {"action": "flood_writes", "params": {"txns_per_s": 500}},
        ],
        "detect_signals": ["db_lock_wait_ms > 5000", "txn_timeout_count > 10"],
        "remediate_steps": [
            {"action": "kill_blocking_queries"},
            {"action": "enable_lock_timeout", "params": {"timeout_ms": 1000}},
            {"action": "rerun_failed_txns"},
        ],
        "verify_signals": ["db_lock_wait_ms < 100", "txn_timeout_count == 0"],
        "slo_target": {"db_lock_wait_ms": 100, "txn_timeout_count": 0},
        "expected_ttd_s": 15,
        "expected_ttm_s": 60,
    },
    "storage_partial_outage": {
        "id": "storage_partial_outage",
        "name": "Storage Partial Outage",
        "description": "Object storage returns 503 for 30% of requests. Data ingestion pipeline backs up.",
        "category": "storage",
        "severity": "HIGH",
        "inject_steps": [
            {"action": "set_error_rate", "params": {"service": "object_store", "pct": 30, "code": 503}},
        ],
        "detect_signals": ["storage_error_rate_pct > 10", "ingest_queue_depth > 1000"],
        "remediate_steps": [
            {"action": "switch_to_backup_region"},
            {"action": "drain_ingest_queue"},
            {"action": "replay_failed_writes"},
        ],
        "verify_signals": ["storage_error_rate_pct < 1", "ingest_queue_depth < 100"],
        "slo_target": {"storage_error_rate_pct": 1.0, "ingest_queue_depth": 100},
        "expected_ttd_s": 30,
        "expected_ttm_s": 90,
    },
    "auth_token_fail": {
        "id": "auth_token_fail",
        "name": "Auth Token Validation Failure",
        "description": "JWT signing key rotated without updating all service configs. Auth middleware rejects valid tokens.",
        "category": "security",
        "severity": "CRITICAL",
        "inject_steps": [
            {"action": "rotate_jwt_key", "params": {"propagate": False}},
        ],
        "detect_signals": ["auth_rejection_rate_pct > 50", "401_count > 100"],
        "remediate_steps": [
            {"action": "propagate_new_key_to_all_services"},
            {"action": "issue_short_lived_bridge_tokens"},
            {"action": "drain_stale_sessions"},
        ],
        "verify_signals": ["auth_rejection_rate_pct < 1", "401_count < 5"],
        "slo_target": {"auth_rejection_rate_pct": 1.0, "401_count": 5},
        "expected_ttd_s": 20,
        "expected_ttm_s": 45,
    },
}


def _chain_head() -> str:
    return "drill_chain_b2c3d4e5"


# ─────────────────── Drill Runner ─────────────────────────────────────────────

def _run_drill(scenario_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    sc = _SCENARIOS[scenario_id]
    timeline: List[Dict[str, Any]] = []
    t = 0

    # Phase INJECT
    for step in sc["inject_steps"]:
        payload = {"scenario": scenario_id, "phase": "inject", "step": step, "t": t}
        timeline.append({
            "phase": "inject", "t_offset_s": t, "action": step["action"],
            "params": step.get("params", {}), "status": "done",
            "outputs_hash": _compact(payload),
        })
        t += 5

    # Phase DETECT
    for sig in sc["detect_signals"]:
        payload = {"scenario": scenario_id, "phase": "detect", "signal": sig, "t": t}
        timeline.append({
            "phase": "detect", "t_offset_s": t, "signal": sig,
            "status": "triggered", "outputs_hash": _compact(payload),
        })
        t += int(sc["expected_ttd_s"] / max(len(sc["detect_signals"]), 1))

    # Phase REMEDIATE
    for step in sc["remediate_steps"]:
        payload = {"scenario": scenario_id, "phase": "remediate", "step": step, "t": t}
        timeline.append({
            "phase": "remediate", "t_offset_s": t, "action": step["action"],
            "params": step.get("params", {}), "status": "done",
            "outputs_hash": _compact(payload),
        })
        t += int(sc["expected_ttm_s"] / max(len(sc["remediate_steps"]), 1))

    # Phase VERIFY
    for sig in sc["verify_signals"]:
        payload = {"scenario": scenario_id, "phase": "verify", "signal": sig, "t": t}
        timeline.append({
            "phase": "verify", "t_offset_s": t, "signal": sig,
            "status": "passed", "outputs_hash": _compact(payload),
        })
        t += 5

    # Metrics
    metrics = {
        "ttr_s": t, "ttd_s": sc["expected_ttd_s"], "ttm_s": sc["expected_ttm_s"],
        "steps_count": len(timeline),
        "inject_steps": len(sc["inject_steps"]),
        "detect_signals": len(sc["detect_signals"]),
        "remediate_steps": len(sc["remediate_steps"]),
        "verify_signals": len(sc["verify_signals"]),
        "slo_met": True,
        "slo_target": sc["slo_target"],
    }

    outputs_hash = _sha({"timeline": timeline, "metrics": metrics})
    run_id = _sha({"scenario_id": scenario_id, "options": options})[:24]

    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "scenario_name": sc["name"],
        "severity": sc["severity"],
        "status": "completed",
        "timeline": timeline,
        "metrics": metrics,
        "outputs_hash": outputs_hash,
        "audit_chain_head_hash": _chain_head(),
        "created_at": ASOF,
    }


# ─────────────────── In-memory store ─────────────────────────────────────────

_RUNS: Dict[str, Dict[str, Any]] = {}


def reset_drills() -> None:
    _RUNS.clear()


# ─────────────────── Public API ───────────────────────────────────────────────

def list_scenarios() -> List[Dict[str, Any]]:
    return [
        {"id": k, "name": v["name"], "category": v["category"], "severity": v["severity"],
         "description": v["description"]}
        for k, v in _SCENARIOS.items()
    ]


def run_drill(scenario_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    if scenario_id not in _SCENARIOS:
        raise ValueError(f"Scenario not found: {scenario_id}")
    run = _run_drill(scenario_id, options)
    _RUNS[run["run_id"]] = run
    return run


def get_run(run_id: str) -> Dict[str, Any]:
    r = _RUNS.get(run_id)
    if not r:
        raise ValueError(f"Run not found: {run_id}")
    return r


def build_incident_pack(run_id: str) -> Dict[str, Any]:
    run = get_run(run_id)
    sc = _SCENARIOS[run["scenario_id"]]
    runbook = {
        "scenario_id": run["scenario_id"],
        "name": sc["name"],
        "inject_steps": sc["inject_steps"],
        "detect_signals": sc["detect_signals"],
        "remediate_steps": sc["remediate_steps"],
        "verify_signals": sc["verify_signals"],
    }
    files = [
        {"name": "runbook.json", "content": json.dumps(runbook, indent=2)},
        {"name": "timeline.json", "content": json.dumps(run["timeline"], indent=2)},
        {"name": "metrics.json", "content": json.dumps(run["metrics"], indent=2)},
    ]
    pack_payload = {"run_id": run_id, "files": [f["name"] for f in files]}
    return {
        "run_id": run_id,
        "scenario_id": run["scenario_id"],
        "scenario_name": run["scenario_name"],
        "files": files,
        "file_count": len(files),
        "pack_hash": _sha(pack_payload),
        "output_hash": run["outputs_hash"],
        "audit_chain_head_hash": _chain_head(),
        "exported_at": ASOF,
    }


# ─────────────────── Router ──────────────────────────────────────────────────

incident_drills_router = APIRouter(tags=["incident_drills"])
incident_drills_exports_router = APIRouter(tags=["incident_drills_exports"])


class RunDrillRequest(BaseModel):
    scenario_id: str = Field(default="api_latency_spike")
    options: Dict[str, Any] = Field(default_factory=dict)


class ExportRequest(BaseModel):
    run_id: str


@incident_drills_router.get("/incidents/scenarios")
def api_list_scenarios():
    return {"scenarios": list_scenarios()}


@incident_drills_router.post("/incidents/run")
def api_run_drill(req: RunDrillRequest):
    try:
        return run_drill(req.scenario_id, req.options)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@incident_drills_router.get("/incidents/runs/{run_id}")
def api_get_run(run_id: str):
    try:
        return get_run(run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@incident_drills_exports_router.post("/exports/incident-pack")
def api_export_pack(req: ExportRequest):
    try:
        return build_incident_pack(req.run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
