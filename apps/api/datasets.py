"""
datasets.py (v5.22.0-v5.25.0 — Wave 49)

Dataset Ingestion v1: Portfolios, Rates Curves, Stress Presets, FX Sets, Credit Curves.

Dataset model:
  dataset_id (sha256), tenant_id, kind, name, schema_version,
  sha256, storage_key, manifest, created_by, created_at, row_count

Kinds: portfolio | rates_curve | stress_preset | fx_set | credit_curve

All IDs and hashes are deterministic — same input → same output.
No external network calls.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# ── In-memory DEMO registry ─────────────────────────────────────────────────

DATASET_STORE: Dict[str, Dict[str, Any]] = {}

# ── Deterministic helpers ────────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _canonical(data: Any) -> str:
    """Canonical JSON: sorted keys, no extra whitespace."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


# ── Validation rules per kind ────────────────────────────────────────────────

REQUIRED_FIELDS: Dict[str, List[str]] = {
    "portfolio": ["positions"],
    "rates_curve": ["curve_date", "tenor_points"],
    "stress_preset": ["name", "shocks"],
    "fx_set": ["base_currency", "pairs"],
    "credit_curve": ["issuer", "tenor_points"],
}

SCHEMA_VERSIONS: Dict[str, str] = {
    "portfolio": "1.0",
    "rates_curve": "1.0",
    "stress_preset": "1.0",
    "fx_set": "1.0",
    "credit_curve": "1.0",
}


def _validate_payload(kind: str, payload: Any) -> List[Dict[str, str]]:
    """
    Validate payload for a given kind.
    Returns list of {path, message} dicts (empty = valid).
    Deterministic: same input → same errors in same order.
    """
    errors: List[Dict[str, str]] = []

    if not isinstance(payload, dict):
        errors.append({"path": "$", "message": "payload must be a JSON object"})
        return errors

    required = REQUIRED_FIELDS.get(kind, [])
    for field in sorted(required):
        if field not in payload:
            errors.append({"path": f"$.{field}", "message": f"required field '{field}' is missing"})

    if kind == "portfolio":
        positions = payload.get("positions", [])
        if not isinstance(positions, list):
            errors.append({"path": "$.positions", "message": "must be an array"})
        else:
            for idx, pos in enumerate(positions):
                if not isinstance(pos, dict):
                    errors.append({"path": f"$.positions[{idx}]", "message": "must be an object"})
                    continue
                for f in ["ticker", "quantity", "cost_basis"]:
                    if f not in pos:
                        errors.append({"path": f"$.positions[{idx}].{f}", "message": f"required field '{f}' missing"})

    elif kind == "rates_curve":
        tp = payload.get("tenor_points", [])
        if not isinstance(tp, list):
            errors.append({"path": "$.tenor_points", "message": "must be an array"})
        elif len(tp) == 0:
            errors.append({"path": "$.tenor_points", "message": "must have at least one tenor point"})

    elif kind == "stress_preset":
        shocks = payload.get("shocks", {})
        if not isinstance(shocks, dict):
            errors.append({"path": "$.shocks", "message": "must be an object of factor→delta mappings"})

    elif kind == "fx_set":
        pairs = payload.get("pairs", {})
        if not isinstance(pairs, dict):
            errors.append({"path": "$.pairs", "message": "must be an object of ccyPair→rate"})

    elif kind == "credit_curve":
        tp = payload.get("tenor_points", [])
        if not isinstance(tp, list):
            errors.append({"path": "$.tenor_points", "message": "must be an array"})
        elif len(tp) == 0:
            errors.append({"path": "$.tenor_points", "message": "must have at least one tenor point"})

    return errors


def _count_rows(kind: str, payload: Any) -> int:
    """Return row count: number of positions/pairs/tenor points etc."""
    if not isinstance(payload, dict):
        return 0
    if kind == "portfolio":
        return len(payload.get("positions", []))
    if kind in ("rates_curve", "credit_curve"):
        return len(payload.get("tenor_points", []))
    if kind == "fx_set":
        return len(payload.get("pairs", {}))
    if kind == "stress_preset":
        return len(payload.get("shocks", {}))
    return 0


def ingest_dataset(
    tenant_id: str,
    kind: str,
    name: str,
    payload: Any,
    created_by: str = "demo@riskcanvas.io",
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    Canonicalize, validate, and register a dataset.
    Returns (dataset, errors). If errors non-empty, dataset is not stored.
    """
    errors = _validate_payload(kind, payload)
    if errors:
        return ({}, errors)

    canonical = _canonical(payload)
    sha = hashlib.sha256(canonical.encode()).hexdigest()
    schema_version = SCHEMA_VERSIONS.get(kind, "1.0")

    dataset_id_src = {"tenant_id": tenant_id, "kind": kind, "sha256": sha, "name": name}
    dataset_id = _sha(dataset_id_src)[:32]

    storage_key = f"datasets/{tenant_id}/{kind}/{dataset_id}.json"

    manifest = {
        "dataset_id": dataset_id,
        "kind": kind,
        "name": name,
        "schema_version": schema_version,
        "sha256": sha,
        "storage_key": storage_key,
        "tenant_id": tenant_id,
        "created_by": created_by,
        "row_count": _count_rows(kind, payload),
    }

    dataset: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "tenant_id": tenant_id,
        "kind": kind,
        "name": name,
        "schema_version": schema_version,
        "sha256": sha,
        "storage_key": storage_key,
        "manifest": manifest,
        "created_by": created_by,
        "created_at": ASOF,
        "row_count": _count_rows(kind, payload),
        "verified": True,
    }

    DATASET_STORE[dataset_id] = dataset
    return (dataset, [])


def list_datasets(
    tenant_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    results = list(DATASET_STORE.values())
    if tenant_id:
        results = [d for d in results if d["tenant_id"] == tenant_id]
    if kind:
        results = [d for d in results if d["kind"] == kind]
    results.sort(key=lambda d: d["dataset_id"])
    return results[:limit]


def get_dataset(dataset_id: str) -> Dict[str, Any]:
    d = DATASET_STORE.get(dataset_id)
    if not d:
        raise ValueError(f"Dataset not found: {dataset_id}")
    return d


# ── Seed DEMO datasets ────────────────────────────────────────────────────────

def _seed() -> None:
    from tenancy_v2 import DEFAULT_TENANT_ID

    _portfolios = [
        ("Growth Portfolio", {
            "positions": [
                {"ticker": "MSFT", "quantity": 1000, "cost_basis": 290.50},
                {"ticker": "AAPL", "quantity": 2500, "cost_basis": 172.30},
                {"ticker": "NVDA", "quantity": 500, "cost_basis": 480.00},
                {"ticker": "AMZN", "quantity": 750, "cost_basis": 178.00},
            ]
        }),
        ("Fixed Income Core", {
            "positions": [
                {"ticker": "US10Y", "quantity": 5000000, "cost_basis": 98.50},
                {"ticker": "US2Y",  "quantity": 2000000, "cost_basis": 99.10},
                {"ticker": "IG_CORP_ETF", "quantity": 10000, "cost_basis": 112.40},
            ]
        }),
    ]
    for name, payload in _portfolios:
        ingest_dataset(DEFAULT_TENANT_ID, "portfolio", name, payload, "seed@riskcanvas.io")

    ingest_dataset(DEFAULT_TENANT_ID, "rates_curve", "USD Swap Curve 2026-02-19", {
        "curve_date": "2026-02-19",
        "currency": "USD",
        "tenor_points": [
            {"tenor": "1M", "rate": 0.0520}, {"tenor": "3M", "rate": 0.0518},
            {"tenor": "6M", "rate": 0.0510}, {"tenor": "1Y", "rate": 0.0498},
            {"tenor": "2Y", "rate": 0.0480}, {"tenor": "5Y", "rate": 0.0462},
            {"tenor": "10Y", "rate": 0.0455}, {"tenor": "30Y", "rate": 0.0450},
        ]
    }, "seed@riskcanvas.io")

    ingest_dataset(DEFAULT_TENANT_ID, "stress_preset", "2026 Macro Shock Base", {
        "name": "2026 Macro Shock Base",
        "description": "Rate +100bp, equity -15%, credit +75bp",
        "shocks": {
            "rates": 0.01,
            "equity": -0.15,
            "credit": 0.0075,
            "fx_usd_eur": -0.03,
        }
    }, "seed@riskcanvas.io")

    ingest_dataset(DEFAULT_TENANT_ID, "fx_set", "2026-02-19 FX Snapshot", {
        "base_currency": "USD",
        "as_of": "2026-02-19",
        "pairs": {
            "USD/EUR": 0.9201,
            "USD/GBP": 0.7916,
            "USD/JPY": 148.72,
            "USD/CHF": 0.8845,
            "USD/CAD": 1.3612,
        }
    }, "seed@riskcanvas.io")

    ingest_dataset(DEFAULT_TENANT_ID, "credit_curve", "MSFT Credit Curve 2026-02-19", {
        "issuer": "MSFT",
        "currency": "USD",
        "rating": "AAA",
        "as_of": "2026-02-19",
        "tenor_points": [
            {"tenor": "1Y", "spread": 0.0012},
            {"tenor": "3Y", "spread": 0.0021},
            {"tenor": "5Y", "spread": 0.0030},
            {"tenor": "10Y", "spread": 0.0045},
        ]
    }, "seed@riskcanvas.io")


_seed()


# ── FastAPI router ────────────────────────────────────────────────────────────

router = APIRouter(prefix="/datasets", tags=["datasets"])


class IngestRequest(BaseModel):
    kind: str
    name: str
    payload: Any
    tenant_id: Optional[str] = None
    created_by: str = "demo@riskcanvas.io"


@router.get("")
async def api_list_datasets(
    tenant_id: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 50,
    x_demo_tenant: Optional[str] = Header(None),
):
    tid = tenant_id or x_demo_tenant
    return {
        "datasets": list_datasets(tenant_id=tid, kind=kind, limit=limit),
        "count": len(list_datasets(tenant_id=tid, kind=kind, limit=limit)),
    }


@router.get("/{dataset_id}")
async def api_get_dataset(dataset_id: str):
    try:
        return {"dataset": get_dataset(dataset_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/ingest")
async def api_ingest_dataset(req: IngestRequest, x_demo_tenant: Optional[str] = Header(None)):
    if req.kind not in SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown kind '{req.kind}'. Valid kinds: {list(SCHEMA_VERSIONS.keys())}",
        )
    tid = req.tenant_id or x_demo_tenant or "default"
    dataset, errors = ingest_dataset(
        tenant_id=tid,
        kind=req.kind,
        name=req.name,
        payload=req.payload,
        created_by=req.created_by,
    )
    if errors:
        return {"valid": False, "errors": errors, "dataset": None}
    return {"valid": True, "errors": [], "dataset": dataset}


@router.post("/validate")
async def api_validate_dataset(req: IngestRequest):
    if req.kind not in SCHEMA_VERSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown kind '{req.kind}'. Valid kinds: {list(SCHEMA_VERSIONS.keys())}",
        )
    errors = _validate_payload(req.kind, req.payload)
    return {"valid": len(errors) == 0, "errors": errors}
