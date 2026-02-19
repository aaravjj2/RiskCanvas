"""
reviews.py (v5.30.0-v5.32.0 — Wave 51)

Collaborative review and sign-off flows.

Review:
  review_id, tenant_id, subject_type, subject_id, status,
  requested_by, reviewers, decision, decision_hash, created_at, updated_at

Status transitions:
  DRAFT → IN_REVIEW → APPROVED | REJECTED

Approving triggers an attestation (approval receipt).
All IDs and hashes deterministic.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

REVIEW_STORE: Dict[str, Dict[str, Any]] = {}

VALID_SUBJECT_TYPES = ["scenario", "run", "artifact", "compliance_pack", "dataset"]
VALID_STATUSES = ["DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"]


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _rid(tenant_id: str, subject_type: str, subject_id: str, requested_by: str) -> str:
    return _sha({"tenant_id": tenant_id, "subject_type": subject_type,
                 "subject_id": subject_id, "requested_by": requested_by})[:32]


def _compute_decision_hash(review_id: str, decision: str, decided_by: str) -> str:
    return _sha({"review_id": review_id, "decision": decision, "decided_by": decided_by, "as_of": ASOF})


def create_review(
    tenant_id: str,
    subject_type: str,
    subject_id: str,
    requested_by: str,
    reviewers: Optional[List[str]] = None,
    notes: str = "",
) -> Dict[str, Any]:
    review_id = _rid(tenant_id, subject_type, subject_id, requested_by)

    review: Dict[str, Any] = {
        "review_id": review_id,
        "tenant_id": tenant_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "status": "DRAFT",
        "requested_by": requested_by,
        "reviewers": reviewers or ["reviewer@riskcanvas.io"],
        "notes": notes,
        "decision": None,
        "decision_hash": None,
        "decided_by": None,
        "decided_at": None,
        "attestation_id": None,
        "created_at": ASOF,
        "updated_at": ASOF,
    }

    REVIEW_STORE[review_id] = review
    return review


def get_review(review_id: str) -> Dict[str, Any]:
    r = REVIEW_STORE.get(review_id)
    if not r:
        raise ValueError(f"Review not found: {review_id}")
    return r


def list_reviews(
    tenant_id: Optional[str] = None,
    subject_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    reviews = list(REVIEW_STORE.values())
    if tenant_id:
        reviews = [r for r in reviews if r["tenant_id"] == tenant_id]
    if subject_type:
        reviews = [r for r in reviews if r["subject_type"] == subject_type]
    if status:
        reviews = [r for r in reviews if r["status"] == status]
    reviews.sort(key=lambda r: r["review_id"])
    return reviews[:limit]


def submit_review(review_id: str) -> Dict[str, Any]:
    """Transition DRAFT → IN_REVIEW."""
    r = get_review(review_id)
    if r["status"] != "DRAFT":
        raise ValueError(f"Cannot submit review in status '{r['status']}'")
    r["status"] = "IN_REVIEW"
    r["updated_at"] = ASOF
    return r


def decide_review(
    review_id: str,
    decision: str,
    decided_by: str = "reviewer@riskcanvas.io",
) -> Dict[str, Any]:
    """Transition IN_REVIEW → APPROVED | REJECTED. Issues attestation on APPROVE."""
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError(f"Invalid decision '{decision}'")
    r = get_review(review_id)
    if r["status"] != "IN_REVIEW":
        raise ValueError(f"Cannot decide review in status '{r['status']}'")

    decision_hash = _compute_decision_hash(review_id, decision, decided_by)
    r["status"] = decision
    r["decision"] = decision
    r["decision_hash"] = decision_hash
    r["decided_by"] = decided_by
    r["decided_at"] = ASOF
    r["updated_at"] = ASOF

    if decision == "APPROVED":
        from attestations import issue_attestation
        attest = issue_attestation(
            tenant_id=r["tenant_id"],
            subject=f"{r['subject_type']}/{r['subject_id']}/review/{review_id}",
            statement_type="review.approved",
            issued_by=decided_by,
            input_hash=_sha({"subject_id": r["subject_id"]}),
            output_hash=decision_hash,
        )
        r["attestation_id"] = attest["attestation_id"]

    return r


# ── Seed DEMO reviews ─────────────────────────────────────────────────────────

def _seed() -> None:
    from tenancy_v2 import DEFAULT_TENANT_ID
    from scenarios_v2 import SCENARIO_STORE

    tid = DEFAULT_TENANT_ID

    # Review for first scenario
    scenario_ids = sorted(SCENARIO_STORE.keys())
    if scenario_ids:
        r1 = create_review(tid, "scenario", scenario_ids[0], "alice@riskcanvas.io",
                           ["reviewer@riskcanvas.io", "carol@riskcanvas.io"],
                           "Quarterly stress test review Q1 2026")
        submit_review(r1["review_id"])
        decide_review(r1["review_id"], "APPROVED", "carol@riskcanvas.io")

    # Review for artifact
    from artifacts_registry import DEMO_REGISTRY
    art_ids = sorted(DEMO_REGISTRY.keys())
    if art_ids:
        r2 = create_review(tid, "artifact", art_ids[0], "bob@riskcanvas.io",
                           ["alice@riskcanvas.io"],
                           "Artifact sign-off for compliance")
        submit_review(r2["review_id"])

    # Draft review
    if len(scenario_ids) > 1:
        create_review(tid, "scenario", scenario_ids[1], "alice@riskcanvas.io",
                      ["reviewer@riskcanvas.io"],
                      "Pending whatif scenario review")


_seed()


# ── FastAPI router ────────────────────────────────────────────────────────────

router = APIRouter(prefix="/reviews", tags=["reviews"])


class CreateReviewRequest(BaseModel):
    tenant_id: Optional[str] = None
    subject_type: str
    subject_id: str
    requested_by: str = "demo@riskcanvas.io"
    reviewers: Optional[List[str]] = None
    notes: str = ""


class DecideReviewRequest(BaseModel):
    decision: str
    decided_by: str = "reviewer@riskcanvas.io"


@router.get("")
async def api_list_reviews(
    tenant_id: Optional[str] = None,
    subject_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    x_demo_tenant: Optional[str] = Header(None),
):
    tid = tenant_id or x_demo_tenant
    items = list_reviews(tenant_id=tid, subject_type=subject_type, status=status, limit=limit)
    return {"reviews": items, "count": len(items)}


@router.post("")
async def api_create_review(
    req: CreateReviewRequest,
    x_demo_tenant: Optional[str] = Header(None),
):
    if req.subject_type not in VALID_SUBJECT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid subject_type '{req.subject_type}'. Valid: {VALID_SUBJECT_TYPES}",
        )
    tid = req.tenant_id or x_demo_tenant or "default"
    review = create_review(
        tenant_id=tid,
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        requested_by=req.requested_by,
        reviewers=req.reviewers,
        notes=req.notes,
    )
    return {"review": review}


@router.get("/{review_id}")
async def api_get_review(review_id: str):
    try:
        return {"review": get_review(review_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{review_id}/submit")
async def api_submit_review(review_id: str):
    try:
        review = submit_review(review_id)
        return {"review": review}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{review_id}/decide")
async def api_decide_review(review_id: str, req: DecideReviewRequest):
    try:
        review = decide_review(review_id, req.decision, req.decided_by)
        return {"review": review}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
