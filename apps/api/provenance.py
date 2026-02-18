"""
Provenance Module (v3.3+)

Every run/report/job/policy result exposes:
  - input_hash   : sha256 of canonical input JSON
  - output_hash  : sha256 of canonical output JSON
  - audit_chain_head_hash : chain head at time of creation
  - tool_call_hashes : list of hashes (empty if not applicable)

The provenance store is an in-memory dict keyed by (kind, id).

GET /provenance/{kind}/{id}  →  ProvenanceRecord
"""

import hashlib
import json
import os
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from audit_v2 import get_chain_head, emit_audit_v2

provenance_router = APIRouter(prefix="/provenance", tags=["provenance"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_payload(payload: Any) -> str:
    """Hash any JSON-serialisable payload (canonical)."""
    return _sha256(_canonical(payload))


# ── Store ─────────────────────────────────────────────────────────────────────

_prov_store: Dict[str, Dict[str, Any]] = {}   # key: "{kind}/{id}"
_prov_lock = Lock()

VALID_KINDS = {"run", "report", "job", "policy"}


def record_provenance(
    kind: str,
    resource_id: str,
    input_payload: Any,
    output_payload: Any,
    tool_call_hashes: Optional[List[str]] = None,
    related_audit_event_ids: Optional[List[int]] = None,
    actor: str = "system",
) -> Dict[str, Any]:
    """
    Create + store a provenance record.  Returns the full record dict.
    Also emits an audit_v2 event.
    """
    if kind not in VALID_KINDS:
        raise ValueError(f"kind must be one of {VALID_KINDS}")

    input_hash = hash_payload(input_payload)
    output_hash = hash_payload(output_payload)
    chain_head = get_chain_head()

    record = {
        "kind": kind,
        "resource_id": resource_id,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "audit_chain_head_hash": chain_head,
        "tool_call_hashes": tool_call_hashes or [],
        "related_audit_event_ids": related_audit_event_ids or [],
        "lineage": {
            "kind": kind,
            "resource_id": resource_id,
            "input_canonical": _canonical(input_payload)[:256],  # truncated for size
        },
    }

    key = f"{kind}/{resource_id}"
    with _prov_lock:
        _prov_store[key] = record

    # Emit audit event for provenance creation
    emit_audit_v2(
        actor=actor,
        action="provenance.record",
        resource_type=kind,
        resource_id=resource_id,
        payload={"input_hash": input_hash, "output_hash": output_hash, "chain_head": chain_head},
    )

    return record


def get_provenance(kind: str, resource_id: str) -> Optional[Dict[str, Any]]:
    key = f"{kind}/{resource_id}"
    with _prov_lock:
        return _prov_store.get(key)


def reset_provenance_store() -> None:
    """For tests (DEMO only)."""
    with _prov_lock:
        _prov_store.clear()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProvenanceRecord(BaseModel):
    kind: str
    resource_id: str
    input_hash: str
    output_hash: str
    audit_chain_head_hash: str
    tool_call_hashes: List[str]
    related_audit_event_ids: List[int]
    lineage: Dict[str, Any]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@provenance_router.get("/{kind}/{resource_id}", response_model=ProvenanceRecord)
async def get_provenance_record(kind: str, resource_id: str):
    """Retrieve provenance record for a given kind + id."""
    if kind not in VALID_KINDS:
        raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(VALID_KINDS)}")

    rec = get_provenance(kind, resource_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Provenance record not found: {kind}/{resource_id}")

    return ProvenanceRecord(**rec)
