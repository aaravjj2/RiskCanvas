"""
AuditV2 Module — Immutable, Hash-Chained Audit Log (v3.3+)

Each event is:
  - Sequentially numbered (event_id)
  - Timestamp-normalised in DEMO mode
  - Hash-chained: chain_hash = sha256(prev_hash + payload_hash + meta_canonical)
  - Verifiable: GET /audit/v2/verify walks the chain

Design decisions:
  - Pure in-memory store (reset per test via /audit/v2/reset)
  - No external dependencies; zero network in DEMO mode
  - Canonical JSON = json.dumps with sorted keys, no whitespace
"""

import hashlib
import json
import os
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# ── Constants ────────────────────────────────────────────────────────────────

_DEMO_TS = "2026-01-01T00:00:00+00:00"
_GENESIS_HASH = "0" * 64  # prev_hash for event 0

audit_v2_router = APIRouter(prefix="/audit/v2", tags=["audit-v2"])

# ── Helpers ───────────────────────────────────────────────────────────────────


def _demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def _canonical(obj: Any) -> str:
    """Deterministic JSON representation: sorted keys, no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── In-memory store ───────────────────────────────────────────────────────────

_store: List[Dict[str, Any]] = []
_store_lock = Lock()


def _current_chain_head() -> str:
    """Return the chain_hash of the most recent event, or genesis if empty."""
    if not _store:
        return _GENESIS_HASH
    return _store[-1]["chain_hash"]


# ── Public emit API ───────────────────────────────────────────────────────────

def emit_audit_v2(
    actor: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    workspace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Append a new audit event.  Returns the full event dict.
    Thread-safe via _store_lock.
    """
    with _store_lock:
        event_id = len(_store)
        ts = _DEMO_TS if _demo_mode() else __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

        payload_canonical = _canonical(payload or {})
        payload_hash = _sha256(payload_canonical)

        prev_hash = _store[-1]["chain_hash"] if _store else _GENESIS_HASH

        meta_canonical = _canonical({
            "event_id": event_id,
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "workspace_id": workspace_id,
            "ts_norm": ts,
        })
        chain_hash = _sha256(prev_hash + payload_hash + meta_canonical)

        event = {
            "event_id": event_id,
            "ts_norm": ts,
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "workspace_id": workspace_id,
            "payload_canonical_json": payload_canonical,
            "payload_hash": payload_hash,
            "prev_hash": prev_hash,
            "chain_hash": chain_hash,
        }
        _store.append(event)
        return event


def get_chain_head() -> str:
    """Return the current chain head hash (for provenance stamping)."""
    with _store_lock:
        return _current_chain_head()


def reset_store() -> None:
    """Clear the store (DEMO only / tests)."""
    with _store_lock:
        _store.clear()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AuditV2Event(BaseModel):
    event_id: int
    ts_norm: str
    actor: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    workspace_id: Optional[str]
    payload_canonical_json: str
    payload_hash: str
    prev_hash: str
    chain_hash: str


class AuditV2EventsResponse(BaseModel):
    events: List[AuditV2Event]
    total: int
    chain_head: str


class AuditV2ResetResponse(BaseModel):
    ok: bool
    message: str


class AuditV2VerifyResponse(BaseModel):
    ok: bool
    events_checked: int
    first_bad_event_id: Optional[int]
    chain_head: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@audit_v2_router.get("/events", response_model=AuditV2EventsResponse)
async def list_audit_v2_events(
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    since_event_id: Optional[int] = Query(None),
):
    """List audit events with optional filtering."""
    with _store_lock:
        events = list(_store)

    if workspace_id:
        events = [e for e in events if e.get("workspace_id") == workspace_id]
    if since_event_id is not None:
        events = [e for e in events if e["event_id"] > since_event_id]

    events = events[-limit:]  # tail

    return AuditV2EventsResponse(
        events=[AuditV2Event(**e) for e in events],
        total=len(events),
        chain_head=get_chain_head(),
    )


@audit_v2_router.post("/reset", response_model=AuditV2ResetResponse)
async def reset_audit_v2():
    """Reset the audit store. Only available in DEMO mode."""
    if not _demo_mode():
        raise HTTPException(status_code=403, detail="reset only available in DEMO mode")
    reset_store()
    return AuditV2ResetResponse(ok=True, message="audit store cleared")


@audit_v2_router.get("/verify", response_model=AuditV2VerifyResponse)
async def verify_audit_v2():
    """
    Walk the chain and verify every hash linkage.
    Returns ok=True if intact, else first_bad_event_id is set.
    """
    with _store_lock:
        events = list(_store)

    if not events:
        return AuditV2VerifyResponse(ok=True, events_checked=0, first_bad_event_id=None, chain_head=_GENESIS_HASH)

    first_bad: Optional[int] = None
    prev_chain = _GENESIS_HASH

    for ev in events:
        # Recompute chain_hash
        meta_canonical = _canonical({
            "event_id": ev["event_id"],
            "actor": ev["actor"],
            "action": ev["action"],
            "resource_type": ev["resource_type"],
            "resource_id": ev["resource_id"],
            "workspace_id": ev["workspace_id"],
            "ts_norm": ev["ts_norm"],
        })
        expected_chain = _sha256(prev_chain + ev["payload_hash"] + meta_canonical)

        if expected_chain != ev["chain_hash"] or ev["prev_hash"] != prev_chain:
            first_bad = ev["event_id"]
            break

        prev_chain = ev["chain_hash"]

    return AuditV2VerifyResponse(
        ok=first_bad is None,
        events_checked=len(events),
        first_bad_event_id=first_bad,
        chain_head=events[-1]["chain_hash"] if events else _GENESIS_HASH,
    )
