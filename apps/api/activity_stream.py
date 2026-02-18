"""
Activity Stream module (v4.1.0)

Deterministic activity event log for workspace collaboration feel.
All events are canonical JSON, seeded in DEMO mode, ordered by (workspace_id, seq).
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Canonical helpers
# ---------------------------------------------------------------------------

def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _norm_ts(seq: int, workspace_id: str = "demo") -> str:
    """Return a deterministic ISO-like timestamp from sequence + workspace."""
    base = _sha({"seq": seq, "ws": workspace_id})[:8]
    minute = (seq % 60)
    hour = (seq // 60) % 24
    return f"2026-02-18T{hour:02d}:{minute:02d}:00Z"


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

EVENT_TYPES = [
    "run.execute",
    "report.build",
    "job.submit",
    "policy.evaluate",
    "eval.suite_run",
    "sre.playbook_generate",
    "search.reindex",
    "presence.join",
    "presence.leave",
]

# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

class ActivityStore:
    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._seq: int = 0

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def emit(
        self,
        workspace_id: str,
        actor: str,
        event_type: str,
        message: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        seq = self._next_seq()
        ts = _norm_ts(seq, workspace_id)
        payload: Dict[str, Any] = {
            "event_id": seq,
            "workspace_id": workspace_id,
            "actor": actor,
            "type": event_type,
            "message": message,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "meta": meta or {},
            "ts": ts,
        }
        payload["event_hash"] = _sha(payload)
        self._events.append(payload)
        return payload

    def list(
        self,
        workspace_id: Optional[str] = None,
        limit: int = 50,
        since_event_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        events = self._events
        if workspace_id:
            events = [e for e in events if e["workspace_id"] == workspace_id]
        if since_event_id is not None:
            events = [e for e in events if e["event_id"] > since_event_id]
        # Ordered newest-first
        return list(reversed(events[-limit:])) if limit else list(reversed(events))

    def reset(self) -> None:
        self._events = []
        self._seq = 0


_store = ActivityStore()


def get_activity_store() -> ActivityStore:
    return _store


# ---------------------------------------------------------------------------
# DEMO seed data (called on /test/reset in DEMO mode)
# ---------------------------------------------------------------------------

DEMO_SEED: List[Dict[str, Any]] = [
    {"actor": "alice@demo", "type": "run.execute", "message": "Portfolio analysis run started",
     "resource_id": "run-demo-001", "resource_type": "run"},
    {"actor": "bob@demo", "type": "policy.evaluate", "message": "Policy evaluated: decision=ALLOW",
     "resource_id": "pol-demo-001", "resource_type": "policy"},
    {"actor": "alice@demo", "type": "report.build", "message": "Report bundle generated",
     "resource_id": "rep-demo-001", "resource_type": "report"},
    {"actor": "carol@demo", "type": "eval.suite_run", "message": "Eval suite governance_policy_suite passed 5/5",
     "resource_id": "eval-demo-001", "resource_type": "eval"},
    {"actor": "bob@demo", "type": "job.submit", "message": "Batch analysis job submitted",
     "resource_id": "job-demo-001", "resource_type": "job"},
    {"actor": "carol@demo", "type": "sre.playbook_generate", "message": "SRE playbook generated for P0 incident",
     "resource_id": "sre-demo-001", "resource_type": "sre_playbook"},
    {"actor": "alice@demo", "type": "run.execute", "message": "Stress scenario run completed",
     "resource_id": "run-demo-002", "resource_type": "run"},
    {"actor": "dave@demo", "type": "search.reindex", "message": "Search index rebuilt (7 types)",
     "resource_id": None, "resource_type": None},
]


def seed_demo_activity(workspace_id: str = "demo-workspace") -> List[Dict[str, Any]]:
    """Seed deterministic demo activity events. Idempotent (resets first)."""
    _store.reset()
    seeded = []
    for entry in DEMO_SEED:
        ev = _store.emit(
            workspace_id=workspace_id,
            actor=entry["actor"],
            event_type=entry["type"],
            message=entry["message"],
            resource_id=entry.get("resource_id"),
            resource_type=entry.get("resource_type"),
        )
        seeded.append(ev)
    return seeded


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

activity_router = APIRouter(prefix="/activity", tags=["activity"])

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


@activity_router.get("")
def list_activity(
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    since_event_id: Optional[int] = Query(None),
) -> JSONResponse:
    events = _store.list(workspace_id=workspace_id, limit=limit, since_event_id=since_event_id)
    return JSONResponse({"events": events, "count": len(events)})


@activity_router.post("/reset")
def reset_activity() -> JSONResponse:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if not demo_mode:
        raise HTTPException(status_code=403, detail="Activity reset only in DEMO mode")
    seeded = seed_demo_activity()
    return JSONResponse({"status": "ok", "seeded": len(seeded)})


# ---------------------------------------------------------------------------
# Convenience: emit from other modules
# ---------------------------------------------------------------------------

def emit_activity(
    workspace_id: str = "demo-workspace",
    actor: str = "system",
    event_type: str = "run.execute",
    message: str = "",
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _store.emit(
        workspace_id=workspace_id,
        actor=actor,
        event_type=event_type,
        message=message,
        resource_id=resource_id,
        resource_type=resource_type,
        meta=meta,
    )
