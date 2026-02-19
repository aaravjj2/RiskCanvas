"""
compliance_pack.py (v5.10.0-v5.13.0 — Wave 44)

SOC2-ish compliance pack generator — deterministic, offline.

Generates a stable zip manifest with:
  system_overview.md
  policy_snapshots.json
  readiness_evals.json
  incident_drill_runs.json
  audit_chain_head.txt
  attestations_chain_head.txt
  artifacts_manifest.json
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

_GENERATED_PACKS: Dict[str, Dict[str, Any]] = {}


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


_SYSTEM_OVERVIEW_TEMPLATE = """# RiskCanvas — System Overview

**Tenant:** {tenant_name}
**Generated:** {generated_at}
**Window:** {window}

## Architecture
- Backend: FastAPI (Python 3.10), port 8090
- Frontend: React 19 + Vite + TypeScript + Tailwind
- Database: SQLite (DEMO) / PostgreSQL (PROD)

## Key Controls
- Access Control: RBAC v2 (OWNER/ADMIN/ANALYST/VIEWER)
- Audit Trail: Dual-chain (audit_v2 + attestations)
- Policy Enforcement: Policy Registry v2
- Artifact Integrity: SHA-256 signed manifests
- Incident Response: Automated drills + runbooks

## Compliance posture
- SOC 2 Type I evidence window: {window}
- Controls evaluated: 12
- Controls passed: 11
- Controls failed: 1 (pending remediation)
"""


def generate_compliance_pack(
    tenant_id: str,
    window: str = "last_30_demo_days",
) -> Dict[str, Any]:
    from tenancy_v2 import get_tenant, DEFAULT_TENANT_ID
    from artifacts_registry import list_artifacts
    from attestations import list_attestations, get_chain_head

    tid = tenant_id or DEFAULT_TENANT_ID
    try:
        tenant = get_tenant(tid)
    except ValueError:
        tenant = {"name": "DEMO Tenant", "tenant_id": tid}

    arts = list_artifacts(tenant_id=tid)
    attestations = list_attestations(tid, limit=100)
    chain_head = get_chain_head(tid) or "genesis"

    # Deterministic policy snapshots
    policy_snapshots = [
        {"policy_id": _sha({"p": i, "t": tid})[:16], "name": f"POL-{i:03d}",
         "version": f"v{i}.0", "status": "active",
         "last_eval": ASOF, "passed": True}
        for i in range(1, 7)
    ]

    # Deterministic readiness snapshots
    readiness_evals = [
        {"eval_id": _sha({"r": i, "t": tid})[:16], "name": f"Readiness Q{i} 2026",
         "score": 80 + i * 2, "passed": True}
        for i in range(1, 4)
    ]

    # Deterministic incident drill runs
    drill_runs = [
        {"drill_id": _sha({"d": i, "t": tid})[:16], "name": f"SRE Drill {i}",
         "severity": "HIGH" if i % 2 == 0 else "MEDIUM",
         "completed": True, "mttr_minutes": 12 + i * 3}
        for i in range(1, 5)
    ]

    # Audit chain head (stable)
    from audit_v2 import get_chain_head as audit_get_chain_head
    audit_head = {"chain_head": audit_get_chain_head()}

    system_overview = _SYSTEM_OVERVIEW_TEMPLATE.format(
        tenant_name=tenant["name"],
        generated_at=ASOF,
        window=window,
    )

    files = [
        {"name": "system_overview.md", "content": system_overview,
         "sha256": _sha({"c": system_overview})[:16]},
        {"name": "policy_snapshots.json",
         "content": json.dumps(policy_snapshots, indent=2),
         "sha256": _sha({"c": policy_snapshots})[:16]},
        {"name": "readiness_evals.json",
         "content": json.dumps(readiness_evals, indent=2),
         "sha256": _sha({"c": readiness_evals})[:16]},
        {"name": "incident_drill_runs.json",
         "content": json.dumps(drill_runs, indent=2),
         "sha256": _sha({"c": drill_runs})[:16]},
        {"name": "audit_chain_head.txt",
         "content": json.dumps(audit_head, indent=2),
         "sha256": _sha({"c": audit_head})[:16]},
        {"name": "attestations_chain_head.txt",
         "content": chain_head,
         "sha256": _sha({"c": chain_head})[:16]},
        {"name": "artifacts_manifest.json",
         "content": json.dumps([
             {"artifact_id": a["artifact_id"], "type": a["type"], "sha256": a["sha256"]}
             for a in arts
         ], indent=2),
         "sha256": _sha({"c": [a["artifact_id"] for a in arts]})[:16]},
    ]

    payload = {
        "tenant_id": tid,
        "window": window,
        "file_names": [f["name"] for f in files],
    }
    pack_id = _sha(payload)[:32]
    manifest_hash = _sha({"pack_id": pack_id, "files": [f["sha256"] for f in files]})

    pack = {
        "pack_id": pack_id,
        "tenant_id": tid,
        "tenant_name": tenant["name"],
        "window": window,
        "generated_at": ASOF,
        "file_count": len(files),
        "files": files,
        "manifest_hash": manifest_hash,
        "artifact_refs": [a["artifact_id"] for a in arts],
        "attestation_count": len(attestations),
        "chain_head_hash": chain_head,
        "controls_evaluated": 12,
        "controls_passed": 11,
        "verdict": "PASS",
    }
    _GENERATED_PACKS[pack_id] = pack
    return pack


def verify_compliance_pack(pack_id: str) -> Dict[str, Any]:
    pack = _GENERATED_PACKS.get(pack_id)
    if not pack:
        raise ValueError(f"Pack not found: {pack_id}")
    # Recompute manifest hash
    expected = _sha({
        "pack_id": pack_id,
        "files": [f["sha256"] for f in pack["files"]]
    })
    matches = expected == pack["manifest_hash"]
    return {
        "pack_id": pack_id,
        "manifest_hash": pack["manifest_hash"],
        "recomputed_hash": expected,
        "verified": matches,
        "verdict": "PASS" if matches else "FAIL",
    }


def list_compliance_packs(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    packs = list(_GENERATED_PACKS.values())
    if tenant_id:
        packs = [p for p in packs if p["tenant_id"] == tenant_id]
    return sorted(packs, key=lambda p: p["pack_id"])


# ── FastAPI router ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/compliance", tags=["compliance"])


class GeneratePackRequest(BaseModel):
    tenant_id: Optional[str] = None
    window: str = "last_30_demo_days"


@router.post("/generate-pack")
def api_generate_pack(body: GeneratePackRequest = GeneratePackRequest()):
    from tenancy_v2 import DEFAULT_TENANT_ID
    tid = body.tenant_id or DEFAULT_TENANT_ID
    return generate_compliance_pack(tid, body.window)


@router.get("/packs")
def api_list_packs(tenant_id: Optional[str] = None):
    return {"packs": list_compliance_packs(tenant_id)}


@router.get("/packs/{pack_id}")
def api_get_pack(pack_id: str):
    pack = _GENERATED_PACKS.get(pack_id)
    if not pack:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Pack not found: {pack_id}")
    return pack


@router.post("/packs/{pack_id}/verify")
def api_verify_pack(pack_id: str):
    try:
        return verify_compliance_pack(pack_id)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
