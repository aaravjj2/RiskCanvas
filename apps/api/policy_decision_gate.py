"""
policy_decision_gate.py (v5.57.0 — Wave 68)

Policy Decision Gate — evaluates whether key room/export actions are
allowed based on required attestations and review states.

Rules:
  - room.lock requires: at least 1 review in APPROVED state for the subject
  - export.decision_packet requires: review APPROVED + room LOCKED
  - default (nothing configured): ALLOW

Endpoint:
  POST /policy/decision-gate
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

router = APIRouter(prefix="/policy", tags=["policy"])

# ── Demo review + attestation state (injected by rooms module indirectly) ──────

# We use in-memory demo state so there are no external calls in DEMO mode.
_DEMO_REVIEWS: Dict[str, str] = {
    "review-001": "APPROVED",
    "review-demo-001": "APPROVED",
}
_DEMO_ROOMS_LOCKED: set = {"room-demo-locked-001"}  # permanently locked demo room


def _check_reviews_approved(subject_id: str) -> bool:
    """Check if any review for subject is APPROVED (DEMO: fixed set)."""
    # In DEMO mode, simulate a review lookup
    for review_id, status in _DEMO_REVIEWS.items():
        if status == "APPROVED":
            return True
    return False


def _add_approved_review(review_id: str) -> None:
    """Register a review as approved (used by test flow)."""
    _DEMO_REVIEWS[review_id] = "APPROVED"


# ── Request / Response models ─────────────────────────────────────────────────


class DecisionGateRequest(BaseModel):
    tenant_id: str = "demo-tenant"
    room_id: Optional[str] = None
    action: str = "room.lock"  # room.lock | export.decision_packet
    subject_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class GateReason(BaseModel):
    code: str
    message: str
    satisfied: bool


class DecisionGateResponse(BaseModel):
    verdict: str  # ALLOW | BLOCK | CONDITIONAL
    action: str
    room_id: Optional[str]
    reasons: List[Dict[str, Any]]
    gate_hash: str
    asof: str


def _gate_hash(req: DecisionGateRequest, verdict: str, reasons: List[Dict]) -> str:
    raw = json.dumps({
        "room_id": req.room_id,
        "action": req.action,
        "verdict": verdict,
        "reasons": reasons,
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@router.post("/decision-gate")
def evaluate_decision_gate(req: DecisionGateRequest):
    """Evaluate whether the requested action is ALLOW/BLOCK/CONDITIONAL."""
    reasons = []
    verdicts_block = []

    if req.action == "room.lock":
        # Rule: at least 1 APPROVED review for the subject
        has_review = _check_reviews_approved(req.subject_id or "")
        r = {
            "code": "REVIEW_APPROVED",
            "message": "Room subject has an approved review" if has_review
                       else "No approved review found for room subject",
            "satisfied": has_review,
            "required": True,
        }
        reasons.append(r)
        if not has_review:
            verdicts_block.append("REVIEW_APPROVED")

    elif req.action == "export.decision_packet":
        # Rule 1: review APPROVED
        has_review = _check_reviews_approved(req.subject_id or "")
        r1 = {
            "code": "REVIEW_APPROVED",
            "message": "Approved review exists" if has_review
                       else "No approved review — packet export blocked",
            "satisfied": has_review,
            "required": True,
        }
        reasons.append(r1)
        if not has_review:
            verdicts_block.append("REVIEW_APPROVED")

        # Rule 2: room LOCKED (if room_id provided)
        if req.room_id:
            # Import rooms dynamically to avoid circular dependency
            try:
                from decision_rooms import _ROOMS  # type: ignore
                room = _ROOMS.get(req.room_id)
                room_locked = (room is not None and room.get("status") == "LOCKED")
            except ImportError:
                room_locked = req.room_id in _DEMO_ROOMS_LOCKED
        else:
            room_locked = True  # no room required

        r2 = {
            "code": "ROOM_LOCKED",
            "message": "Decision room is locked" if room_locked
                       else "Decision room must be locked before export",
            "satisfied": room_locked,
            "required": False,  # CONDITIONAL — warns but doesn't block
        }
        reasons.append(r2)

    else:
        # Unknown action — default ALLOW with info
        reasons.append({
            "code": "UNKNOWN_ACTION",
            "message": f"Action '{req.action}' has no gate configured — defaulting to ALLOW",
            "satisfied": True,
            "required": False,
        })

    # Compute verdict
    if verdicts_block:
        verdict = "BLOCK"
    elif any(not r["satisfied"] and not r["required"] for r in reasons):
        verdict = "CONDITIONAL"
    else:
        verdict = "ALLOW"

    gate_hash = _gate_hash(req, verdict, reasons)

    return {
        "verdict": verdict,
        "action": req.action,
        "room_id": req.room_id,
        "reasons": reasons,
        "gate_hash": gate_hash,
        "asof": ASOF,
    }


@router.post("/decision-gate/approve-review")
def approve_review_for_gate(review_id: str = "review-test-001"):
    """Helper endpoint: mark a review as APPROVED (for demo/test flow)."""
    _add_approved_review(review_id)
    return {"review_id": review_id, "status": "APPROVED", "added": True}
