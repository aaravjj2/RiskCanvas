"""
DevOps Pro v1 (v3.9+)

Provides:
1) MR Review Bundle — structured review.md + review.json with risk findings
2) Pipeline Failure Analyzer — deterministic rule engine for log analysis
3) Artifact Pack builder — stable bundle with manifest hash
"""

import hashlib
import json
import os
import re
import zipfile
import io
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter
from pydantic import BaseModel

# ── DEMO timestamp ─────────────────────────────────────────────────────────────

def _demo_ts() -> str:
    return "2026-01-01T00:00:00+00:00" if os.getenv("DEMO_MODE", "false").lower() == "true" else datetime.utcnow().isoformat() + "+00:00"


# ── MR Review Bundle ───────────────────────────────────────────────────────────

_SECRET_PATTERNS_MR: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S+"), "SECRET_IN_DIFF", "blocker"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OPENAI_KEY_DETECTED", "blocker"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "GITHUB_PAT_DETECTED", "blocker"),
]

_WARNING_PATTERNS_MR: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\b(TODO|FIXME|HACK|XXX)\b"), "TODO_FIXME", "warning"),
    (re.compile(r"(?i)(console\.log|print\(|debugger;|pdb\.set_trace)"), "DEBUG_LOG", "warning"),
    (re.compile(r"except\s*:"), "BARE_EXCEPT", "warning"),
    (re.compile(r"import \*"), "WILDCARD_IMPORT", "warning"),
    (re.compile(r"eval\("), "EVAL_USAGE", "warning"),
]


def analyze_diff(diff_text: str) -> Dict[str, Any]:
    """
    Analyze a git diff for security and quality findings.
    Returns structured findings list + risk summary.
    """
    findings: List[Dict[str, Any]] = []
    lines = diff_text.split("\n")

    added_lines = [(i + 1, line) for i, line in enumerate(lines)
                   if line.startswith("+") and not line.startswith("+++")]

    for lineno, line in added_lines:
        for pat, code, severity in _SECRET_PATTERNS_MR:
            if pat.search(line):
                findings.append({
                    "line": lineno,
                    "code": code,
                    "severity": severity,
                    "message": f"{code.replace('_', ' ').title()} detected.",
                    "excerpt": line[:80].replace("+", "", 1).strip(),
                })

        for pat, code, severity in _WARNING_PATTERNS_MR:
            if pat.search(line):
                findings.append({
                    "line": lineno,
                    "code": code,
                    "severity": severity,
                    "message": f"{code.replace('_', ' ').title()} found.",
                    "excerpt": line[:80].replace("+", "", 1).strip(),
                })

    # Large diff check
    if len(added_lines) > 300:
        findings.append({
            "line": 0,
            "code": "LARGE_DIFF",
            "severity": "warning",
            "message": f"Large diff: {len(added_lines)} added lines (>300). Consider splitting.",
            "excerpt": "",
        })

    # Policy gate check — run policy engine
    diff_hash = hashlib.sha256(diff_text.encode()).hexdigest()[:16]

    blockers = [f for f in findings if f["severity"] == "blocker"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    decision = "block" if blockers else "allow"

    return {
        "diff_hash": diff_hash,
        "findings": findings,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "total_findings": len(findings),
        "decision": decision,
        "summary": f"{decision.upper()}: {len(blockers)} blocker(s), {len(warnings)} warning(s).",
        "added_lines_count": len(added_lines),
    }


def build_review_md(analysis: Dict[str, Any], diff_hash: str) -> str:
    """Generate deterministic review.md from analysis result."""
    from audit_v2 import get_chain_head
    try:
        chain_head = get_chain_head()
    except Exception:
        chain_head = "N/A"

    lines = [
        "# MR Review Bundle",
        "",
        f"**Decision:** `{analysis['decision'].upper()}`  ",
        f"**Diff hash:** `{diff_hash}`  ",
        f"**Audit chain head:** `{chain_head}`  ",
        f"**Timestamp:** {_demo_ts()}  ",
        f"**Findings:** {analysis['total_findings']} total "
        f"({analysis['blocker_count']} blocker(s), {analysis['warning_count']} warning(s))  ",
        "",
        "## Findings",
        "",
        "| Line | Code | Severity | Message |",
        "|------|------|----------|---------|",
    ]
    for f in sorted(analysis["findings"], key=lambda x: (x["severity"], x["line"])):
        sev_icon = "🔴" if f["severity"] == "blocker" else "🟡"
        lines.append(f"| {f['line']} | `{f['code']}` | {sev_icon} {f['severity']} | {f['message']} |")

    lines += [
        "",
        "## Policy Decision",
        "",
        f"Policy gate decision: **{analysis['decision'].upper()}**",
        "",
        "---",
        "_Generated by RiskCanvas DevOps Pro v1 (v3.9+)_",
        "",
    ]
    return "\n".join(lines)


def build_review_bundle(diff_text: str) -> Dict[str, Any]:
    """Build the complete MR review bundle."""
    analysis = analyze_diff(diff_text)
    diff_hash = analysis["diff_hash"]
    review_md = build_review_md(analysis, diff_hash)

    review_json = {
        "diff_hash": diff_hash,
        "ts": _demo_ts(),
        "decision": analysis["decision"],
        "summary": analysis["summary"],
        "findings": analysis["findings"],
    }

    bundle_hash = hashlib.sha256(
        json.dumps(review_json, sort_keys=True).encode()
    ).hexdigest()[:16]

    return {
        "bundle_hash": bundle_hash,
        "diff_hash": diff_hash,
        "decision": analysis["decision"],
        "summary": analysis["summary"],
        "total_findings": analysis["total_findings"],
        "blocker_count": analysis["blocker_count"],
        "warning_count": analysis["warning_count"],
        "review_md": review_md,
        "review_json": review_json,
        "ts": _demo_ts(),
    }


# ── Pipeline Failure Analyzer ──────────────────────────────────────────────────

_PIPELINE_RULES: List[Tuple[re.Pattern, str, str, str]] = [
    (re.compile(r"(?i)out of memory|OOM|MemoryError|cannot allocate"), "OOM", "fatal",
     "Reduce memory usage: lower batch size, add swap, or scale VM."),
    (re.compile(r"(?i)timeout|ETIMEDOUT|connection timed out"), "TIMEOUT", "error",
     "Check network connectivity, increase timeout thresholds, or retry."),
    (re.compile(r"(?i)permission denied|access denied|EACCES|EPERM"), "PERMISSION", "error",
     "Verify IAM roles, file system permissions, and service account grants."),
    (re.compile(r"(?i)import error|ModuleNotFoundError|cannot import"), "IMPORT_ERROR", "error",
     "Install missing dependencies: check requirements.txt and run pip install."),
    (re.compile(r"(?i)syntax error|SyntaxError|unexpected token"), "SYNTAX_ERROR", "fatal",
     "Fix the syntax error at the indicated line before re-running."),
    (re.compile(r"(?i)failed to connect|connection refused|ECONNREFUSED"), "CONNECTION_REFUSED", "error",
     "Verify service is running and port is correct. Check firewall rules."),
    (re.compile(r"(?i)assertion.*failed|assert.*error|AssertionError"), "ASSERTION_FAILED", "warning",
     "Review test assertions. Likely a logic error in the test or the code."),
    (re.compile(r"(?i)disk full|no space left|ENOSPC"), "DISK_FULL", "fatal",
     "Free disk space: clean artifacts, compress logs, or expand volume."),
    (re.compile(r"(?i)exit code [1-9]\d*"), "NON_ZERO_EXIT", "warning",
     "Check the last failing command; look for the specific error above."),
    (re.compile(r"(?i)rate limit|429|too many requests"), "RATE_LIMIT", "warning",
     "Back off and retry. Check API quotas and add exponential backoff."),
    (re.compile(r"(?i)test.*failed|FAILED|failure"), "TEST_FAILURE", "warning",
     "Review failing test output. Check logic and data dependencies."),
    (re.compile(r"(?i)build failed|build error|npm err"), "BUILD_FAILURE", "error",
     "Check build logs for the first error; fix dependencies and syntax."),
]


def analyze_pipeline_log(log_text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based analysis of pipeline log text.
    Returns categorized findings + remediation steps.
    """
    lines = log_text.split("\n")
    findings: List[Dict[str, Any]] = []
    seen_codes: set = set()

    for i, line in enumerate(lines):
        for pat, code, severity, remediation in _PIPELINE_RULES:
            if code in seen_codes:
                continue
            if pat.search(line):
                findings.append({
                    "line": i + 1,
                    "code": code,
                    "severity": severity,
                    "excerpt": line[:120].strip(),
                    "remediation": remediation,
                })
                seen_codes.add(code)

    # Sort by severity priority
    sev_order = {"fatal": 0, "error": 1, "warning": 2}
    findings.sort(key=lambda x: (sev_order.get(x["severity"], 9), x["line"]))

    categories = sorted(set(f["code"] for f in findings))
    log_hash = hashlib.sha256(log_text.encode()).hexdigest()[:16]

    return {
        "log_hash": log_hash,
        "total_findings": len(findings),
        "categories": categories,
        "findings": findings,
        "fatal_count": sum(1 for f in findings if f["severity"] == "fatal"),
        "error_count": sum(1 for f in findings if f["severity"] == "error"),
        "warning_count": sum(1 for f in findings if f["severity"] == "warning"),
        "ts": _demo_ts(),
    }


# ── Artifact Pack Builder ──────────────────────────────────────────────────────

def build_artifact_pack(files: Dict[str, str]) -> Dict[str, Any]:
    """
    Build a deterministic artifact pack (in-memory zip).
    `files` is {filename: content_str}, sorted for determinism.

    Returns:
    {
        manifest_hash: str,
        file_list: [str],
        pack_b64: str,  # base64-encoded zip bytes
        ts: str,
    }
    """
    sorted_files = sorted(files.items(), key=lambda x: x[0])

    # Build manifest
    manifest = {
        "ts": _demo_ts(),
        "files": [{"name": k, "size": len(v.encode())} for k, v in sorted_files],
    }
    manifest_str = json.dumps(manifest, sort_keys=True, indent=2)
    manifest_hash = hashlib.sha256(manifest_str.encode()).hexdigest()[:32]
    manifest["manifest_hash"] = manifest_hash

    # Build zip in memory with stable ordering
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Always write manifest first
        zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True, indent=2))
        for name, content in sorted_files:
            zf.writestr(name, content)

    pack_bytes = buf.getvalue()
    pack_b64 = base64.b64encode(pack_bytes).decode()

    return {
        "manifest_hash": manifest_hash,
        "file_list": [k for k, _ in sorted_files],
        "file_count": len(sorted_files) + 1,  # +1 for manifest
        "pack_b64": pack_b64,
        "pack_size_bytes": len(pack_bytes),
        "ts": _demo_ts(),
    }


def build_default_devops_pack(review_bundle: Optional[Dict] = None, pipeline_result: Optional[Dict] = None) -> Dict[str, Any]:
    """Build artifact pack from review bundle and/or pipeline analysis."""
    files: Dict[str, str] = {}

    if review_bundle:
        files["review.md"] = review_bundle.get("review_md", "")
        files["review.json"] = json.dumps(review_bundle.get("review_json", {}), sort_keys=True, indent=2)

    if pipeline_result:
        files["pipeline_analysis.json"] = json.dumps(pipeline_result, sort_keys=True, indent=2)

    if not files:
        files["README.md"] = "# Empty pack\nNo content provided."

    return build_artifact_pack(files)


# ── FastAPI Router ─────────────────────────────────────────────────────────────

devops_pro_router = APIRouter(prefix="/devops", tags=["devops_pro"])


class MRReviewRequest(BaseModel):
    diff: str
    base_ref: str = "main"
    head_ref: str = "feature"


class PipelineAnalyzeRequest(BaseModel):
    log: str


class ArtifactsBuildRequest(BaseModel):
    review_bundle_hash: Optional[str] = None
    include_review: bool = False
    include_pipeline: bool = False
    # Inline content (DEMO)
    review_md: Optional[str] = None
    pipeline_json: Optional[str] = None


@devops_pro_router.post("/mr/review-bundle")
def api_mr_review_bundle(req: MRReviewRequest):
    return build_review_bundle(req.diff)


@devops_pro_router.post("/pipeline/analyze")
def api_pipeline_analyze(req: PipelineAnalyzeRequest):
    return analyze_pipeline_log(req.log)


@devops_pro_router.post("/artifacts/build")
def api_artifacts_build(req: ArtifactsBuildRequest):
    files: Dict[str, str] = {}
    if req.review_md:
        files["review.md"] = req.review_md
    if req.pipeline_json:
        files["pipeline_analysis.json"] = req.pipeline_json
    if not files:
        files["README.md"] = "# RiskCanvas DevOps Pro Artifact Pack\n\nGenerated by v3.9+\n"
    return build_artifact_pack(files)
