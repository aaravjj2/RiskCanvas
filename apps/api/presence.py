"""
Presence module (v4.1.0)

Deterministic presence state for workspace collaboration feel.
DEMO: seeded static presence list, no real clocks.
LOCAL/PROD: explicit endpoint updates only — no websockets required.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------

STATUS_ONLINE = "online"
STATUS_IDLE = "idle"
STATUS_OFFLINE = "offline"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _demo_last_seen(actor: str) -> str:
    base = _sha({"actor": actor, "pin": "presence"})[:6]
    minutes_ago = int(base, 16) % 15  # 0-14 minutes ago
    return f"2026-02-18T11:{(30 - minutes_ago) % 60:02d}:00Z"


# ---------------------------------------------------------------------------
# DEMO seed data
# ---------------------------------------------------------------------------

DEMO_PRESENCE: List[Dict[str, Any]] = [
    {"actor": "alice@demo", "display": "Alice", "status": STATUS_ONLINE},
    {"actor": "bob@demo", "display": "Bob", "status": STATUS_ONLINE},
    {"actor": "carol@demo", "display": "Carol", "status": STATUS_IDLE},
    {"actor": "dave@demo", "display": "Dave", "status": STATUS_OFFLINE},
]


# ---------------------------------------------------------------------------
# In-memory presence store
# ---------------------------------------------------------------------------

class PresenceStore:
    def __init__(self) -> None:
        self._state: Dict[str, Dict[str, Any]] = {}

    def update(
        self,
        workspace_id: str,
        actor: str,
        status: str,
        display: Optional[str] = None,
        last_seen_norm: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = f"{workspace_id}:{actor}"
        record = {
            "workspace_id": workspace_id,
            "actor": actor,
            "display": display or actor.split("@")[0].capitalize(),
            "status": status,
            "last_seen_norm": last_seen_norm or _demo_last_seen(actor),
        }
        record["presence_hash"] = _sha(record)
        self._state[key] = record
        return record

    def list(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = list(self._state.values())
        if workspace_id:
            records = [r for r in records if r["workspace_id"] == workspace_id]
        # Stable ordering: online first, then idle, then offline; then alpha
        order = {STATUS_ONLINE: 0, STATUS_IDLE: 1, STATUS_OFFLINE: 2}
        return sorted(records, key=lambda r: (order.get(r["status"], 9), r["actor"]))

    def reset(self) -> None:
        self._state = {}


_store = PresenceStore()


def get_presence_store() -> PresenceStore:
    return _store


def seed_demo_presence(workspace_id: str = "demo-workspace") -> List[Dict[str, Any]]:
    """Seed deterministic demo presence. Idempotent."""
    _store.reset()
    seeded = []
    for entry in DEMO_PRESENCE:
        rec = _store.update(
            workspace_id=workspace_id,
            actor=entry["actor"],
            display=entry["display"],
            status=entry["status"],
            last_seen_norm=_demo_last_seen(entry["actor"]),
        )
        seeded.append(rec)
    return seeded


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

presence_router = APIRouter(prefix="/presence", tags=["presence"])


class PresenceUpdateRequest(BaseModel):
    workspace_id: str
    actor: str
    status: str  # online | idle | offline
    display: Optional[str] = None


@presence_router.get("")
def get_presence(workspace_id: Optional[str] = Query(None)) -> JSONResponse:
    records = _store.list(workspace_id=workspace_id)
    online = sum(1 for r in records if r["status"] == STATUS_ONLINE)
    idle = sum(1 for r in records if r["status"] == STATUS_IDLE)
    return JSONResponse({
        "presence": records,
        "count": len(records),
        "online_count": online,
        "idle_count": idle,
    })


@presence_router.post("/update")
def update_presence(req: PresenceUpdateRequest) -> JSONResponse:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if demo_mode:
        # In DEMO mode: presence is seeded and static. No-op but deterministic.
        existing = _store.list(workspace_id=req.workspace_id)
        for r in existing:
            if r["actor"] == req.actor:
                return JSONResponse({"status": "no-op", "demo_mode": True, "record": r})
        # If not found (new actor in DEMO), add them
        record = _store.update(
            workspace_id=req.workspace_id,
            actor=req.actor,
            status=req.status,
            display=req.display,
        )
        return JSONResponse({"status": "ok", "record": record})

    if req.status not in (STATUS_ONLINE, STATUS_IDLE, STATUS_OFFLINE):
        raise HTTPException(status_code=400, detail=f"Invalid status: {req.status}")
    record = _store.update(
        workspace_id=req.workspace_id,
        actor=req.actor,
        status=req.status,
        display=req.display,
    )
    return JSONResponse({"status": "ok", "record": record})
