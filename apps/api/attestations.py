"""
attestations.py (v5.06.0-v5.09.0 — Wave 43)

Cryptographic action receipts / attestation engine.

Attestation:
  attestation_id, tenant_id, subject, statement_type,
  issued_by, issued_at, input_hash, output_hash, prev_hash

Forms a hash chain per tenant.
Statement types: mr-review-complete, incident-run-complete,
                 readiness-eval-complete, artifact-created, export-generated
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

_CHAINS: Dict[str, List[Dict[str, Any]]] = {}  # tenant_id → list of attestations


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _attest_id(payload: Dict) -> str:
    return _sha(payload)[:32]


# ── Issue attestation ────────────────────────────────────────────────────────

def issue_attestation(
    tenant_id: str,
    subject: str,
    statement_type: str,
    issued_by: str,
    input_hash: str,
    output_hash: str,
) -> Dict[str, Any]:
    chain = _CHAINS.setdefault(tenant_id, [])
    prev_hash = chain[-1]["attestation_id"] if chain else "genesis"

    payload = {
        "tenant_id": tenant_id,
        "subject": subject,
        "statement_type": statement_type,
        "issued_by": issued_by,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "prev_hash": prev_hash,
        "seq": len(chain),
    }
    attest_id = _attest_id(payload)
    attest = {
        "attestation_id": attest_id,
        "tenant_id": tenant_id,
        "subject": subject,
        "statement_type": statement_type,
        "issued_by": issued_by,
        "issued_at": ASOF,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "prev_hash": prev_hash,
        "seq": len(chain),
        "chain_head_hash": attest_id,
    }
    chain.append(attest)
    return attest


def list_attestations(
    tenant_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    return list(_CHAINS.get(tenant_id, []))[::-1][:limit]


def get_attestation(attestation_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    for tid, chain in _CHAINS.items():
        if tenant_id and tid != tenant_id:
            continue
        for a in chain:
            if a["attestation_id"] == attestation_id:
                return a
    raise ValueError(f"Attestation not found: {attestation_id}")


def get_chain_head(tenant_id: str) -> Optional[str]:
    chain = _CHAINS.get(tenant_id, [])
    return chain[-1]["attestation_id"] if chain else None


def build_receipts_pack(tenant_id: str) -> Dict[str, Any]:
    chain = _CHAINS.get(tenant_id, [])
    head = chain[-1]["attestation_id"] if chain else "empty"
    content = json.dumps(chain, sort_keys=True)
    sha = hashlib.sha256(content.encode()).hexdigest()
    payload = {"tenant_id": tenant_id, "chain_head": head, "pack": "receipts"}
    pack_id = _sha(payload)[:24]
    # Gather artifact refs
    artifact_ids = list({a["subject"] for a in chain if "artifact" in a["statement_type"]})
    return {
        "pack_id": pack_id,
        "tenant_id": tenant_id,
        "chain_head_hash": head,
        "attestation_count": len(chain),
        "chain_sha256": sha,
        "referenced_artifacts": artifact_ids,
        "files": ["attestations.json", "chain_head.txt"],
        "exported_at": ASOF,
    }


# ── Seed demo attestations ──────────────────────────────────────────────────

def _build_demo_attestations() -> None:
    from tenancy_v2 import DEFAULT_TENANT_ID
    from artifacts_registry import list_artifacts
    tid = DEFAULT_TENANT_ID
    arts = list_artifacts(tenant_id=tid)

    events = [
        ("mr-review-rev-101", "mr-review-complete", "alice",
         "sha256:input-mr-101", "sha256:output-mr-101"),
        ("incident-inc-sre-7", "incident-run-complete", "alice",
         "sha256:input-sre-7", "sha256:output-sre-7"),
        ("readiness-rdns-q1", "readiness-eval-complete", "carol",
         "sha256:input-rdns-q1", "sha256:output-rdns-q1"),
    ]
    for subject, stype, issued_by, inp, out in events:
        issue_attestation(tid, subject, stype, issued_by, inp, out)

    for art in arts[:3]:
        issue_attestation(
            tid,
            art["artifact_id"],
            "artifact-created",
            art["created_by"],
            art["sha256"],
            _sha({"artifact": art["artifact_id"], "created": True}),
        )


_build_demo_attestations()


# ── FastAPI router ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/attestations", tags=["attestations"])


@router.get("")
def api_list_attestations(tenant_id: Optional[str] = None, limit: int = 50):
    from tenancy_v2 import DEFAULT_TENANT_ID
    tid = tenant_id or DEFAULT_TENANT_ID
    return {
        "attestations": list_attestations(tid, limit),
        "tenant_id": tid,
        "chain_head": get_chain_head(tid),
    }


@router.get("/{attestation_id}")
def api_get_attestation(attestation_id: str, tenant_id: Optional[str] = None):
    try:
        return get_attestation(attestation_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/receipts-pack")
def api_receipts_pack(tenant_id: Optional[str] = None):
    from tenancy_v2 import DEFAULT_TENANT_ID
    tid = tenant_id or DEFAULT_TENANT_ID
    return build_receipts_pack(tid)
