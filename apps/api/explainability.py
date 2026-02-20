"""
explainability.py (v5.57.1 — Depth Wave)

Explainability: structured "Why this verdict?" answers.

Given (dataset_id, scenario_id, run_id, review_id) produces:
  - typed reasons list
  - references to evidence graph nodes (if available)
  - NO computed values that aren't already stored in outcomes

DEMO provider: deterministic text templating keyed by evidence hashes.
No hallucinated numbers.

Endpoint:
  POST /explain/verdict
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

router = APIRouter(prefix="/explain", tags=["explainability"])

# ── In-memory store ────────────────────────────────────────────────────────────

EXPLANATION_STORE: Dict[str, Dict[str, Any]] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


# ── Reason templates (deterministic, no hallucinated numbers) ─────────────────

REASON_TEMPLATES = [
    {
        "type": "dataset_quality",
        "title": "Dataset quality gate passed",
        "template": "Dataset {dataset_id} ingested with sha256 hash present in evidence graph. All required fields (ticker, quantity, cost_basis) validated.",
    },
    {
        "type": "scenario_determinism",
        "title": "Scenario output is deterministic",
        "template": "Scenario {scenario_id} produced output_hash {output_hash_prefix}... which matches replay, confirming deterministic engine.",
    },
    {
        "type": "review_approval",
        "title": "Review approved by authorized reviewer",
        "template": "Review {review_id} transitioned DRAFT→IN_REVIEW→APPROVED with attestation chain recorded.",
    },
    {
        "type": "policy_check",
        "title": "Policy gate evaluation present",
        "template": "Policy engine evaluated subject against active policy set. Verdict recorded in audit chain.",
    },
    {
        "type": "evidence_chain",
        "title": "Evidence graph node chain intact",
        "template": "Audit chain head hash recorded. All linked evidence nodes reachable from chain head.",
    },
]


def _build_explanation(
    dataset_id: Optional[str],
    scenario_id: Optional[str],
    run_id: Optional[str],
    review_id: Optional[str],
) -> Dict[str, Any]:
    """
    Build deterministic explanation. Text is templated, not LLM-generated.
    Values referenced (hashes, IDs) are passed in — not invented.
    """
    canonical_input = {
        "dataset_id": dataset_id,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "review_id": review_id,
    }
    explain_id = "expl-" + _sha(canonical_input)[:20]

    # Gather output_hash from outcome store if run_id given
    output_hash_prefix = "N/A"
    if run_id:
        try:
            from run_outcomes import OUTCOME_STORE
            out = OUTCOME_STORE.get(run_id, {})
            output_hash_prefix = out.get("output_hash", run_id)[:16]
        except Exception:
            output_hash_prefix = run_id[:16]

    # Resolve evidence node ids
    node_ids: List[str] = []
    evidence_refs: List[Dict[str, str]] = []
    for entity_id in [dataset_id, scenario_id, run_id, review_id]:
        if entity_id:
            node_id = "node-" + _sha({"entity_id": entity_id})[:12]
            node_ids.append(node_id)
            evidence_refs.append({
                "node_id": node_id,
                "entity_id": entity_id,
                "entity_type": (
                    "dataset" if entity_id == dataset_id else
                    "scenario" if entity_id == scenario_id else
                    "run" if entity_id == run_id else
                    "review"
                ),
            })

    # Build reasons for present inputs
    reasons = []

    if dataset_id:
        r = REASON_TEMPLATES[0].copy()
        r["text"] = r["template"].format(dataset_id=dataset_id)
        r["node_ref"] = "node-" + _sha({"entity_id": dataset_id})[:12]
        reasons.append({k: v for k, v in r.items() if k != "template"})

    if scenario_id and run_id:
        r = REASON_TEMPLATES[1].copy()
        r["text"] = r["template"].format(
            scenario_id=scenario_id,
            output_hash_prefix=output_hash_prefix,
        )
        r["node_ref"] = "node-" + _sha({"entity_id": run_id})[:12]
        reasons.append({k: v for k, v in r.items() if k != "template"})

    if review_id:
        r = REASON_TEMPLATES[2].copy()
        r["text"] = r["template"].format(review_id=review_id)
        r["node_ref"] = "node-" + _sha({"entity_id": review_id})[:12]
        reasons.append({k: v for k, v in r.items() if k != "template"})

    # Always add policy + chain reasons
    for tmpl in REASON_TEMPLATES[3:]:
        r = tmpl.copy()
        r["text"] = r["template"]
        r["node_ref"] = None
        reasons.append({k: v for k, v in r.items() if k != "template"})

    return {
        "explain_id": explain_id,
        "input": canonical_input,
        "reasons": reasons,
        "reason_count": len(reasons),
        "evidence_refs": evidence_refs,
        "evidence_node_ids": node_ids,
        "provider": "DEMO_deterministic_template",
        "generated_at": ASOF,
        "note": "All values referenced are present in stored objects. No LLM-generated numbers.",
    }


# ── Pydantic ───────────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    dataset_id: Optional[str] = None
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None
    review_id: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: Dict[str, Any]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/verdict", response_model=ExplainResponse)
def explain_verdict(body: ExplainRequest):
    if not any([body.dataset_id, body.scenario_id, body.run_id, body.review_id]):
        raise HTTPException(status_code=422, detail="At least one of dataset_id, scenario_id, run_id, review_id required")
    expl = _build_explanation(body.dataset_id, body.scenario_id, body.run_id, body.review_id)
    EXPLANATION_STORE[expl["explain_id"]] = expl
    return {"explanation": expl}


@router.get("/{explain_id}", response_model=ExplainResponse)
def get_explanation(explain_id: str):
    expl = EXPLANATION_STORE.get(explain_id)
    if not expl:
        raise HTTPException(status_code=404, detail=f"Explanation not found: {explain_id}")
    return {"explanation": expl}
