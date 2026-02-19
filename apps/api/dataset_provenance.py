"""
dataset_provenance.py (v5.47.0 — Wave 58)

Dataset Provenance — adds provenance fields to datasets and enforces
license compliance in DEMO mode.

Provenance fields (per dataset):
  source_type: synthetic | upload | generated | harvested
  source_note: human description of origin
  license_tag: CC0 | MIT | PROPRIETARY | DEMO | APACHE2
  checksum: sha256 of canonical dataset JSON
  ingest_user: who ingested it
  ingest_time: ISO-8601 deterministic

DEMO mode restrictions:
  - Only ALLOWED_DEMO_LICENSES may be ingested / used
  - Attempting to use PROPRIETARY in DEMO raises 403

Endpoints:
  GET  /provenance/datasets              — list all datasets with provenance
  GET  /provenance/datasets/{id}         — single dataset + provenance
  POST /provenance/datasets              — ingest dataset with provenance
  GET  /provenance/datasets/{id}/license — license compliance check
  GET  /provenance/summary               — aggregate stats
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

ALLOWED_DEMO_LICENSES = {"CC0", "MIT", "DEMO", "APACHE2"}
ALL_LICENSES = {"CC0", "MIT", "PROPRIETARY", "DEMO", "APACHE2"}

PROVENANCE_STORE: Dict[str, Dict[str, Any]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _checksum(data: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()


def _license_compliant(license_tag: str) -> bool:
    if DEMO_MODE and license_tag not in ALLOWED_DEMO_LICENSES:
        return False
    return True


# ── Core functions ─────────────────────────────────────────────────────────────


def ingest_dataset(
    dataset_id: str,
    name: str,
    kind: str,
    source_type: str,
    source_note: str,
    license_tag: str,
    rows: int,
    ingest_user: str = "system@riskcanvas.io",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if license_tag not in ALL_LICENSES:
        raise ValueError(f"Unknown license_tag: {license_tag}")

    if not _license_compliant(license_tag):
        raise PermissionError(
            f"License '{license_tag}' is not permitted in DEMO mode. "
            f"Allowed: {sorted(ALLOWED_DEMO_LICENSES)}"
        )

    canonical = {
        "id": dataset_id,
        "name": name,
        "kind": kind,
        "source_type": source_type,
        "rows": rows,
        **(extra or {}),
    }
    checksum = _checksum(canonical)

    record = {
        "dataset_id": dataset_id,
        "name": name,
        "kind": kind,
        "rows": rows,
        "source_type": source_type,
        "source_note": source_note,
        "license_tag": license_tag,
        "checksum": checksum,
        "ingest_user": ingest_user,
        "ingest_time": ASOF,
        "license_compliant": True,
        "demo_mode": DEMO_MODE,
        **(extra or {}),
    }
    PROVENANCE_STORE[dataset_id] = record
    return record


def get_dataset_provenance(dataset_id: str) -> Dict[str, Any]:
    if dataset_id not in PROVENANCE_STORE:
        raise ValueError(f"Dataset not found: {dataset_id}")
    return PROVENANCE_STORE[dataset_id]


def list_datasets(limit: int = 100) -> List[Dict[str, Any]]:
    return list(PROVENANCE_STORE.values())[:limit]


def get_license_compliance(dataset_id: str) -> Dict[str, Any]:
    rec = get_dataset_provenance(dataset_id)
    return {
        "dataset_id": dataset_id,
        "license_tag": rec["license_tag"],
        "compliant": _license_compliant(rec["license_tag"]),
        "demo_mode": DEMO_MODE,
        "allowed_demo_licenses": sorted(ALLOWED_DEMO_LICENSES),
        "check_at": ASOF,
    }


def get_summary() -> Dict[str, Any]:
    records = list(PROVENANCE_STORE.values())
    by_license: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for r in records:
        by_license[r["license_tag"]] = by_license.get(r["license_tag"], 0) + 1
        by_source[r["source_type"]] = by_source.get(r["source_type"], 0) + 1

    return {
        "total": len(records),
        "by_license": by_license,
        "by_source_type": by_source,
        "demo_mode": DEMO_MODE,
        "summary_at": ASOF,
    }


# ── Demo seed ──────────────────────────────────────────────────────────────────


def _seed() -> None:
    if PROVENANCE_STORE:
        return

    seeds = [
        ("ds-prov-001", "Demo Rates Dataset", "rates", "synthetic",
         "Synthetically generated SOFR rate curves", "DEMO", 5000),
        ("ds-prov-002", "Credit Spreads (DEMO)", "credit", "generated",
         "Auto-generated credit spread matrix for demo", "CC0", 1200),
        ("ds-prov-003", "FX Forwards (MIT)", "fx", "harvested",
         "Historical FX forward curves under MIT license", "MIT", 3600),
        ("ds-prov-004", "Liquidity Metrics", "liquidity", "synthetic",
         "Synthetic daily liquidity snapshots", "DEMO", 720),
        ("ds-prov-005", "Stress Test Scenarios", "stress", "generated",
         "Basel stress scenario matrix", "APACHE2", 200),
    ]
    for args in seeds:
        ingest_dataset(*args)


_seed()


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/provenance", tags=["dataset-provenance"])


class IngestRequest(BaseModel):
    dataset_id: Optional[str] = None
    name: str
    kind: str
    source_type: str
    source_note: str
    license_tag: str
    rows: int = 0
    ingest_user: str = "api@riskcanvas.io"


@router.get("/datasets")
def http_list_datasets(limit: int = 100):
    return {"datasets": list_datasets(limit=limit), "count": len(PROVENANCE_STORE)}


@router.get("/datasets/{dataset_id}")
def http_get_dataset(dataset_id: str):
    try:
        return {"dataset": get_dataset_provenance(dataset_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/datasets")
def http_ingest_dataset(req: IngestRequest):
    dataset_id = req.dataset_id or f"ds-{uuid.uuid4().hex[:12]}"
    try:
        record = ingest_dataset(
            dataset_id=dataset_id,
            name=req.name,
            kind=req.kind,
            source_type=req.source_type,
            source_note=req.source_note,
            license_tag=req.license_tag,
            rows=req.rows,
            ingest_user=req.ingest_user,
        )
        return {"dataset": record}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets/{dataset_id}/license")
def http_license_compliance(dataset_id: str):
    try:
        return get_license_compliance(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/summary")
def http_summary():
    return get_summary()
