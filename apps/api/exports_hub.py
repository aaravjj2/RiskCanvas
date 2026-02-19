"""
exports_hub.py  (v4.80.0 — Wave 34)

Exports Hub: browse, verify, and download recent export packs.
All responses are deterministic DEMO fixtures.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import datetime

router = APIRouter(prefix="/exports", tags=["exports-hub"])

# ─── Deterministic fixture data ───────────────────────────────────────────────

_DEMO_EXPORTS = [
    {
        "pack_id": "pack-mr-101-v53",
        "type": "mr-review",
        "label": "MR-101 Review Pack",
        "created_at": "2026-02-19T08:00:00Z",
        "sha256": "a3f4e2b1c9d7f6e5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1",
        "size_bytes": 42810,
        "status": "verified",
        "wave": "w26",
    },
    {
        "pack_id": "pack-incident-sre-drill-7",
        "type": "incident-drill",
        "label": "SRE Drill — Incident #7",
        "created_at": "2026-02-19T08:15:00Z",
        "sha256": "b4a5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5",
        "size_bytes": 18240,
        "status": "verified",
        "wave": "w27",
    },
    {
        "pack_id": "pack-readiness-2026-02-19",
        "type": "release-readiness",
        "label": "Release Readiness 2026-02-19",
        "created_at": "2026-02-19T09:00:00Z",
        "sha256": "c5b6a7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6",
        "size_bytes": 9120,
        "status": "verified",
        "wave": "w28",
    },
    {
        "pack_id": "pack-judge-w26-32-final",
        "type": "judge-pack",
        "label": "Judge Pack W26-32 (Final)",
        "created_at": "2026-02-19T10:30:00Z",
        "sha256": "d6c7b8a9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7",
        "size_bytes": 1353,
        "status": "verified",
        "wave": "w32",
    },
    {
        "pack_id": "pack-policy-v2-head",
        "type": "policy-v2",
        "label": "Policy Registry V2 Export",
        "created_at": "2026-02-19T11:00:00Z",
        "sha256": "e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1d2c3b4a5f6e7d8",
        "size_bytes": 3840,
        "status": "verified",
        "wave": "w30",
    },
]

# ─── API Models ───────────────────────────────────────────────────────────────

class ExportPackSummary(BaseModel):
    pack_id: str
    type: str
    label: str
    created_at: str
    sha256: str
    size_bytes: int
    status: str
    wave: str


class RecentExportsResponse(BaseModel):
    packs: List[ExportPackSummary]
    total: int
    generated_at: str


class VerifyResponse(BaseModel):
    pack_id: str
    verified: bool
    sha256: str
    message: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/recent", response_model=RecentExportsResponse)
def get_recent_exports():
    """Return recent export packs (deterministic DEMO fixtures)."""
    return RecentExportsResponse(
        packs=[ExportPackSummary(**p) for p in _DEMO_EXPORTS],
        total=len(_DEMO_EXPORTS),
        generated_at="2026-02-19T12:00:00Z",
    )


@router.get("/verify/{pack_id}", response_model=VerifyResponse)
def verify_pack(pack_id: str):
    """Verify a pack by ID — always verified in DEMO mode."""
    pack = next((p for p in _DEMO_EXPORTS if p["pack_id"] == pack_id), None)
    if pack is None:
        return VerifyResponse(
            pack_id=pack_id,
            verified=False,
            sha256="",
            message="Pack not found in DEMO fixtures",
        )
    return VerifyResponse(
        pack_id=pack_id,
        verified=True,
        sha256=pack["sha256"],
        message="Verified (DEMO mode — deterministic fixture)",
    )
