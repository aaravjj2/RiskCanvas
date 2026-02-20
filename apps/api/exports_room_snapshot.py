"""
exports_room_snapshot.py (v5.59.0 — Wave 70)

Exports Hub v2 — Room Snapshot export type.

A room_snapshot.zip includes:
  - pinned entity JSON
  - evidence graph slice
  - notes + decisions
  - attestations head hashes
  - stable manifest with hash

Endpoints:
  POST /exports/room-snapshot
  GET  /exports/room-snapshots
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

router = APIRouter(prefix="/exports", tags=["exports-room-snapshot"])

# ── In-memory snapshot store ───────────────────────────────────────────────────

_SNAPSHOTS: Dict[str, Dict[str, Any]] = {}


def _sha256(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _manifest_hash(room_id: str, entities: List[str], notes: str, attestations: List) -> str:
    return _sha256({
        "room_id": room_id,
        "entities": sorted(entities),
        "notes": notes,
        "attestations": attestations,
    })[:24]


# ── Request models ─────────────────────────────────────────────────────────────


class RoomSnapshotRequest(BaseModel):
    room_id: str
    include_graph_slice: bool = True
    include_notes: bool = True
    tenant_id: str = "demo-tenant"


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post("/room-snapshot")
def generate_room_snapshot(req: RoomSnapshotRequest):
    """Generate a deterministic room snapshot export."""
    # Pull room data (import dynamically)
    try:
        from decision_rooms import _ROOMS, _ROOM_ATTESTATIONS  # type: ignore
        room = _ROOMS.get(req.room_id)
        attestations = _ROOM_ATTESTATIONS.get(req.room_id, [])
    except ImportError:
        room = None
        attestations = []

    if room is None:
        # Demo fallback
        room = {
            "room_id": req.room_id,
            "name": f"Demo Room {req.room_id}",
            "subject_id": "scen-001",
            "pinned_entities": ["scen-001", "run-001", "ds-prov-001"],
            "notes": "Demo room snapshot",
            "status": "LOCKED",
            "lock_hash": "demo-lock-hash-001",
        }
        attestations = []

    # Pull graph slice
    graph_slice = {}
    if req.include_graph_slice:
        try:
            from evidence_graph import _GRAPH_NODES, _GRAPH_EDGES  # type: ignore
            pinned = room.get("pinned_entities", [])
            nodes = [n for n in _GRAPH_NODES.values() if n["node_id"] in pinned]
            edges = [e for e in _GRAPH_EDGES.values()
                     if e["src"] in pinned or e["dst"] in pinned]
            graph_slice = {
                "nodes": sorted(nodes, key=lambda n: n["node_id"]),
                "edges": sorted(edges, key=lambda e: e["edge_id"]),
            }
        except ImportError:
            graph_slice = {"nodes": [], "edges": []}

    notes = room.get("notes", "") if req.include_notes else ""
    pinned_entities = room.get("pinned_entities", [])

    # Build manifest
    manifest_hash = _manifest_hash(
        req.room_id, pinned_entities, notes, attestations
    )
    snapshot_id = "snap-" + manifest_hash[:12]

    # Build zip manifest (stable, no actual zip needed in DEMO)
    zip_manifest: Dict[str, Any] = {
        "snapshot_id": snapshot_id,
        "room_id": req.room_id,
        "room_name": room.get("name", req.room_id),
        "tenant_id": req.tenant_id,
        "manifest_hash": manifest_hash,
        "files": {
            "room.json": _sha256(room)[:16],
            "graph_slice.json": _sha256(graph_slice)[:16] if graph_slice else None,
            "notes.md": _sha256(notes)[:16],
            "attestations.json": _sha256(attestations)[:16],
        },
        "pinned_entity_count": len(pinned_entities),
        "attestation_count": len(attestations),
        "lock_hash": room.get("lock_hash"),
        "graph_slice": graph_slice,
        "attestations": attestations,
        "created_at": ASOF,
    }

    _SNAPSHOTS[snapshot_id] = zip_manifest
    return {"snapshot": zip_manifest, "status": "generated"}


@router.get("/room-snapshots")
def list_room_snapshots(tenant_id: str = "demo-tenant"):
    snaps = list(_SNAPSHOTS.values())
    return {"snapshots": snaps, "count": len(snaps)}
