"""
decision_rooms.py (v5.55.0 — Wave 66)

Decision Rooms v1 — collaboration hub where scenarios/runs/reviews/approvals/
attestations converge into a verifiable decision.

Room lifecycle:  OPEN → LOCKED → ARCHIVED
Locking a room issues an attestation "room.locked" referencing graph head hash.

Endpoints:
  GET  /rooms
  POST /rooms
  GET  /rooms/{id}
  POST /rooms/{id}/pin
  POST /rooms/{id}/lock
  GET  /rooms/{id}/timeline
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

router = APIRouter(prefix="/rooms", tags=["rooms"])

RoomStatus = Literal["OPEN", "LOCKED", "ARCHIVED"]

# ── Helpers ────────────────────────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _room_id(name: str, tenant_id: str) -> str:
    return "room-" + _sha256({"name": name, "tenant_id": tenant_id})[:12]


# ── In-memory store ────────────────────────────────────────────────────────────

_ROOMS: Dict[str, Dict[str, Any]] = {}
_ROOM_ATTESTATIONS: Dict[str, List[Dict[str, Any]]] = {}  # room_id -> attestations

# Seed demo rooms
_SEED_ROOMS = [
    {
        "room_id": "room-demo-001",
        "tenant_id": "demo-tenant",
        "name": "Feb 2026 Rate Shock Decision",
        "subject_type": "scenario",
        "subject_id": "scen-001",
        "status": "OPEN",
        "pinned_entities": ["scen-001", "run-001", "ds-prov-001"],
        "notes": "## Rate Shock +100bps\n\nReview required before execution.\n\n- Dataset: Demo Rates\n- Scenario: Rate Shock +100bps",
        "created_by": "demo-user",
        "created_at": ASOF,
        "updated_at": ASOF,
        "lock_hash": None,
    },
    {
        "room_id": "room-demo-002",
        "tenant_id": "demo-tenant",
        "name": "Credit Event EUR Decision",
        "subject_type": "scenario",
        "subject_id": "scen-002",
        "status": "OPEN",
        "pinned_entities": ["scen-002", "run-002", "ds-prov-002"],
        "notes": "## Credit Event EUR\n\nPending compliance review.",
        "created_by": "demo-user",
        "created_at": ASOF,
        "updated_at": ASOF,
        "lock_hash": None,
    },
]
for _r in _SEED_ROOMS:
    _ROOMS[_r["room_id"]] = _r
    _ROOM_ATTESTATIONS[_r["room_id"]] = []


# ── Request models ─────────────────────────────────────────────────────────────


class CreateRoomRequest(BaseModel):
    name: str
    tenant_id: str = "demo-tenant"
    subject_type: str = "scenario"
    subject_id: str = ""
    notes: str = ""
    created_by: str = "api-user"


class PinEntityRequest(BaseModel):
    entity_id: str
    entity_type: str = ""


class LockRoomRequest(BaseModel):
    locked_by: str = "api-user"
    reason: str = ""


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("")
def list_rooms(tenant_id: str = "demo-tenant"):
    rooms = [r for r in _ROOMS.values() if r["tenant_id"] == tenant_id]
    rooms_sorted = sorted(rooms, key=lambda r: r["created_at"])
    return {"rooms": rooms_sorted, "count": len(rooms_sorted)}


@router.post("")
def create_room(req: CreateRoomRequest):
    room_id = _room_id(req.name, req.tenant_id)
    if room_id in _ROOMS:
        return {"room": _ROOMS[room_id], "status": "exists"}
    room: Dict[str, Any] = {
        "room_id": room_id,
        "tenant_id": req.tenant_id,
        "name": req.name,
        "subject_type": req.subject_type,
        "subject_id": req.subject_id,
        "status": "OPEN",
        "pinned_entities": [],
        "notes": req.notes,
        "created_by": req.created_by,
        "created_at": ASOF,
        "updated_at": ASOF,
        "lock_hash": None,
    }
    _ROOMS[room_id] = room
    _ROOM_ATTESTATIONS[room_id] = []
    return {"room": room, "status": "created"}


@router.get("/{room_id}")
def get_room(room_id: str):
    room = _ROOMS.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    attestations = _ROOM_ATTESTATIONS.get(room_id, [])
    return {"room": room, "attestations": attestations}


@router.get("/{room_id}/timeline")
def get_room_timeline(room_id: str):
    room = _ROOMS.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    # Build timeline entries from pinned entities
    timeline = []
    for entity_id in room["pinned_entities"]:
        timeline.append({
            "entity_id": entity_id,
            "pinned_at": ASOF,
            "pinned_by": room["created_by"],
        })
    attestations = _ROOM_ATTESTATIONS.get(room_id, [])
    return {
        "room_id": room_id,
        "timeline": timeline,
        "attestations": attestations,
    }


@router.post("/{room_id}/pin")
def pin_entity(room_id: str, req: PinEntityRequest):
    room = _ROOMS.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    if room["status"] == "LOCKED":
        raise HTTPException(status_code=409, detail="Room is LOCKED and cannot be modified")
    if req.entity_id not in room["pinned_entities"]:
        room["pinned_entities"].append(req.entity_id)
    return {"room_id": room_id, "pinned_entities": room["pinned_entities"]}


@router.post("/{room_id}/lock")
def lock_room(room_id: str, req: LockRoomRequest):
    room = _ROOMS.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    if room["status"] == "LOCKED":
        # Return existing attestation for idempotency
        existing = next(
            (a for a in _ROOM_ATTESTATIONS.get(room_id, []) if a.get("event") == "room.locked"),
            None,
        )
        if not existing:
            graph_head = room.get("lock_hash") or _sha256({"room_id": room_id})
            existing = {
                "attestation_id": "attest-" + graph_head[:12],
                "room_id": room_id,
                "event": "room.locked",
                "graph_head_hash": graph_head,
                "locked_by": req.locked_by or "system",
                "reason": req.reason or "already locked",
                "locked_at": ASOF,
            }
        return {"room": room, "attestation": existing, "status": "already_locked"}

    # Compute graph head hash (deterministic, based on room state)
    graph_head = _sha256({
        "room_id": room_id,
        "pinned_entities": sorted(room["pinned_entities"]),
        "notes": room["notes"],
        "subject_id": room["subject_id"],
    })
    room["status"] = "LOCKED"
    room["lock_hash"] = graph_head

    # Issue "room.locked" attestation
    attestation = {
        "attestation_id": "attest-" + graph_head[:12],
        "room_id": room_id,
        "event": "room.locked",
        "graph_head_hash": graph_head,
        "locked_by": req.locked_by,
        "reason": req.reason,
        "locked_at": ASOF,
    }
    _ROOM_ATTESTATIONS[room_id].append(attestation)

    return {"room": room, "attestation": attestation, "status": "locked"}
