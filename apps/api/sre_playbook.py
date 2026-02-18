"""
SRE Playbook Generator (v4.0+)

Deterministic playbook.md + playbook.json generation.
Inputs: optional policy_gate_result + pipeline_analysis + platform_health
All facts cited by hash; no invented numbers.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

# ── Helpers ────────────────────────────────────────────────────────────────────

def _demo_ts() -> str:
    return "2026-01-01T00:00:00+00:00" if os.getenv("DEMO_MODE", "false").lower() == "true" else datetime.utcnow().isoformat() + "+00:00"


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


# ── Step generators ────────────────────────────────────────────────────────────

def _triage_steps(
    policy: Optional[Dict],
    pipeline: Optional[Dict],
    health: Optional[Dict],
) -> List[Dict[str, str]]:
    steps: List[Dict[str, str]] = []

    if policy and policy.get("decision") == "block":
        blockers = [r for r in policy.get("reasons", []) if r.get("severity") == "blocker"]
        for b in blockers:
            steps.append({
                "phase": "triage",
                "action": f"Policy blocker [{b.get('code', '?')}]: {b.get('message', '')}",
                "source_hash": _sha(policy),
                "priority": "P0",
            })

    if pipeline and pipeline.get("fatal_count", 0) > 0:
        for f in pipeline.get("findings", []):
            if f["severity"] == "fatal":
                steps.append({
                    "phase": "triage",
                    "action": f"Pipeline fatal [{f['code']}]: {f['excerpt'][:80]}",
                    "remediation": f["remediation"],
                    "source_hash": _sha(pipeline),
                    "priority": "P0",
                })

    if health and health.get("status") not in (None, "healthy", "ok"):
        steps.append({
            "phase": "triage",
            "action": f"Platform health degraded (status={health.get('status', 'unknown')}). "
                      f"Check services listed in platform health endpoint.",
            "source_hash": _sha(health),
            "priority": "P1",
        })

    if not steps:
        steps.append({
            "phase": "triage",
            "action": "No immediate blockers detected. Proceed to mitigate phase.",
            "source_hash": "none",
            "priority": "P2",
        })

    return steps


def _mitigate_steps(
    policy: Optional[Dict],
    pipeline: Optional[Dict],
    health: Optional[Dict],
) -> List[Dict[str, str]]:
    steps: List[Dict[str, str]] = []

    if pipeline:
        for f in pipeline.get("findings", []):
            if f["severity"] in ("error", "warning"):
                steps.append({
                    "phase": "mitigate",
                    "action": f"Resolve [{f['code']}]: {f['remediation']}",
                    "source_hash": _sha(pipeline),
                    "priority": "P1" if f["severity"] == "error" else "P2",
                })

    if policy and policy.get("decision") == "allow":
        steps.append({
            "phase": "mitigate",
            "action": "Policy gate approved. No tool budget changes needed.",
            "source_hash": _sha(policy),
            "priority": "P3",
        })

    if not steps:
        steps.append({
            "phase": "mitigate",
            "action": "No mitigation steps required.",
            "source_hash": "none",
            "priority": "P3",
        })

    return steps


def _followup_steps(
    policy: Optional[Dict],
    pipeline: Optional[Dict],
    health: Optional[Dict],
) -> List[Dict[str, str]]:
    steps = [
        {
            "phase": "follow_up",
            "action": "Re-run eval suite to verify fixes (POST /governance/evals/run-suite).",
            "source_hash": "eval_harness_v2",
            "priority": "P2",
        },
        {
            "phase": "follow_up",
            "action": "Verify audit chain integrity (GET /audit/v2/verify).",
            "source_hash": "audit_v2",
            "priority": "P3",
        },
        {
            "phase": "follow_up",
            "action": "Update runbook documentation and close incident ticket.",
            "source_hash": "none",
            "priority": "P3",
        },
    ]
    return steps


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_playbook(
    policy_gate_result: Optional[Dict] = None,
    pipeline_analysis: Optional[Dict] = None,
    platform_health: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate a deterministic SRE playbook.
    All numeric references come from inputs only (no invented values).
    """
    inputs_hash = _sha({
        "policy": policy_gate_result,
        "pipeline": pipeline_analysis,
        "health": platform_health,
    })

    triage = _triage_steps(policy_gate_result, pipeline_analysis, platform_health)
    mitigate = _mitigate_steps(policy_gate_result, pipeline_analysis, platform_health)
    followup = _followup_steps(policy_gate_result, pipeline_analysis, platform_health)

    all_steps = triage + mitigate + followup

    # Build playbook_json
    playbook_json: Dict[str, Any] = {
        "inputs_hash": inputs_hash,
        "ts": _demo_ts(),
        "steps": all_steps,
        "step_count": len(all_steps),
        "triage_count": len(triage),
        "mitigate_count": len(mitigate),
        "followup_count": len(followup),
        "p0_count": sum(1 for s in all_steps if s.get("priority") == "P0"),
        "p1_count": sum(1 for s in all_steps if s.get("priority") == "P1"),
    }

    # Stable playbook_hash
    canonical = json.dumps(playbook_json, sort_keys=True)
    playbook_json["playbook_hash"] = hashlib.sha256(canonical.encode()).hexdigest()[:32]

    # Build playbook.md
    playbook_md = _build_md(playbook_json, policy_gate_result, pipeline_analysis, platform_health)

    return {
        "playbook_hash": playbook_json["playbook_hash"],
        "inputs_hash": inputs_hash,
        "ts": _demo_ts(),
        "playbook_md": playbook_md,
        "playbook_json": playbook_json,
    }


def _build_md(
    pj: Dict[str, Any],
    policy: Optional[Dict],
    pipeline: Optional[Dict],
    health: Optional[Dict],
) -> str:
    lines = [
        "# SRE Playbook",
        "",
        f"**Playbook Hash:** `{pj['playbook_hash']}`  ",
        f"**Inputs Hash:** `{pj['inputs_hash']}`  ",
        f"**Generated:** {pj['ts']}  ",
        f"**Steps:** {pj['step_count']} total "
        f"(P0: {pj['p0_count']}, P1: {pj['p1_count']})  ",
        "",
    ]

    # Add context summary
    if policy:
        lines += [
            "## Context: Policy Gate",
            "",
            f"- Decision: **{policy.get('decision', 'N/A').upper()}**",
            f"- Mode: `{policy.get('mode', 'N/A')}`",
            f"- Hash: `{_sha(policy)}`",
            "",
        ]
    if pipeline:
        lines += [
            "## Context: Pipeline Analysis",
            "",
            f"- Fatal: {pipeline.get('fatal_count', 0)}, Error: {pipeline.get('error_count', 0)}, Warning: {pipeline.get('warning_count', 0)}",
            f"- Hash: `{_sha(pipeline)}`",
            "",
        ]

    for phase in ("triage", "mitigate", "follow_up"):
        phase_steps = [s for s in pj["steps"] if s["phase"] == phase]
        if phase_steps:
            lines += [f"## {phase.replace('_', ' ').title()}", ""]
            for i, s in enumerate(phase_steps, 1):
                lines.append(f"**{i}. [{s['priority']}]** {s['action']}")
                if s.get("remediation"):
                    lines.append(f"   > Remediation: {s['remediation']}")
                lines.append(f"   > Source hash: `{s['source_hash']}`")
                lines.append("")

    lines += ["---", "_Generated by RiskCanvas SRE Agent v4.0+_", ""]
    return "\n".join(lines)


# ── FastAPI Router ─────────────────────────────────────────────────────────────

sre_router = APIRouter(prefix="/sre", tags=["sre"])


class PlaybookRequest(BaseModel):
    policy_gate_result: Optional[Dict[str, Any]] = None
    pipeline_analysis: Optional[Dict[str, Any]] = None
    platform_health: Optional[Dict[str, Any]] = None


@sre_router.post("/playbook/generate")
def api_generate_playbook(req: PlaybookRequest):
    return generate_playbook(
        policy_gate_result=req.policy_gate_result,
        pipeline_analysis=req.pipeline_analysis,
        platform_health=req.platform_health,
    )
