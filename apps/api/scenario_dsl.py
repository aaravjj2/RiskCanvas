"""
RiskCanvas v4.14.0 — Scenario DSL + Validator + Storage

Provides a typed-JSON Scenario DSL with:
- Shocks for spot/vol/rates/curve nodes
- Named parameters + "apply to symbols"
- Deterministic scenario_id: sha256(canonical_scenario)[:32]
- In-memory storage (DEMO + tests)
- Diff engine between two scenarios (v4.15.0)
- Pack export (v4.16.0)

No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
SCENARIO_DSL_VERSION = "v1.0"

# ─────────────────────────── Helpers ─────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _compact_hash(data: Any) -> str:
    return _sha256(data)[:16]


def _chain_head() -> str:
    return "scenarioc5d6e7f8a9"


def _make_scenario_id(canonical_scenario: Dict[str, Any]) -> str:
    """Deterministic scenario id: sha256(canonical)[:32]."""
    return _sha256(canonical_scenario)[:32]


# ─────────────────────────── DSL Pydantic Models ──────────────────────────────


class SpotShock(BaseModel):
    symbols: List[str] = Field(default_factory=list, description="Symbols to apply shock to; empty = all")
    shock_type: str = Field("relative", description="relative | absolute")
    shock_value: float = Field(..., description="Shock magnitude (e.g. -0.10 = -10%)")


class VolShock(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    shock_type: str = Field("relative", description="relative | absolute")
    shock_value: float


class RatesShock(BaseModel):
    curve_id: str = Field("USD_SOFR", description="Rates curve to shock")
    shock_type: str = Field("parallel", description="parallel | tilt | twist")
    shock_bps: float = Field(..., description="Shock in basis points")


class CurveNodeShock(BaseModel):
    curve_id: str
    tenor: str = Field(..., description="e.g. '2Y', '5Y'")
    shock_bps: float


class ScenarioDSL(BaseModel):
    """Top-level Scenario DSL object."""
    name: str = Field(..., description="Human-readable scenario name")
    description: str = Field("", description="Optional description")
    tags: List[str] = Field(default_factory=list)
    spot_shocks: List[SpotShock] = Field(default_factory=list)
    vol_shocks: List[VolShock] = Field(default_factory=list)
    rates_shocks: List[RatesShock] = Field(default_factory=list)
    curve_node_shocks: List[CurveNodeShock] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Named parameters for templating")

    class Config:
        extra = "forbid"


# ─────────────────────────── Validator ───────────────────────────────────────


VALID_SHOCK_TYPES = {"relative", "absolute"}
VALID_RATES_SHOCK_TYPES = {"parallel", "tilt", "twist"}


def validate_scenario_dsl(scenario: Dict[str, Any]) -> List[str]:
    """
    Validate a scenario DSL dict.
    Returns list of validation errors (empty = valid).
    Deterministic: same input → same errors.
    """
    errors: List[str] = []

    if not scenario.get("name", "").strip():
        errors.append("name: must be non-empty")

    for i, shock in enumerate(scenario.get("spot_shocks", [])):
        if shock.get("shock_type", "relative") not in VALID_SHOCK_TYPES:
            errors.append(f"spot_shocks[{i}].shock_type: must be one of {VALID_SHOCK_TYPES}")
        if "shock_value" not in shock:
            errors.append(f"spot_shocks[{i}].shock_value: required")

    for i, shock in enumerate(scenario.get("vol_shocks", [])):
        if shock.get("shock_type", "relative") not in VALID_SHOCK_TYPES:
            errors.append(f"vol_shocks[{i}].shock_type: must be one of {VALID_SHOCK_TYPES}")

    for i, shock in enumerate(scenario.get("rates_shocks", [])):
        if shock.get("shock_type", "parallel") not in VALID_RATES_SHOCK_TYPES:
            errors.append(f"rates_shocks[{i}].shock_type: must be one of {VALID_RATES_SHOCK_TYPES}")
        if "shock_bps" not in shock:
            errors.append(f"rates_shocks[{i}].shock_bps: required")

    return sorted(errors)  # stable ordering


# ─────────────────────────── Storage ─────────────────────────────────────────


_scenario_store: Dict[str, Dict[str, Any]] = {}


def _canonical_scenario(dsl_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return canonical form (sorted keys, arrays in stable order)."""
    canonical = {
        "name": dsl_dict.get("name", ""),
        "description": dsl_dict.get("description", ""),
        "tags": sorted(dsl_dict.get("tags", [])),
        "spot_shocks": sorted(
            dsl_dict.get("spot_shocks", []),
            key=lambda x: json.dumps(x, sort_keys=True),
        ),
        "vol_shocks": sorted(
            dsl_dict.get("vol_shocks", []),
            key=lambda x: json.dumps(x, sort_keys=True),
        ),
        "rates_shocks": sorted(
            dsl_dict.get("rates_shocks", []),
            key=lambda x: json.dumps(x, sort_keys=True),
        ),
        "curve_node_shocks": sorted(
            dsl_dict.get("curve_node_shocks", []),
            key=lambda x: json.dumps(x, sort_keys=True),
        ),
        "parameters": {k: dsl_dict["parameters"][k] for k in sorted(dsl_dict.get("parameters", {}).keys())},
    }
    return canonical


def store_scenario(dsl_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Store a validated scenario. Returns stored record with id + hashes."""
    canonical = _canonical_scenario(dsl_dict)
    scenario_id = _make_scenario_id(canonical)

    ih = _compact_hash({"op": "create", "canonical": canonical})
    oh = _compact_hash(canonical)

    record = {
        "scenario_id": scenario_id,
        "dsl_version": SCENARIO_DSL_VERSION,
        "created_at": "2026-02-18T00:00:00Z",  # Fixed for determinism
        "canonical": canonical,
        "input_hash": ih,
        "output_hash": oh,
        "audit_chain_head_hash": _chain_head(),
    }

    _scenario_store[scenario_id] = record
    return record


def list_scenarios() -> List[Dict[str, Any]]:
    """List all stored scenarios in stable id order."""
    return [
        {
            "scenario_id": r["scenario_id"],
            "name": r["canonical"]["name"],
            "description": r["canonical"]["description"],
            "tags": r["canonical"]["tags"],
            "output_hash": r["output_hash"],
        }
        for r in sorted(_scenario_store.values(), key=lambda x: x["scenario_id"])
    ]


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    return _scenario_store.get(scenario_id)


def reset_scenario_store() -> None:
    """Reset for testing."""
    _scenario_store.clear()


# ─────────────────────────── Diff Engine (v4.15.0) ───────────────────────────


def diff_scenarios(a_id: str, b_id: str) -> Dict[str, Any]:
    """
    Compute deterministic diff between two scenarios.
    Returns added/removed/changed fields.
    """
    a = _scenario_store.get(a_id)
    b = _scenario_store.get(b_id)
    if a is None:
        raise ValueError(f"Scenario not found: {a_id}")
    if b is None:
        raise ValueError(f"Scenario not found: {b_id}")

    ca = a["canonical"]
    cb = b["canonical"]

    changes: List[Dict[str, Any]] = []

    def _field_diff(field: str) -> None:
        va = ca.get(field)
        vb = cb.get(field)
        if va != vb:
            changes.append({"field": field, "from": va, "to": vb, "change_type": "modified"})

    for field in sorted(["name", "description", "tags", "parameters"]):
        _field_diff(field)

    # Shock diffs
    for shock_type in sorted(["spot_shocks", "vol_shocks", "rates_shocks", "curve_node_shocks"]):
        sa = sorted([json.dumps(s, sort_keys=True) for s in ca.get(shock_type, [])])
        sb = sorted([json.dumps(s, sort_keys=True) for s in cb.get(shock_type, [])])
        added = set(sb) - set(sa)
        removed = set(sa) - set(sb)
        if added or removed:
            changes.append({
                "field": shock_type,
                "added_count": len(added),
                "removed_count": len(removed),
                "change_type": "shock_diff",
            })

    changes.sort(key=lambda x: x["field"])

    ih = _compact_hash({"a_id": a_id, "b_id": b_id})
    oh = _compact_hash(changes)

    return {
        "a_id": a_id,
        "b_id": b_id,
        "a_name": a["canonical"]["name"],
        "b_name": b["canonical"]["name"],
        "change_count": len(changes),
        "changes": changes,
        "input_hash": ih,
        "output_hash": oh,
        "audit_chain_head_hash": _chain_head(),
    }


# ─────────────────────────── Pack Export (v4.16.0) ───────────────────────────


def build_scenario_pack(scenario_ids: List[str]) -> Dict[str, Any]:
    """
    Build a deterministic scenario pack from a list of scenario IDs.
    Stable ZIP ordering guaranteed via sorted keys.
    """
    scenarios = []
    missing = []
    for sid in sorted(scenario_ids):
        rec = _scenario_store.get(sid)
        if rec:
            scenarios.append(rec)
        else:
            missing.append(sid)

    if missing:
        raise ValueError(f"Scenarios not found: {missing}")

    manifest = {
        "pack_type": "scenario_pack",
        "scenario_ids": sorted(scenario_ids),
        "scenario_count": len(scenarios),
        "dsl_version": SCENARIO_DSL_VERSION,
        "scenarios": [
            {
                "scenario_id": s["scenario_id"],
                "name": s["canonical"]["name"],
                "output_hash": s["output_hash"],
            }
            for s in sorted(scenarios, key=lambda x: x["scenario_id"])
        ],
    }
    manifest["manifest_hash"] = _compact_hash(manifest)

    pack = {
        "manifest": manifest,
        "scenarios": scenarios,
        "pack_hash": _compact_hash({"manifest": manifest, "scenario_ids": sorted(scenario_ids)}),
        "audit_chain_head_hash": _chain_head(),
    }
    return pack


# ─────────────────────────── Request Models ──────────────────────────────────


class ScenarioCreateRequest(BaseModel):
    scenario: Dict[str, Any] = Field(..., description="Scenario DSL object")


class ScenarioDiffRequest(BaseModel):
    a_id: str
    b_id: str


class ScenarioPackRequest(BaseModel):
    scenario_ids: List[str] = Field(..., description="IDs to include in pack")


# ─────────────────────────── Router ──────────────────────────────────────────

scenario_router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@scenario_router.post("/validate")
async def validate_scenario(req: ScenarioCreateRequest) -> Dict[str, Any]:
    """Validate a scenario DSL object. Returns errors list."""
    errors = validate_scenario_dsl(req.scenario)
    ih = _compact_hash(req.scenario)
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "error_count": len(errors),
        "input_hash": ih,
        "audit_chain_head_hash": _chain_head(),
    }


@scenario_router.post("/create")
async def create_scenario(req: ScenarioCreateRequest) -> Dict[str, Any]:
    """Validate and store a scenario DSL object."""
    errors = validate_scenario_dsl(req.scenario)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    record = store_scenario(req.scenario)
    return record


@scenario_router.get("/list")
async def get_scenario_list() -> Dict[str, Any]:
    """List all stored scenarios."""
    scenarios = list_scenarios()
    oh = _compact_hash(scenarios)
    return {
        "scenarios": scenarios,
        "count": len(scenarios),
        "output_hash": oh,
        "audit_chain_head_hash": _chain_head(),
    }


@scenario_router.get("/{scenario_id}")
async def get_scenario_by_id(scenario_id: str) -> Dict[str, Any]:
    """Get a scenario by ID."""
    rec = get_scenario(scenario_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    return rec


@scenario_router.post("/diff")
async def diff_scenarios_endpoint(req: ScenarioDiffRequest) -> Dict[str, Any]:
    """Compute deterministic diff between two scenarios."""
    try:
        return diff_scenarios(req.a_id, req.b_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────── Scenario Exports Router ─────────────────────────

scenario_exports_router = APIRouter(prefix="/exports", tags=["scenario-exports"])


@scenario_exports_router.post("/scenario-pack")
async def export_scenario_pack(req: ScenarioPackRequest) -> Dict[str, Any]:
    """Export a scenario pack with stable ordering and manifest hash."""
    try:
        return build_scenario_pack(req.scenario_ids)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
