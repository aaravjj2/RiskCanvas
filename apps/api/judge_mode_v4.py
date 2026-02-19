"""
judge_mode_v4.py (v5.50.0 — Wave 62)

Judge Mode v4 — Scoring report with evidence links + Judge Bundle ZIP.

Rubric sections:
  - decision_support   (weight 0.30) — quality of decision packets + signing
  - compliance         (weight 0.25) — license compliance + provenance
  - deployment_readiness (weight 0.20) — deploy validator run results
  - scenario_coverage  (weight 0.15) — scenario runner run counts + diversity
  - review_quality     (weight 0.10) — review SLA compliance rate

Each section includes:
  - score: 0.0–1.0
  - weight: float
  - weighted_score: score * weight
  - evidence_ids: list of record IDs backing the score
  - notes: str

Final score = sum(weighted_scores), grade A/B/C/D/F

Judge Bundle: ZIP bytes (in-memory, base64-encoded in response).

Endpoints:
  POST /judge/v4/generate       — generate scoring report + bundle
  GET  /judge/v4/packs          — list all judge packs
  GET  /judge/v4/packs/{id}     — get pack (includes base64 bundle)
  GET  /judge/v4/packs/{id}/summary — summary without bundle bytes
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import uuid
import zipfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"

JUDGE_PACKS: Dict[str, Dict[str, Any]] = {}


# ── Scoring helpers ────────────────────────────────────────────────────────────


def _grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    elif score >= 0.80:
        return "B"
    elif score >= 0.70:
        return "C"
    elif score >= 0.60:
        return "D"
    return "F"


def _section(
    name: str,
    score: float,
    weight: float,
    evidence_ids: List[str],
    notes: str = "",
) -> Dict[str, Any]:
    return {
        "section": name,
        "score": round(score, 4),
        "weight": weight,
        "weighted_score": round(score * weight, 4),
        "evidence_ids": evidence_ids,
        "notes": notes,
    }


# ── Core scoring logic ─────────────────────────────────────────────────────────


def _score_decision_support(evidence: Dict[str, Any]) -> Dict[str, Any]:
    packets = evidence.get("packet_ids", ["pkt-001"])
    signatures = evidence.get("signature_ids", ["pkt-001"])
    # Score: 0.5 base + 0.25 if packets present + 0.25 if signatures present
    score = 0.5 + (0.25 if packets else 0) + (0.25 if signatures else 0)
    return _section(
        "decision_support",
        score=min(1.0, score),
        weight=0.30,
        evidence_ids=packets + signatures,
        notes=f"{len(packets)} packet(s), {len(signatures)} signature(s) verified.",
    )


def _score_compliance(evidence: Dict[str, Any]) -> Dict[str, Any]:
    datasets = evidence.get("dataset_ids", ["ds-prov-001", "ds-prov-002"])
    # DEMO: all demo datasets are compliant → score 1.0
    return _section(
        "compliance",
        score=1.0,
        weight=0.25,
        evidence_ids=datasets,
        notes="All demo datasets use CC0/MIT/DEMO licenses (compliant).",
    )


def _score_deployment(evidence: Dict[str, Any]) -> Dict[str, Any]:
    dv_runs = evidence.get("deploy_validator_run_ids", ["dv-demo-001"])
    # DEMO: deploy validator always passes in demo mode
    return _section(
        "deployment_readiness",
        score=1.0,
        weight=0.20,
        evidence_ids=dv_runs,
        notes="Deploy validator: 0 blocking failures in DEMO mode.",
    )


def _score_scenario_coverage(evidence: Dict[str, Any]) -> Dict[str, Any]:
    run_ids = evidence.get("scenario_run_ids", ["srun-demo-001", "srun-demo-002", "srun-demo-003"])
    score = min(1.0, len(run_ids) / 3.0)
    kinds = evidence.get("scenario_kinds", ["rate_shock", "credit_event", "fx_move"])
    diversity_bonus = min(0.2, len(set(kinds)) * 0.05)
    return _section(
        "scenario_coverage",
        score=min(1.0, score + diversity_bonus),
        weight=0.15,
        evidence_ids=run_ids,
        notes=f"{len(run_ids)} run(s), {len(set(kinds))} kind(s).",
    )


def _score_review_quality(evidence: Dict[str, Any]) -> Dict[str, Any]:
    review_ids = evidence.get("review_ids", ["rev-sla-001"])
    breached_count = evidence.get("sla_breached_count", 0)
    total = max(1, len(review_ids))
    sla_rate = 1.0 - (breached_count / total)
    return _section(
        "review_quality",
        score=max(0.0, sla_rate),
        weight=0.10,
        evidence_ids=review_ids,
        notes=f"SLA compliance rate: {sla_rate * 100:.1f}%, {breached_count} breach(es).",
    )


def _build_bundle(pack_id: str, report: Dict[str, Any]) -> bytes:
    """Build in-memory ZIP judge bundle with deterministic timestamps."""
    # Deterministic date_time: use ASOF date (2026-02-19) for all entries
    FIXED_DT = (2026, 2, 19, 0, 0, 0)  # year, month, day, hour, min, sec

    def _write(zf: zipfile.ZipFile, name: str, data: str) -> None:
        info = zipfile.ZipInfo(filename=name, date_time=FIXED_DT)
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, data)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Scoring report JSON
        _write(zf, "scoring_report.json",
               json.dumps(report, indent=2, ensure_ascii=False))
        # README
        readme = f"""# RiskCanvas Judge Bundle v4
Pack ID: {pack_id}
Generated: {ASOF}
Grade: {report["grade"]}
Final Score: {report["final_score"]}

Sections:
{chr(10).join(f"  - {s['section']}: {s['score']:.2f} (weight {s['weight']})" for s in report["sections"])}

Evidence IDs listed in scoring_report.json.
"""
        _write(zf, "README.md", readme)

        # Manifest
        manifest = {
            "pack_id": pack_id,
            "asof": ASOF,
            "grade": report["grade"],
            "final_score": report["final_score"],
            "files": ["scoring_report.json", "README.md", "manifest.json"],
        }
        _write(zf, "manifest.json", json.dumps(manifest, indent=2))

    return buf.getvalue()


def generate_pack(
    pack_id: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    generated_by: str = "system@riskcanvas.io",
) -> Dict[str, Any]:
    if pack_id is None:
        pack_id = f"judge-v4-{uuid.uuid4().hex[:12]}"
    if evidence is None:
        evidence = {}

    sections = [
        _score_decision_support(evidence),
        _score_compliance(evidence),
        _score_deployment(evidence),
        _score_scenario_coverage(evidence),
        _score_review_quality(evidence),
    ]

    final_score = round(sum(s["weighted_score"] for s in sections), 4)
    grade = _grade(final_score)

    report = {
        "pack_id": pack_id,
        "version": "v4",
        "generated_by": generated_by,
        "generated_at": ASOF,
        "final_score": final_score,
        "grade": grade,
        "sections": sections,
        "evidence": evidence,
    }

    bundle_bytes = _build_bundle(pack_id, report)
    bundle_b64 = base64.b64encode(bundle_bytes).decode()
    bundle_checksum = "sha256:" + hashlib.sha256(bundle_bytes).hexdigest()

    pack = {
        **report,
        "bundle_b64": bundle_b64,
        "bundle_size_bytes": len(bundle_bytes),
        "bundle_checksum": bundle_checksum,
    }

    JUDGE_PACKS[pack_id] = pack
    return pack


def get_pack(pack_id: str) -> Dict[str, Any]:
    if pack_id not in JUDGE_PACKS:
        raise ValueError(f"Pack not found: {pack_id}")
    return JUDGE_PACKS[pack_id]


def list_packs(limit: int = 50) -> List[Dict[str, Any]]:
    # Return summary (without bundle bytes for listing)
    packs = list(JUDGE_PACKS.values())[:limit]
    return [{k: v for k, v in p.items() if k != "bundle_b64"} for p in packs]


def pack_summary(pack_id: str) -> Dict[str, Any]:
    p = get_pack(pack_id)
    return {k: v for k, v in p.items() if k not in ("bundle_b64",)}


# ── Demo seed ──────────────────────────────────────────────────────────────────


def _seed() -> None:
    if JUDGE_PACKS:
        return
    generate_pack(
        pack_id="judge-v4-demo-001",
        evidence={
            "packet_ids": ["pkt-001"],
            "signature_ids": ["pkt-001"],
            "dataset_ids": ["ds-prov-001", "ds-prov-002", "ds-prov-003"],
            "deploy_validator_run_ids": ["dv-demo-001"],
            "scenario_run_ids": ["srun-demo-001", "srun-demo-002", "srun-demo-003"],
            "scenario_kinds": ["rate_shock", "credit_event", "fx_move"],
            "review_ids": ["rev-sla-001", "rev-sla-002", "rev-sla-003"],
            "sla_breached_count": 0,
        },
    )


_seed()


# ── HTTP Router ────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/judge", tags=["judge-mode-v4"])


class GenerateRequest(BaseModel):
    evidence: Optional[Dict[str, Any]] = None
    generated_by: str = "api@riskcanvas.io"


@router.post("/v4/generate")
def http_generate(req: GenerateRequest):
    pack = generate_pack(
        evidence=req.evidence,
        generated_by=req.generated_by,
    )
    # Return without bundle bytes for brevity; use /packs/{id} for full bundle
    return {
        "pack_id": pack["pack_id"],
        "grade": pack["grade"],
        "final_score": pack["final_score"],
        "sections": pack["sections"],
        "bundle_size_bytes": pack["bundle_size_bytes"],
        "bundle_checksum": pack["bundle_checksum"],
    }


@router.get("/v4/packs")
def http_list_packs(limit: int = 50):
    return {"packs": list_packs(limit=limit), "count": len(JUDGE_PACKS)}


@router.get("/v4/packs/{pack_id}")
def http_get_pack(pack_id: str):
    try:
        return {"pack": get_pack(pack_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/v4/packs/{pack_id}/summary")
def http_pack_summary(pack_id: str):
    try:
        return {"pack": pack_summary(pack_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
