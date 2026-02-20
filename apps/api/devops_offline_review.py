"""
devops_offline_review.py (v5.59.1 — Depth Wave)

GitLab offline MR → Policy Gate → Export packet pipeline.

POST /devops/mr/offline/review-and-open
  - accepts: diff (string), mr_title, mr_iid, reviewer
  - performs:
    a) scan diff for patterns (deterministic)
    b) run policy gate v3 (subject_type=policy_check)
    c) open a review in DRAFT state automatically
  - returns: review_id, policy_verdict, diff_scan_result

Deterministic: same diff → same review_id → same verdict.
No external network calls.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

router = APIRouter(prefix="/devops/mr/offline", tags=["devops-offline"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


# ── DEMO diff scanner ──────────────────────────────────────────────────────────

RISK_PATTERNS = [
    {"pattern": "DEMO_MODE", "severity": "info",     "message": "DEMO_MODE reference detected"},
    {"pattern": "api_key",   "severity": "high",     "message": "Potential API key reference"},
    {"pattern": "password",  "severity": "high",     "message": "Potential password reference"},
    {"pattern": "secret",    "severity": "medium",   "message": "Potential secret reference"},
    {"pattern": "TODO",      "severity": "low",      "message": "TODO comment in diff"},
    {"pattern": "FIXME",     "severity": "low",      "message": "FIXME comment in diff"},
    {"pattern": "hardcode",  "severity": "medium",   "message": "Potential hardcoded value"},
]


def _scan_diff(diff: str) -> Dict[str, Any]:
    """Scan diff for risk patterns. Deterministic: same diff → same scan."""
    findings = []
    diff_lower = diff.lower()
    for rp in RISK_PATTERNS:
        if rp["pattern"].lower() in diff_lower:
            findings.append({
                "pattern": rp["pattern"],
                "severity": rp["severity"],
                "message": rp["message"],
                "line_count": diff_lower.count(rp["pattern"].lower()),
            })

    scan_hash = _sha({"diff": diff, "patterns": [f["pattern"] for f in findings]})
    return {
        "scan_hash": scan_hash[:20],
        "findings": findings,
        "finding_count": len(findings),
        "severity_summary": {
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium"),
            "low": sum(1 for f in findings if f["severity"] == "low"),
            "info": sum(1 for f in findings if f["severity"] == "info"),
        },
        "passed": not any(f["severity"] == "high" for f in findings),
    }


# ── Main pipeline ──────────────────────────────────────────────────────────────

def offline_review_and_open(
    diff: str,
    mr_title: str,
    mr_iid: str,
    reviewer: str,
    tenant_id: str = "demo-tenant",
) -> Dict[str, Any]:
    """Full pipeline: scan → policy → open review."""

    # Step 1: scan diff
    diff_scan = _scan_diff(diff)

    # Step 2: build a policy_check subject
    subject_id = "mr-" + _sha({"mr_iid": mr_iid, "mr_title": mr_title})[:16]

    # Step 3: run policy gate v3
    from policy_engine_v3 import evaluate_policy_v3
    context = {
        "diff_scan": diff_scan,
        "mr_iid": mr_iid,
    }
    policy = evaluate_policy_v3(
        subject_type="policy_check",
        subject_id=subject_id,
        checks=["attestation_chain", "eval_stability"],
        context=context,
    )

    # Override verdict based on diff scan
    if not diff_scan["passed"]:
        policy["verdict"] = "BLOCK"
        policy["reasons"].append({
            "check": "diff_scan",
            "passed": False,
            "reason": f"Diff scan found {diff_scan['severity_summary']['high']} high-severity findings",
            "reference": diff_scan["scan_hash"],
        })

    # Step 4: open a review (DRAFT)
    from reviews import create_review
    notes = (
        f"## Offline MR Review\n\n"
        f"**MR:** #{mr_iid} — {mr_title}\n\n"
        f"**Diff scan:** {diff_scan['finding_count']} findings "
        f"(high={diff_scan['severity_summary']['high']})\n\n"
        f"**Policy verdict:** {policy['verdict']}\n\n"
        f"Auto-opened by devops pipeline."
    )
    review = create_review(
        tenant_id=tenant_id,
        subject_type="policy_check",
        subject_id=subject_id,
        requested_by=reviewer,
        notes=notes,
    )

    return {
        "review_id": review["review_id"],
        "subject_id": subject_id,
        "policy_verdict": policy["verdict"],
        "policy_decision_id": policy["decision_id"],
        "diff_scan": diff_scan,
        "review": review,
        "policy": policy,
        "pipeline": "offline_mr_review_v1",
        "generated_at": ASOF,
    }


# ── Pydantic ───────────────────────────────────────────────────────────────────

class OfflineReviewRequest(BaseModel):
    diff: str
    mr_title: str = "Untitled MR"
    mr_iid: str = "1"
    reviewer: str = "reviewer@demo"
    tenant_id: str = "demo-tenant"


class OfflineReviewResponse(BaseModel):
    result: Dict[str, Any]


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/review-and-open", response_model=OfflineReviewResponse)
def devops_offline_review_and_open(body: OfflineReviewRequest):
    result = offline_review_and_open(
        diff=body.diff,
        mr_title=body.mr_title,
        mr_iid=body.mr_iid,
        reviewer=body.reviewer,
        tenant_id=body.tenant_id,
    )
    return {"result": result}
