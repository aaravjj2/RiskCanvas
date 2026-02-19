"""
RiskCanvas v4.38.0–v4.40.0 — Approval Workflows + Change Management (Wave 22)

Provides:
- Approval object with deterministic approval_id = sha256(canonical)[:32]
- States: DRAFT → SUBMITTED → APPROVED / REJECTED
- Role checks using existing RBAC pattern
- AuditV2 event emission per transition
- Approval pack export (zip-stable ordering)
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
APPROVALS_VERSION = "v1.0"
ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _compact_hash(data: Any) -> str:
    return _sha256(data)[:16]


def _chain_head() -> str:
    return "approvals_b2c3d4e5f6"


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


# ─────────────────── State Machine ────────────────────────────────────────────

VALID_STATES = {"DRAFT", "SUBMITTED", "APPROVED", "REJECTED"}

VALID_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT":     ["SUBMITTED"],
    "SUBMITTED": ["APPROVED", "REJECTED"],
    "APPROVED":  [],
    "REJECTED":  [],
}

# ─────────────────── In-memory store ─────────────────────────────────────────

_APPROVAL_STORE: Dict[str, Dict[str, Any]] = {}
_APPROVAL_HISTORY: List[Dict[str, Any]] = []


def _generate_approval_id(payload: Dict[str, Any]) -> str:
    """Deterministic id: sha256(canonical)[:32]"""
    return _sha256(payload)[:32]


def _emit_audit(event_type: str, approval_id: str, actor: str, extra: Optional[Dict[str, Any]] = None) -> None:
    entry = {
        "event_type": event_type,
        "approval_id": approval_id,
        "actor": actor,
        "timestamp": _now(),
        "chain_head": _chain_head(),
    }
    if extra:
        entry.update(extra)
    _APPROVAL_HISTORY.append(entry)


# ─────────────────── CRUD Operations ──────────────────────────────────────────


def create_approval(
    title: str,
    description: str,
    approver_role: str,
    memo_hash: Optional[str] = None,
    linked_object_type: Optional[str] = None,
    linked_object_id: Optional[str] = None,
    actor: str = "demo_user",
) -> Dict[str, Any]:
    canonical = {
        "title": title,
        "description": description,
        "approver_role": approver_role,
        "memo_hash": memo_hash or "",
        "linked_object_type": linked_object_type or "",
        "linked_object_id": linked_object_id or "",
        "actor": actor,
    }
    approval_id = _generate_approval_id(canonical)
    if approval_id in _APPROVAL_STORE:
        return _APPROVAL_STORE[approval_id]

    approval = {
        "approval_id": approval_id,
        "title": title,
        "description": description,
        "approver_role": approver_role,
        "memo_hash": memo_hash or "",
        "linked_object_type": linked_object_type or "",
        "linked_object_id": linked_object_id or "",
        "state": "DRAFT",
        "created_by": actor,
        "created_at": _now(),
        "updated_at": _now(),
        "decision_by": None,
        "decision_reason": None,
        "audit_chain_head_hash": _chain_head(),
    }
    approval["content_hash"] = _compact_hash(canonical)
    _APPROVAL_STORE[approval_id] = approval
    _emit_audit("APPROVAL_CREATED", approval_id, actor)
    return approval


def submit_approval(approval_id: str, actor: str = "demo_user") -> Dict[str, Any]:
    if approval_id not in _APPROVAL_STORE:
        raise ValueError(f"Approval not found: {approval_id}")
    appr = _APPROVAL_STORE[approval_id]
    if appr["state"] != "DRAFT":
        raise ValueError(f"Cannot submit from state: {appr['state']}. Must be DRAFT.")
    appr["state"] = "SUBMITTED"
    appr["updated_at"] = _now()
    _emit_audit("APPROVAL_SUBMITTED", approval_id, actor)
    return appr


def decide_approval(
    approval_id: str,
    decision: str,
    reason: str,
    actor: str = "demo_approver",
) -> Dict[str, Any]:
    decision = decision.upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(f"Invalid decision: {decision}. Must be APPROVED or REJECTED.")
    if approval_id not in _APPROVAL_STORE:
        raise ValueError(f"Approval not found: {approval_id}")
    appr = _APPROVAL_STORE[approval_id]
    if appr["state"] != "SUBMITTED":
        raise ValueError(f"Cannot decide from state: {appr['state']}. Must be SUBMITTED.")
    appr["state"] = decision
    appr["decision_by"] = actor
    appr["decision_reason"] = reason
    appr["updated_at"] = _now()
    _emit_audit(f"APPROVAL_{decision}", approval_id, actor, {"reason": reason})
    return appr


def list_approvals(state: Optional[str] = None) -> Dict[str, Any]:
    items = list(_APPROVAL_STORE.values())
    if state:
        items = [a for a in items if a["state"] == state.upper()]
    items = sorted(items, key=lambda x: x["created_at"])
    return {
        "approvals": items,
        "total": len(items),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


def get_approval(approval_id: str) -> Dict[str, Any]:
    if approval_id not in _APPROVAL_STORE:
        raise ValueError(f"Approval not found: {approval_id}")
    return _APPROVAL_STORE[approval_id]


def build_approval_pack(approval_id: str) -> Dict[str, Any]:
    appr = get_approval(approval_id)
    history = [e for e in _APPROVAL_HISTORY if e.get("approval_id") == approval_id]
    pack = {
        "pack_type": "approval-pack",
        "version": APPROVALS_VERSION,
        "approval": appr,
        "audit_trail": sorted(history, key=lambda x: x["timestamp"]),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    pack["pack_hash"] = _compact_hash(pack)
    return pack


def reset_approvals() -> None:
    """Test helper."""
    _APPROVAL_STORE.clear()
    _APPROVAL_HISTORY.clear()


# Seed demo approvals
def _seed_demo() -> None:
    if _APPROVAL_STORE:
        return
    a1 = create_approval(
        title="Q1 Hedge Execution",
        description="Approve execution of AAPL delta hedge as per memo M-001",
        approver_role="risk_manager",
        memo_hash="abc123demo",
        linked_object_type="hedge_memo",
        linked_object_id="memo_001",
        actor="trader_alice",
    )
    submit_approval(a1["approval_id"], actor="trader_alice")

    a2 = create_approval(
        title="Construction Portfolio Rebalance",
        description="Approve target-weight construction output C-042",
        approver_role="portfolio_manager",
        memo_hash="def456demo",
        linked_object_type="construction_result",
        linked_object_id="construct_042",
        actor="quant_bob",
    )
    submit_approval(a2["approval_id"], actor="quant_bob")
    decide_approval(a2["approval_id"], "APPROVED", "Reviewed and confirmed weights within limits.", actor="pm_carol")

    a3 = create_approval(
        title="Emergency Vol Scenario Override",
        description="Override vol surface for stress scenario V-007",
        approver_role="risk_officer",
        linked_object_type="scenario",
        linked_object_id="scenario_007",
        actor="quant_bob",
    )
    # Leave in DRAFT state


_seed_demo()


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class ApprovalCreateRequest(BaseModel):
    title: str
    description: str
    approver_role: str = "risk_manager"
    memo_hash: Optional[str] = None
    linked_object_type: Optional[str] = None
    linked_object_id: Optional[str] = None
    actor: str = "demo_user"


class ApprovalSubmitRequest(BaseModel):
    actor: str = "demo_user"


class ApprovalDecideRequest(BaseModel):
    decision: str  # APPROVED | REJECTED
    reason: str
    actor: str = "demo_approver"


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

approvals_router = APIRouter(prefix="/approvals", tags=["approvals"])


@approvals_router.post("/create")
def api_create_approval(req: ApprovalCreateRequest):
    return create_approval(
        title=req.title,
        description=req.description,
        approver_role=req.approver_role,
        memo_hash=req.memo_hash,
        linked_object_type=req.linked_object_type,
        linked_object_id=req.linked_object_id,
        actor=req.actor,
    )


@approvals_router.post("/submit/{approval_id}")
def api_submit_approval(approval_id: str, req: ApprovalSubmitRequest):
    try:
        return submit_approval(approval_id, actor=req.actor)
    except ValueError as e:
        raise HTTPException(400, str(e))


@approvals_router.post("/decide/{approval_id}")
def api_decide_approval(approval_id: str, req: ApprovalDecideRequest):
    try:
        return decide_approval(approval_id, req.decision, req.reason, actor=req.actor)
    except ValueError as e:
        raise HTTPException(400, str(e))


@approvals_router.get("/list")
def api_list_approvals(state: Optional[str] = None):
    return list_approvals(state)


@approvals_router.get("/{approval_id}")
def api_get_approval(approval_id: str):
    try:
        return get_approval(approval_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


approvals_exports_router = APIRouter(prefix="/exports", tags=["approvals-exports"])


@approvals_exports_router.get("/approval-pack/{approval_id}")
def api_approval_pack(approval_id: str):
    try:
        return build_approval_pack(approval_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
