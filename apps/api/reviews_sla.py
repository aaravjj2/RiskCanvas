"""
reviews_sla.py (v5.48.0 — Wave 60)

Reviews Assignment + SLA extension.

Extends the review concept with:
  - reviewer_assignment: deterministic round-robin from REVIEWERS pool
  - sla_deadline: ingest_time + 48 h (deterministic string, no real time math)
  - sla_breached: True if decided_at > sla_deadline  (string comparison, ASOF-safe)
  - escalation_events: list of escalation dict when SLA breached
  - bulk_assign: assign multiple pending reviews to reviewers in batch
  - dashboard: aggregated SLA health per reviewer

Endpoints:
  GET  /reviews-sla/reviews               — list reviews with SLA fields
  GET  /reviews-sla/reviews/{id}          — single review + SLA
  POST /reviews-sla/reviews               — create review with auto-assignment + SLA
  POST /reviews-sla/reviews/{id}/decide   — approve/reject + check SLA breach
  POST /reviews-sla/bulk-assign           — bulk reviewer assignment
  GET  /reviews-sla/dashboard             — SLA health dashboard
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

REVIEWERS = [
    "alice@riskcanvas.io",
    "bob@riskcanvas.io",
    "carol@riskcanvas.io",
    "dave@riskcanvas.io",
]

# In-memory store
REVIEWS_SLA_STORE: Dict[str, Dict[str, Any]] = {}

# ── Deterministic helpers ──────────────────────────────────────────────────────


def _assign_reviewer(review_id: str) -> str:
    """Deterministic round-robin: hash(review_id) % len(REVIEWERS)."""
    idx = int(hashlib.md5(review_id.encode()).hexdigest(), 16) % len(REVIEWERS)
    return REVIEWERS[idx]


def _sla_deadline(created_at: str) -> str:
    """
    Returns a deterministic SLA deadline.
    Using ASOF-safe string: since all demos use ASOF, the deadline is fixed.
    In real usage this would add 48h.  Here we use a fixed offset string.
    """
    # Deterministic: ASOF with day offset +2 kept as literal string.
    # Works for demo: 2026-02-19 + 2 days = 2026-02-21T00:00:00Z
    return "2026-02-21T00:00:00Z"


def _is_breached(decided_at: Optional[str], deadline: str) -> bool:
    if not decided_at:
        return False
    # String comparison is safe for ISO-8601 with same timezone suffix
    return decided_at > deadline


def _escalation_event(review_id: str, reviewer: str, deadline: str) -> Dict[str, Any]:
    return {
        "type": "SLA_BREACH",
        "review_id": review_id,
        "assigned_to": reviewer,
        "deadline": deadline,
        "escalated_to": "manager@riskcanvas.io",
        "escalated_at": ASOF,
        "message": f"Review {review_id} exceeded SLA deadline {deadline}",
    }


# ── Core logic ─────────────────────────────────────────────────────────────────


def create_review(
    review_id: str,
    packet_id: str,
    title: str,
    tenant_id: str = "tenant-001",
    notes: str = "",
    reviewer_override: Optional[str] = None,
) -> Dict[str, Any]:
    assigned_to = reviewer_override or _assign_reviewer(review_id)
    deadline = _sla_deadline(ASOF)

    review = {
        "review_id": review_id,
        "packet_id": packet_id,
        "title": title,
        "tenant_id": tenant_id,
        "notes": notes,
        "status": "PENDING",
        "assigned_to": assigned_to,
        "sla_deadline": deadline,
        "sla_breached": False,
        "escalation_events": [],
        "decision": None,
        "decided_at": None,
        "created_at": ASOF,
    }
    REVIEWS_SLA_STORE[review_id] = review
    return review


def decide_review(
    review_id: str,
    decision: str,
    decided_by: str,
    decided_at: str = ASOF,
    rationale: str = "",
) -> Dict[str, Any]:
    if review_id not in REVIEWS_SLA_STORE:
        raise ValueError(f"Review not found: {review_id}")

    review = REVIEWS_SLA_STORE[review_id]
    if decision not in {"APPROVED", "REJECTED"}:
        raise ValueError(f"Invalid decision: {decision}. Must be APPROVED or REJECTED.")

    deadline = review["sla_deadline"]
    breached = _is_breached(decided_at, deadline)

    review["status"] = decision
    review["decision"] = decision
    review["decided_at"] = decided_at
    review["decided_by"] = decided_by
    review["rationale"] = rationale
    review["sla_breached"] = breached

    if breached:
        event = _escalation_event(review_id, review["assigned_to"], deadline)
        review["escalation_events"].append(event)

    return review


def bulk_assign(review_ids: List[str]) -> List[Dict[str, Any]]:
    """Assign reviewers to multiple pending reviews deterministically."""
    updated = []
    for rid in review_ids:
        if rid in REVIEWS_SLA_STORE:
            rev = REVIEWS_SLA_STORE[rid]
            if rev["status"] == "PENDING":
                rev["assigned_to"] = _assign_reviewer(rid)
                updated.append(rev)
    return updated


def get_review(review_id: str) -> Dict[str, Any]:
    if review_id not in REVIEWS_SLA_STORE:
        raise ValueError(f"Review not found: {review_id}")
    return REVIEWS_SLA_STORE[review_id]


def list_reviews(limit: int = 100) -> List[Dict[str, Any]]:
    return list(REVIEWS_SLA_STORE.values())[:limit]


def get_dashboard() -> Dict[str, Any]:
    reviews = list(REVIEWS_SLA_STORE.values())
    by_reviewer: Dict[str, Dict[str, int]] = {}
    total_breached = 0

    for rev in reviews:
        r = rev["assigned_to"] or "unassigned"
        if r not in by_reviewer:
            by_reviewer[r] = {"total": 0, "breached": 0, "approved": 0, "rejected": 0}
        by_reviewer[r]["total"] += 1
        if rev["sla_breached"]:
            by_reviewer[r]["breached"] += 1
            total_breached += 1
        if rev["status"] == "APPROVED":
            by_reviewer[r]["approved"] += 1
        elif rev["status"] == "REJECTED":
            by_reviewer[r]["rejected"] += 1

    return {
        "total_reviews": len(reviews),
        "total_breached": total_breached,
        "by_reviewer": by_reviewer,
        "snapshot_at": ASOF,
    }


# ── Demo seed ──────────────────────────────────────────────────────────────────


def _seed() -> None:
    if REVIEWS_SLA_STORE:
        return

    seeds = [
        ("rev-sla-001", "pkt-001", "Q1 2026 Rate Risk Review"),
        ("rev-sla-002", "pkt-002", "Credit Event Response Review"),
        ("rev-sla-003", "pkt-003", "FX Exposure Report"),
    ]
    for review_id, packet_id, title in seeds:
        create_review(review_id, packet_id, title)

    # Decide rev-sla-001 within SLA
    decide_review("rev-sla-001", "APPROVED", "alice@riskcanvas.io",
                  decided_at="2026-02-20T12:00:00Z", rationale="All checks passed.")


_seed()


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/reviews-sla", tags=["reviews-sla"])


class CreateReviewRequest(BaseModel):
    review_id: Optional[str] = None
    packet_id: str
    title: str
    tenant_id: str = "tenant-001"
    notes: str = ""
    reviewer_override: Optional[str] = None


class DecideReviewRequest(BaseModel):
    decision: str
    decided_by: str
    decided_at: str = ASOF
    rationale: str = ""


class BulkAssignRequest(BaseModel):
    review_ids: List[str]


@router.get("/reviews")
def http_list_reviews(limit: int = 100):
    return {"reviews": list_reviews(limit=limit), "count": len(REVIEWS_SLA_STORE)}


@router.get("/reviews/{review_id}")
def http_get_review(review_id: str):
    try:
        return {"review": get_review(review_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reviews")
def http_create_review(req: CreateReviewRequest):
    review_id = req.review_id or f"rev-{uuid.uuid4().hex[:12]}"
    try:
        review = create_review(
            review_id=review_id,
            packet_id=req.packet_id,
            title=req.title,
            tenant_id=req.tenant_id,
            notes=req.notes,
            reviewer_override=req.reviewer_override,
        )
        return {"review": review}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reviews/{review_id}/decide")
def http_decide_review(review_id: str, req: DecideReviewRequest):
    try:
        review = decide_review(
            review_id=review_id,
            decision=req.decision,
            decided_by=req.decided_by,
            decided_at=req.decided_at,
            rationale=req.rationale,
        )
        return {"review": review}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/bulk-assign")
def http_bulk_assign(req: BulkAssignRequest):
    updated = bulk_assign(req.review_ids)
    return {"updated": updated, "count": len(updated)}


@router.get("/dashboard")
def http_dashboard():
    return get_dashboard()
