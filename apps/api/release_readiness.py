"""
RiskCanvas v4.58.0-v4.61.0 — Release Readiness Scoring (Wave 28)

Provides:
- Deterministic readiness evaluator: 8 gates → score 0-100 → SHIP/CONDITIONAL/BLOCK
- Each gate: status (PASS/WARN/FAIL), weight, score_contribution
- Release memo: gate breakdown + risk summary + recommendation
- Export: release-memo-pack (memo.json + gate_report.json)
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
VERSION = "v4.61.0"
ASOF = "2026-02-19T10:00:00Z"


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _compact(data: Any) -> str:
    return _sha(data)[:16]


def _chain_head() -> str:
    return "readiness_chain_c3d4e5f6"


# ─────────────────── Gate Definitions ────────────────────────────────────────

_GATES = [
    {"id": "test_pass_rate", "name": "Test Pass Rate", "weight": 20, "thresholds": {"PASS": 98.0, "WARN": 90.0}},
    {"id": "code_coverage", "name": "Code Coverage", "weight": 15, "thresholds": {"PASS": 85.0, "WARN": 75.0}},
    {"id": "critical_vulnerabilities", "name": "Critical Vulns (count)", "weight": 20, "thresholds": {"PASS": 0, "WARN": 2}, "invert": True},
    {"id": "e2e_pass_rate", "name": "E2E Test Pass Rate", "weight": 15, "thresholds": {"PASS": 100.0, "WARN": 95.0}},
    {"id": "build_latency_s", "name": "Build Latency (s)", "weight": 5, "thresholds": {"PASS": 120, "WARN": 300}, "invert": True},
    {"id": "approval_count", "name": "Approvals", "weight": 10, "thresholds": {"PASS": 2, "WARN": 1}},
    {"id": "docs_coverage_pct", "name": "Docs Coverage %", "weight": 10, "thresholds": {"PASS": 80.0, "WARN": 60.0}},
    {"id": "secret_scan_violations", "name": "Secret Scan Violations", "weight": 5, "thresholds": {"PASS": 0, "WARN": 0}, "invert": True},
]


def _evaluate_gate(gate: Dict[str, Any], value: float) -> Dict[str, Any]:
    thr = gate["thresholds"]
    invert = gate.get("invert", False)
    if invert:
        # lower is better
        if value <= thr["PASS"]:
            status = "PASS"
        elif value <= thr["WARN"]:
            status = "WARN"
        else:
            status = "FAIL"
    else:
        # higher is better
        if value >= thr["PASS"]:
            status = "PASS"
        elif value >= thr["WARN"]:
            status = "WARN"
        else:
            status = "FAIL"

    score_map = {"PASS": 1.0, "WARN": 0.5, "FAIL": 0.0}
    contribution = gate["weight"] * score_map[status]
    return {
        "gate_id": gate["id"],
        "gate_name": gate["name"],
        "weight": gate["weight"],
        "value": value,
        "status": status,
        "score_contribution": contribution,
        "threshold_pass": thr["PASS"],
        "threshold_warn": thr["WARN"],
    }


# ─────────────────── Demo defaults ───────────────────────────────────────────

_DEMO_METRICS = {
    "test_pass_rate": 99.5,
    "code_coverage": 87.3,
    "critical_vulnerabilities": 0,
    "e2e_pass_rate": 100.0,
    "build_latency_s": 95,
    "approval_count": 2,
    "docs_coverage_pct": 82.0,
    "secret_scan_violations": 0,
}


def _evaluate_readiness(metrics: Dict[str, float], context: Dict[str, Any]) -> Dict[str, Any]:
    gate_results = []
    total_weight = sum(g["weight"] for g in _GATES)
    total_score = 0.0

    for gate in _GATES:
        value = metrics.get(gate["id"], 0.0)
        result = _evaluate_gate(gate, value)
        gate_results.append(result)
        total_score += result["score_contribution"]

    score_pct = round((total_score / total_weight) * 100, 2)

    if score_pct >= 90:
        verdict = "SHIP"
        verdict_color = "green"
    elif score_pct >= 70:
        verdict = "CONDITIONAL"
        verdict_color = "yellow"
    else:
        verdict = "BLOCK"
        verdict_color = "red"

    blocked_gates = [g for g in gate_results if g["status"] == "FAIL"]
    warned_gates = [g for g in gate_results if g["status"] == "WARN"]

    risk_summary = []
    for g in blocked_gates:
        risk_summary.append(f"FAIL: {g['gate_name']} = {g['value']} (threshold: {g['threshold_pass']})")
    for g in warned_gates:
        risk_summary.append(f"WARN: {g['gate_name']} = {g['value']} (threshold: {g['threshold_pass']})")

    return {
        "score": score_pct,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "gate_results": gate_results,
        "blocked_gates": len(blocked_gates),
        "warned_gates": len(warned_gates),
        "risk_summary": risk_summary,
        "context": context,
    }


# ─────────────────── In-memory store ─────────────────────────────────────────

_ASSESSMENTS: Dict[str, Dict[str, Any]] = {}


def reset_readiness() -> None:
    _ASSESSMENTS.clear()


# ─────────────────── Public API ───────────────────────────────────────────────

def evaluate_readiness(metrics: Dict[str, float], context: Dict[str, Any]) -> Dict[str, Any]:
    effective_metrics = {**_DEMO_METRICS, **metrics}
    result = _evaluate_readiness(effective_metrics, context)

    memo = {
        "title": f"Release Readiness — {context.get('version', 'HEAD')}",
        "branch": context.get("branch", "main"),
        "version": context.get("version", "HEAD"),
        "author": context.get("author", "unknown"),
        "verdict": result["verdict"],
        "score": result["score"],
        "gate_count": len(_GATES),
        "blocked_gates": result["blocked_gates"],
        "warned_gates": result["warned_gates"],
        "risk_summary": result["risk_summary"],
        "recommendation": (
            "Proceed to production deployment." if result["verdict"] == "SHIP"
            else "Address WARN items before deployment." if result["verdict"] == "CONDITIONAL"
            else "BLOCK — resolve failing gates before merge."
        ),
    }

    assessment_id = _sha({"metrics": effective_metrics, "context": context})[:24]
    assessment = {
        "assessment_id": assessment_id,
        "metrics": effective_metrics,
        "context": context,
        "score": result["score"],
        "verdict": result["verdict"],
        "verdict_color": result["verdict_color"],
        "gate_results": result["gate_results"],
        "blocked_gates": result["blocked_gates"],
        "warned_gates": result["warned_gates"],
        "risk_summary": result["risk_summary"],
        "memo": memo,
        "output_hash": _sha(result),
        "audit_chain_head_hash": _chain_head(),
        "created_at": ASOF,
    }
    _ASSESSMENTS[assessment_id] = assessment
    return assessment


def get_assessment(assessment_id: str) -> Dict[str, Any]:
    a = _ASSESSMENTS.get(assessment_id)
    if not a:
        raise ValueError(f"Assessment not found: {assessment_id}")
    return a


def build_release_memo_pack(assessment_id: str) -> Dict[str, Any]:
    assessment = get_assessment(assessment_id)
    files = [
        {"name": "memo.json", "content": json.dumps(assessment["memo"], indent=2)},
        {"name": "gate_report.json", "content": json.dumps(assessment["gate_results"], indent=2)},
        {"name": "risk_summary.txt", "content": "\n".join(assessment["risk_summary"]) or "No risks identified."},
    ]
    pack_payload = {"assessment_id": assessment_id, "files": [f["name"] for f in files]}
    return {
        "assessment_id": assessment_id,
        "verdict": assessment["verdict"],
        "score": assessment["score"],
        "files": files,
        "file_count": len(files),
        "pack_hash": _sha(pack_payload),
        "output_hash": assessment["output_hash"],
        "audit_chain_head_hash": _chain_head(),
        "exported_at": ASOF,
    }


# ─────────────────── Router ──────────────────────────────────────────────────

release_readiness_router = APIRouter(tags=["release_readiness"])
release_readiness_exports_router = APIRouter(tags=["release_readiness_exports"])


class EvaluateRequest(BaseModel):
    metrics: Dict[str, float] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=lambda: {"version": "HEAD", "branch": "main", "author": "ci-bot"})


class ExportRequest(BaseModel):
    assessment_id: str


@release_readiness_router.post("/release/readiness/evaluate")
def api_evaluate(req: EvaluateRequest):
    return evaluate_readiness(req.metrics, req.context)


@release_readiness_router.get("/release/readiness/{assessment_id}")
def api_get_assessment(assessment_id: str):
    try:
        return get_assessment(assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@release_readiness_exports_router.post("/exports/release-memo-pack")
def api_export_pack(req: ExportRequest):
    try:
        return build_release_memo_pack(req.assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
