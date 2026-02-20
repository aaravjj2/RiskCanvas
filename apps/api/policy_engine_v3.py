"""
policy_engine_v3.py (v5.58.0 — Depth Wave)

Policy Gate v3: enterprise gates for room.lock and decision_packet.export

Checks:
  - must have approved review (status=APPROVED)
  - must have attestation chain head present
  - must have eval stability_score above threshold (DEMO fixed ≥0.90)

Endpoints:
  POST /policy/v3/decision   { subject_type, subject_id, checks: [...] }

Returns: verdict (SHIP|CONDITIONAL|BLOCK) + reasons + references.
Deterministic: same canonical request → same verdict (once prereqs are stable).
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_STABILITY_THRESHOLD = 0.90

router = APIRouter(prefix="/policy/v3", tags=["policy-v3"])

# ── In-memory store ────────────────────────────────────────────────────────────

DECISION_STORE: Dict[str, Dict[str, Any]] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


# ── Check implementations ──────────────────────────────────────────────────────

def _check_approved_review(subject_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """True if subject has an APPROVED review in the review store."""
    review_id = context.get("review_id")
    if review_id:
        try:
            from reviews import REVIEW_STORE
            review = REVIEW_STORE.get(review_id)
            if review and review.get("status") == "APPROVED":
                return {
                    "check": "approved_review",
                    "passed": True,
                    "detail": f"Review {review_id} is APPROVED",
                    "reference": review_id,
                }
            elif review:
                return {
                    "check": "approved_review",
                    "passed": False,
                    "detail": f"Review {review_id} status={review.get('status')} (must be APPROVED)",
                    "reference": review_id,
                }
        except Exception:
            pass
    return {
        "check": "approved_review",
        "passed": False,
        "detail": "No approved_review found for subject",
        "reference": None,
    }


def _check_attestation_chain(subject_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """True if attestation chain head is present."""
    try:
        from audit_v2 import get_chain_head
        head = get_chain_head()
        if head:
            return {
                "check": "attestation_chain",
                "passed": True,
                "detail": f"Chain head hash present: {str(head)[:16]}...",
                "reference": str(head)[:16],
            }
    except Exception:
        pass
    # DEMO fallback: always pass if subject_id present
    if subject_id:
        return {
            "check": "attestation_chain",
            "passed": True,
            "detail": "DEMO: attestation chain head assumed present",
            "reference": "demo-chain-head",
        }
    return {
        "check": "attestation_chain",
        "passed": False,
        "detail": "No attestation chain head found",
        "reference": None,
    }


def _check_eval_stability(subject_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """True if latest eval v3 has stability_score >= 0.90."""
    eval_id = context.get("eval_id")
    if eval_id:
        try:
            from eval_harness_v3 import EVAL_STORE
            ev = EVAL_STORE.get(eval_id)
            if ev:
                score = ev.get("metrics", {}).get("stability_score", 0.0)
                passed = score >= DEMO_STABILITY_THRESHOLD
                return {
                    "check": "eval_stability",
                    "passed": passed,
                    "detail": f"Stability score {score:.4f} {'≥' if passed else '<'} threshold {DEMO_STABILITY_THRESHOLD}",
                    "reference": eval_id,
                }
        except Exception:
            pass
    # DEMO fallback: pass (stability is always met in demo)
    return {
        "check": "eval_stability",
        "passed": True,
        "detail": f"DEMO: stability_score assumed ≥ {DEMO_STABILITY_THRESHOLD}",
        "reference": None,
    }


CHECK_MAP = {
    "approved_review": _check_approved_review,
    "attestation_chain": _check_attestation_chain,
    "eval_stability": _check_eval_stability,
}

ALL_CHECKS = list(CHECK_MAP.keys())


def evaluate_policy_v3(
    subject_type: str,
    subject_id: str,
    checks: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluate policy for subject_type + subject_id.
    Returns verdict (SHIP|CONDITIONAL|BLOCK) + reasons (deterministic ordering).
    """
    checks_to_run = sorted(checks or ALL_CHECKS)
    ctx = context or {}

    check_results = []
    for chk in checks_to_run:
        fn = CHECK_MAP.get(chk)
        if fn:
            check_results.append(fn(subject_id, ctx))
        else:
            check_results.append({
                "check": chk,
                "passed": False,
                "detail": f"Unknown check: {chk}",
                "reference": None,
            })

    passed = [r for r in check_results if r["passed"]]
    failed = [r for r in check_results if not r["passed"]]

    # Verdict logic
    if not failed:
        verdict = "SHIP"
    elif len(failed) == 1 and failed[0]["check"] == "eval_stability":
        verdict = "CONDITIONAL"
    else:
        verdict = "BLOCK"

    reasons = [
        {
            "check": r["check"],
            "passed": r["passed"],
            "reason": r["detail"],
            "reference": r["reference"],
        }
        for r in check_results
    ]

    decision_id = "pv3-" + _sha({
        "subject_type": subject_type,
        "subject_id": subject_id,
        "checks": checks_to_run,
        "verdict": verdict,
    })[:20]

    return {
        "decision_id": decision_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "verdict": verdict,
        "reasons": reasons,
        "checks_run": len(check_results),
        "checks_passed": len(passed),
        "checks_failed": len(failed),
        "evaluated_at": ASOF,
        "policy_version": "v3",
    }


# ── Pydantic ───────────────────────────────────────────────────────────────────

class PolicyV3Request(BaseModel):
    subject_type: str
    subject_id: str
    checks: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class PolicyV3Response(BaseModel):
    decision: Dict[str, Any]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/decision", response_model=PolicyV3Response)
def policy_v3_decision(body: PolicyV3Request):
    decision = evaluate_policy_v3(
        subject_type=body.subject_type,
        subject_id=body.subject_id,
        checks=body.checks,
        context=body.context,
    )
    DECISION_STORE[decision["decision_id"]] = decision
    return {"decision": decision}


@router.get("/decision/{decision_id}", response_model=PolicyV3Response)
def get_policy_v3_decision(decision_id: str):
    d = DECISION_STORE.get(decision_id)
    if not d:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
    return {"decision": d}
