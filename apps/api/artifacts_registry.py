"""
artifacts_registry.py (v5.02.0-v5.04.0 — Wave 42)

Artifact lifecycle: jobs produce signed, verifiable artifacts.

Artifact:
  artifact_id (sha256), tenant_id, type, created_by, source_job_id,
  size, sha256, storage_key, manifest

Types: mr-review-pack, incident-pack, readiness-memo, compliance-pack,
       export-bundle, attestation-chain
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _make_artifact(
    tenant_id: str,
    artifact_type: str,
    created_by: str,
    source_job_id: str,
    content: Any,
    manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    content_json = json.dumps(content, sort_keys=True, ensure_ascii=True)
    sha = hashlib.sha256(content_json.encode()).hexdigest()
    payload = {
        "tenant_id": tenant_id,
        "type": artifact_type,
        "created_by": created_by,
        "source_job_id": source_job_id,
        "sha256": sha,
    }
    artifact_id = _sha(payload)[:32]
    size = len(content_json.encode())
    art = {
        "artifact_id": artifact_id,
        "tenant_id": tenant_id,
        "type": artifact_type,
        "created_by": created_by,
        "source_job_id": source_job_id,
        "size": size,
        "sha256": sha,
        "storage_key": f"demo/{tenant_id}/{artifact_type}/{artifact_id[:8]}",
        "manifest": manifest or {"file_count": 1, "content_type": "application/json"},
        "created_at": ASOF,
        "verified": True,
        "download_url": f"/artifacts/{artifact_id}/downloads",
    }
    return art


# ── Seed demo artifacts ──────────────────────────────────────────────────────

def _build_demo_artifacts() -> None:
    from tenancy_v2 import DEFAULT_TENANT_ID
    tid = DEFAULT_TENANT_ID

    artifact_defs = [
        ("mr-review-pack", "alice", "job-mr-review-101",
         {"review_id": "rev-101", "verdict": "BLOCK", "findings": 3},
         {"files": ["trace.json", "findings.json", "recommendations.json", "diff.txt"]}),
        ("incident-pack", "alice", "job-incident-sre-7",
         {"incident_id": "inc-sre-7", "severity": "HIGH", "rca_complete": True},
         {"files": ["runbook.json", "timeline.json", "evidence.json"]}),
        ("readiness-memo", "carol", "job-readiness-q1",
         {"readiness_id": "rdns-q1", "score": 87, "passed": True},
         {"files": ["memo.pdf", "checklist.json"]}),
        ("compliance-pack", "alice", "job-compliance-feb",
         {"window": "last_30_demo_days", "controls": 12, "passed": 11},
         {"files": ["system_overview.md", "policy_snapshots.json",
                    "readiness_evals.json", "audit_chain_head.txt",
                    "attestations_chain_head.txt", "artifacts_manifest.json"]}),
        ("export-bundle", "bob", "job-export-w33-40",
         {"pack_id": "pack-judge-w26-32-final", "verified": True},
         {"files": ["bundle.json", "manifest.json"]}),
    ]

    for art_type, creator, job_id, content, manifest in artifact_defs:
        art = _make_artifact(tid, art_type, creator, job_id, content, manifest)
        DEMO_REGISTRY[art["artifact_id"]] = art


_build_demo_artifacts()


# ── Public API functions ─────────────────────────────────────────────────────

def create_artifact(
    tenant_id: str,
    artifact_type: str,
    created_by: str,
    source_job_id: str,
    content: Any,
    manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    art = _make_artifact(tenant_id, artifact_type, created_by,
                         source_job_id, content, manifest)
    DEMO_REGISTRY[art["artifact_id"]] = art
    return art


def list_artifacts(
    tenant_id: Optional[str] = None,
    artifact_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    arts = list(DEMO_REGISTRY.values())
    if tenant_id:
        arts = [a for a in arts if a["tenant_id"] == tenant_id]
    if artifact_type:
        arts = [a for a in arts if a["type"] == artifact_type]
    arts.sort(key=lambda a: (a["type"], a["artifact_id"]))
    return arts[:limit]


def get_artifact(artifact_id: str) -> Dict[str, Any]:
    a = DEMO_REGISTRY.get(artifact_id)
    if not a:
        raise ValueError(f"Artifact not found: {artifact_id}")
    return a


def get_download_descriptor(artifact_id: str) -> Dict[str, Any]:
    a = get_artifact(artifact_id)
    desc_payload = {"artifact_id": artifact_id, "type": "download", "mode": "demo"}
    descriptor_id = _sha(desc_payload)[:24]
    return {
        "descriptor_id": descriptor_id,
        "artifact_id": artifact_id,
        "url": f"/demo/downloads/{artifact_id[:8]}",
        "sha256": a["sha256"],
        "size": a["size"],
        "content_type": "application/zip",
        "expires_at": "2099-12-31T23:59:59Z",
        "mode": "DEMO",
        "note": "In production, this would be an Azure Blob SAS URL",
    }


# ── FastAPI router ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("")
def api_list_artifacts(
    tenant_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50,
):
    arts = list_artifacts(tenant_id, type, limit)
    return {"artifacts": arts, "count": len(arts)}


@router.get("/{artifact_id}")
def api_get_artifact(artifact_id: str):
    try:
        return get_artifact(artifact_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{artifact_id}/downloads")
def api_get_downloads(artifact_id: str):
    try:
        return get_download_descriptor(artifact_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
