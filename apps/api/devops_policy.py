"""
DevOps Policy Gate for RiskCanvas v3.1+.

Provides agentic policy evaluation for MR/diff submissions:
- Input: diff text + optional risk metadata
- Output: allow/block + reasons + remediation checklist (deterministic)
- Export: MR comment markdown, reliability report markdown, policy JSON

All evaluation is offline and deterministic in DEMO mode.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

# AuditV2 integration (v3.3+) — imported lazily to avoid circular deps
def _emit_audit_safe(run_id: str, decision: str) -> None:
    try:
        from audit_v2 import emit_audit_v2
        from provenance import record_provenance
        emit_audit_v2(
            actor="demo_user",
            action="policy.evaluate",
            resource_type="policy",
            resource_id=run_id,
            payload={"decision": decision},
        )
    except Exception:
        pass  # never break policy endpoint due to audit failure

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

policy_router = APIRouter(prefix="/devops/policy", tags=["devops-policy"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class PolicyGateRequest(BaseModel):
    diff_text: str
    risk_delta: Optional[float] = None     # % change in portfolio risk
    coverage_delta: Optional[float] = None # % change in test coverage
    metadata: Optional[Dict[str, Any]] = None


class PolicyReason(BaseModel):
    code: str
    severity: str    # "blocker" | "warning" | "info"
    message: str
    line: Optional[int] = None


class RemediationItem(BaseModel):
    action: str
    priority: str    # "high" | "medium" | "low"


class PolicyGateResponse(BaseModel):
    decision: str           # "allow" | "block"
    run_id: str
    score: int              # 0-100 (higher = riskier)
    reasons: List[PolicyReason]
    remediation: List[RemediationItem]
    summary: str
    timestamp: str


class PolicyExportResponse(BaseModel):
    mr_comment_markdown: str
    reliability_report_markdown: str
    policy_decision_json: str


# ── Policy evaluation logic ────────────────────────────────────────────────────

_BLOCKER_PATTERNS = [
    (r"console\.(log|warn|error|debug)", "debug_logging",      "Debug logging detected — remove before merge"),
    (r"TODO|FIXME|HACK|XXX",             "todo_comments",      "TODO/FIXME/HACK comment in new code"),
    (r"password\s*=\s*['\"][^'\"]{4,}", "hardcoded_secret",   "Possible hardcoded password/secret"),
    (r"api_key\s*=\s*['\"][^'\"]{4,}",  "hardcoded_api_key",  "Possible hardcoded API key"),
    (r"\.{200,}",                         "long_line",          "Line exceeds 200 characters"),
]

_WARNING_PATTERNS = [
    (r"# type: ignore",               "type_ignore",       "Type ignore comment suppresses type checking"),
    (r"except\s*:",                    "bare_except",       "Bare except clause — specify exception type"),
    (r"import \*",                     "wildcard_import",   "Wildcard import reduces clarity"),
    (r"\bprint\b\(",                   "print_statement",   "print() statement in production code"),
]


def _stable_id(text: str) -> str:
    return "policy-" + hashlib.sha256(text.encode()).hexdigest()[:12]


def _evaluate_diff(diff_text: str, risk_delta: Optional[float], coverage_delta: Optional[float]) -> PolicyGateResponse:
    """Deterministic policy rule engine."""
    reasons: List[PolicyReason] = []
    score = 0

    added_lines = [(i + 1, line) for i, line in enumerate(diff_text.splitlines())
                   if line.startswith("+") and not line.startswith("+++")]

    for lineno, line in added_lines:
        for pattern, code, message in _BLOCKER_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                reasons.append(PolicyReason(
                    code=code, severity="blocker",
                    message=message, line=lineno
                ))
                score += 25

        for pattern, code, message in _WARNING_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                reasons.append(PolicyReason(
                    code=code, severity="warning",
                    message=message, line=lineno
                ))
                score += 10

    # Risk delta blocker
    if risk_delta is not None and risk_delta > 0.2:
        reasons.append(PolicyReason(
            code="risk_increase",
            severity="blocker",
            message=f"Portfolio risk increased by {risk_delta*100:.1f}% — exceeds 20% threshold",
        ))
        score += 30

    # Coverage delta warning
    if coverage_delta is not None and coverage_delta < -0.05:
        reasons.append(PolicyReason(
            code="coverage_decrease",
            severity="warning",
            message=f"Test coverage decreased by {abs(coverage_delta)*100:.1f}%",
        ))
        score += 15

    score = min(score, 100)
    blockers = [r for r in reasons if r.severity == "blocker"]
    decision = "block" if blockers else "allow"

    remediation: List[RemediationItem] = []
    for r in reasons:
        if r.severity == "blocker":
            remediation.append(RemediationItem(action=f"Fix: {r.message}", priority="high"))
        elif r.severity == "warning":
            remediation.append(RemediationItem(action=f"Consider: {r.message}", priority="medium"))

    if not remediation:
        remediation.append(RemediationItem(action="No action required — all policy checks passed", priority="low"))

    blocker_count = len(blockers)
    warning_count = len([r for r in reasons if r.severity == "warning"])
    summary = (
        f"Policy {'BLOCKED' if decision == 'block' else 'PASSED'}: "
        f"{blocker_count} blocker(s), {warning_count} warning(s). Score: {score}/100"
    )

    return PolicyGateResponse(
        decision=decision,
        run_id=_stable_id(diff_text),
        score=score,
        reasons=reasons,
        remediation=remediation,
        summary=summary,
        timestamp="2026-01-01T00:00:00+00:00" if DEMO_MODE
                  else datetime.now(timezone.utc).isoformat(),
    )


def _build_mr_comment(result: PolicyGateResponse) -> str:
    """Build deterministic MR comment markdown."""
    badge = "🔴 BLOCKED" if result.decision == "block" else "✅ ALLOWED"
    lines = [
        f"## RiskCanvas Policy Gate — {badge}",
        "",
        f"**Decision:** `{result.decision.upper()}`  **Score:** {result.score}/100",
        "",
        "### Findings",
    ]
    if result.reasons:
        for r in result.reasons:
            icon = "🚫" if r.severity == "blocker" else ("⚠️" if r.severity == "warning" else "ℹ️")
            line_ref = f" (line {r.line})" if r.line else ""
            lines.append(f"- {icon} `[{r.code}]`{line_ref}: {r.message}")
    else:
        lines.append("- No issues found.")

    lines += ["", "### Remediation Checklist", ""]
    for item in result.remediation:
        lines.append(f"- [ ] **{item.priority.upper()}**: {item.action}")

    lines += ["", f"*Generated by RiskCanvas policy gate — run_id: `{result.run_id}`*"]
    return "\n".join(lines)


def _build_reliability_report(result: PolicyGateResponse) -> str:
    """Build deterministic reliability report markdown."""
    lines = [
        "# RiskCanvas Reliability Report",
        "",
        f"**Decision:** {result.decision.upper()}",
        f"**Score:** {result.score}/100",
        f"**Summary:** {result.summary}",
        "",
        "## Issue Breakdown",
        "",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| Blocker  | {len([r for r in result.reasons if r.severity == 'blocker'])} |",
        f"| Warning  | {len([r for r in result.reasons if r.severity == 'warning'])} |",
        f"| Info     | {len([r for r in result.reasons if r.severity == 'info'])} |",
        "",
        "## Remediation",
        "",
    ]
    for item in result.remediation:
        lines.append(f"- **[{item.priority}]** {item.action}")
    lines += ["", f"*run_id: {result.run_id}*"]
    return "\n".join(lines)


# ── Endpoints ──────────────────────────────────────────────────────────────────

@policy_router.post("/evaluate", response_model=PolicyGateResponse)
async def evaluate_policy_gate(request: PolicyGateRequest):
    """
    Run policy gate evaluation on a diff/metadata.
    Fully offline and deterministic.
    """
    result = _evaluate_diff(request.diff_text, request.risk_delta, request.coverage_delta)
    _emit_audit_safe(result.run_id, result.decision)
    return result


@policy_router.post("/export", response_model=PolicyExportResponse)
async def export_policy_artifacts(request: PolicyGateRequest):
    """
    Evaluate diff and export MR comment + reliability report + policy JSON.
    All artifacts are deterministic.
    """
    result = _evaluate_diff(request.diff_text, request.risk_delta, request.coverage_delta)

    return PolicyExportResponse(
        mr_comment_markdown=_build_mr_comment(result),
        reliability_report_markdown=_build_reliability_report(result),
        policy_decision_json=json.dumps(result.model_dump(), indent=2, default=str),
    )


@policy_router.get("/rules", response_model=List[Dict[str, str]])
async def list_policy_rules():
    """List all active policy rules."""
    rules = []
    for pattern, code, message in _BLOCKER_PATTERNS:
        rules.append({"code": code, "severity": "blocker", "description": message})
    for pattern, code, message in _WARNING_PATTERNS:
        rules.append({"code": code, "severity": "warning", "description": message})
    return rules
