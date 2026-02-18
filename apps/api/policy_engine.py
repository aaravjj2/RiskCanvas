"""
PolicyEngine v2 (v3.7+)

Enforces:
- Allowed tool list by mode (DEMO / LOCAL / PROD)
- Max tool calls per run
- Max response bytes
- Disallowed patterns in prompts/outputs
- "No hallucinated numbers" narrative validator
- Deterministic redaction of secret-like tokens
"""

import hashlib
import json
import math
import re
import os
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter

# ── Mode constants ────────────────────────────────────────────────────────────

ALLOWED_TOOLS_BY_MODE: Dict[str, List[str]] = {
    "DEMO": [
        "portfolio_analysis",
        "var_calculation",
        "price_option",
        "hedge_suggest",
        "rates_bootstrap",
        "stress_apply",
        "sre_playbook",
        "devops_review",
    ],
    "LOCAL": [
        "portfolio_analysis",
        "var_calculation",
        "price_option",
        "hedge_suggest",
        "rates_bootstrap",
        "stress_apply",
        "sre_playbook",
        "devops_review",
        "gitlab_mr_bot",
        "monitor_reporter",
    ],
    "PROD": [
        "portfolio_analysis",
        "var_calculation",
        "price_option",
        "hedge_suggest",
        "rates_bootstrap",
        "stress_apply",
        "sre_playbook",
        "devops_review",
        "gitlab_mr_bot",
        "monitor_reporter",
        "azure_devops",
        "foundry_analysis",
    ],
}

MAX_TOOL_CALLS_BY_MODE: Dict[str, int] = {
    "DEMO": 20,
    "LOCAL": 50,
    "PROD": 100,
}

MAX_RESPONSE_BYTES_BY_MODE: Dict[str, int] = {
    "DEMO": 524288,    # 512 KB
    "LOCAL": 1048576,  # 1 MB
    "PROD": 4194304,   # 4 MB
}

# ── Secret-like pattern detection ─────────────────────────────────────────────

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*\S+"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),  # base64-ish blobs ≥40 chars
    re.compile(r"sk-[A-Za-z0-9]{32,}"),         # OpenAI-style keys
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),         # GitHub PATs
    re.compile(r"\b[0-9a-fA-F]{64}\b"),          # 64-char hex (not audit hashes but catch misc)
]

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),       # SSN
    re.compile(r"\b[A-Z]{2}\d{6}[A-Z]\b"),       # Passport-like
]

# Audit hashes (64-char hex) are LEGITIMATE — whitelist prefix
_AUDIT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_audit_hash(token: str) -> bool:
    return bool(_AUDIT_HASH_RE.match(token))


def redact_secrets(text: str) -> Tuple[str, List[str]]:
    """
    Replace known secret-like tokens in `text` with [REDACTED].
    Returns (redacted_text, list_of_redaction_reasons).
    Deterministic: same input -> same output.
    """
    redacted = text
    reasons: List[str] = []

    for pat in _SECRET_PATTERNS:
        for m in pat.finditer(text):
            token = m.group(0)
            # Skip if it's a legitimate audit hash (64-char hex from our system)
            if _is_audit_hash(token):
                continue
            redacted = redacted.replace(token, "[REDACTED]")
            reasons.append(f"secret_pattern: {pat.pattern[:40]}…")

    for pat in _PII_PATTERNS:
        for m in pat.finditer(text):
            token = m.group(0)
            redacted = redacted.replace(token, "[REDACTED]")
            reasons.append(f"pii_pattern: {pat.pattern[:40]}…")

    return redacted, list(set(reasons))


# ── Disallowed output patterns ────────────────────────────────────────────────

_DISALLOWED_OUTPUT_PATTERNS = [
    (re.compile(r"(?i)hallucin"), "hallucination_marker"),
    (re.compile(r"(?i)as an ai"), "ai_self_reference"),
    (re.compile(r"(?i)i cannot guarantee"), "uncertainty_disclaimer"),
]


def check_disallowed_patterns(text: str) -> List[str]:
    """Return list of disallowed pattern names found in `text`."""
    found = []
    for pat, name in _DISALLOWED_OUTPUT_PATTERNS:
        if pat.search(text):
            found.append(name)
    return found


# ── Numeric extraction (for narrative validation) ─────────────────────────────

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def _extract_numbers(text: str) -> List[float]:
    """Extract all numeric literals from a string."""
    results = []
    for m in _NUMBER_RE.finditer(text):
        try:
            results.append(float(m.group(0)))
        except ValueError:
            pass
    return results


def _numbers_from_obj(obj: Any, depth: int = 0) -> List[float]:
    """Recursively collect all numeric values from a JSON-like object."""
    if depth > 12:
        return []
    nums: List[float] = []
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        nums.append(float(obj))
    elif isinstance(obj, str):
        nums.extend(_extract_numbers(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            nums.extend(_numbers_from_obj(v, depth + 1))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            nums.extend(_numbers_from_obj(item, depth + 1))
    return nums


def validate_narrative(
    narrative: str,
    computed_results: Dict[str, Any],
    tolerance: float = 0.01,
) -> Dict[str, Any]:
    """
    Validate that every number in `narrative` can be found in `computed_results`
    within `tolerance` (relative tolerance, or absolute if computed value is 0).

    Returns:
    {
        "valid": bool,
        "unknown_numbers": [float, ...],
        "narrativeNumbers": [float, ...],
        "computedNumbers": [float, ...],
        "errors": [str, ...],
        "remediation": str | None,
    }
    """
    narrative_nums = _extract_numbers(narrative)
    computed_nums = _numbers_from_obj(computed_results)

    # Build a "close enough" check
    unknown = []
    for n in narrative_nums:
        # Skip small integers (0-99) that commonly appear as counts/percentages
        if abs(n) <= 99 and n == int(n):
            continue
        # Check if n is within tolerance of any computed number
        found = False
        for c in computed_nums:
            if c == 0 and n == 0:
                found = True
                break
            denom = abs(c) if c != 0 else 1.0
            if abs(n - c) / denom <= tolerance:
                found = True
                break
        if not found:
            unknown.append(n)

    valid = len(unknown) == 0
    errors = [f"Number {u} in narrative not found in computed results (tol={tolerance})" for u in unknown]
    remediation = (
        "Remove or correct number(s) not derived from computed results: "
        + ", ".join(str(u) for u in unknown)
    ) if not valid else None

    return {
        "valid": valid,
        "unknown_numbers": sorted(set(unknown)),
        "narrative_numbers": narrative_nums,
        "computed_numbers": sorted(set(computed_nums)),
        "errors": errors,
        "remediation": remediation,
    }


# ── Policy evaluation ─────────────────────────────────────────────────────────

def get_policy_mode() -> str:
    """Resolve policy mode from environment."""
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        return "DEMO"
    if os.getenv("PROD_MODE", "false").lower() == "true":
        return "PROD"
    return "LOCAL"


def evaluate_policy(
    run_config: Dict[str, Any],
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate a run config against the policy for the given mode.

    run_config keys:
      - tools: List[str] — tools requested
      - tool_calls_requested: int
      - response_bytes: int (optional)
      - prompt: str (optional)
      - output: str (optional)

    Returns allow/block + reasons + policy_hash.
    """
    if mode is None:
        mode = get_policy_mode()
    mode = mode.upper()
    if mode not in ALLOWED_TOOLS_BY_MODE:
        mode = "DEMO"

    allowed_tools = ALLOWED_TOOLS_BY_MODE[mode]
    max_calls = MAX_TOOL_CALLS_BY_MODE[mode]
    max_bytes = MAX_RESPONSE_BYTES_BY_MODE[mode]

    reasons: List[Dict[str, str]] = []
    blocked = False

    # Check tool allowlist
    requested_tools = run_config.get("tools", [])
    for tool in requested_tools:
        if tool not in allowed_tools:
            reasons.append({
                "code": "TOOL_NOT_ALLOWED",
                "severity": "blocker",
                "message": f"Tool '{tool}' is not in allowed list for mode {mode}.",
            })
            blocked = True

    # Check tool call budget
    calls_requested = run_config.get("tool_calls_requested", 0)
    if calls_requested > max_calls:
        reasons.append({
            "code": "TOOL_BUDGET_EXCEEDED",
            "severity": "blocker",
            "message": f"Requested {calls_requested} tool calls exceeds max {max_calls} for mode {mode}.",
        })
        blocked = True

    # Check response size
    resp_bytes = run_config.get("response_bytes", 0)
    if resp_bytes > max_bytes:
        reasons.append({
            "code": "RESPONSE_TOO_LARGE",
            "severity": "blocker",
            "message": f"Response {resp_bytes} bytes exceeds max {max_bytes} for mode {mode}.",
        })
        blocked = True

    # Check prompt for secrets
    prompt = run_config.get("prompt", "")
    if prompt:
        _, secret_reasons = redact_secrets(prompt)
        if secret_reasons:
            reasons.append({
                "code": "SECRET_IN_PROMPT",
                "severity": "blocker",
                "message": f"Secret-like pattern detected in prompt ({len(secret_reasons)} match(es)).",
            })
            blocked = True

    # Check output for disallowed patterns
    output = run_config.get("output", "")
    if output:
        disallowed = check_disallowed_patterns(output)
        for d in disallowed:
            reasons.append({
                "code": f"DISALLOWED_OUTPUT_{d.upper()}",
                "severity": "warning",
                "message": f"Disallowed output pattern '{d}' detected.",
            })

    decision = "block" if blocked else "allow"

    # Stable policy_hash over (mode, sorted_tools, max_calls) for determinism
    policy_canonical = json.dumps({
        "mode": mode,
        "allowed_tools": sorted(allowed_tools),
        "max_tool_calls": max_calls,
        "max_response_bytes": max_bytes,
    }, sort_keys=True)
    policy_hash = hashlib.sha256(policy_canonical.encode()).hexdigest()[:16]

    return {
        "decision": decision,
        "mode": mode,
        "reasons": reasons,
        "policy_hash": policy_hash,
        "allowed_tools": allowed_tools,
        "max_tool_calls": max_calls,
        "max_response_bytes": max_bytes,
    }


def apply_policy(
    run_config: Dict[str, Any],
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply policy to a run config: redact secrets, enforce tool list, clip budget.
    Returns sanitized run_config + applied_changes.
    """
    result = evaluate_policy(run_config, mode)
    sanitized = dict(run_config)
    applied: List[str] = []

    # Redact prompt
    prompt = sanitized.get("prompt", "")
    if prompt:
        redacted_prompt, reasons = redact_secrets(prompt)
        if reasons:
            sanitized["prompt"] = redacted_prompt
            applied.append(f"redacted_prompt ({len(reasons)} pattern(s))")

    # Clip tool calls
    max_calls = result["max_tool_calls"]
    if sanitized.get("tool_calls_requested", 0) > max_calls:
        sanitized["tool_calls_requested"] = max_calls
        applied.append(f"clipped_tool_calls_to_{max_calls}")

    # Remove disallowed tools
    allowed = set(result["allowed_tools"])
    tools = sanitized.get("tools", [])
    kept = [t for t in tools if t in allowed]
    if len(kept) != len(tools):
        removed = [t for t in tools if t not in allowed]
        sanitized["tools"] = kept
        applied.append(f"removed_tools:{','.join(removed)}")

    return {
        "sanitized_config": sanitized,
        "policy_evaluation": result,
        "applied_changes": applied,
    }


# ── FastAPI Router ─────────────────────────────────────────────────────────────

from fastapi import APIRouter
from pydantic import BaseModel


governance_v2_router = APIRouter(prefix="/governance", tags=["governance_v2"])


class PolicyEvaluateRequest(BaseModel):
    run_config: Dict[str, Any]
    mode: Optional[str] = None


class PolicyApplyRequest(BaseModel):
    run_config: Dict[str, Any]
    mode: Optional[str] = None


class NarrativeValidateRequest(BaseModel):
    narrative: str
    computed_results: Dict[str, Any]
    tolerance: float = 0.01


@governance_v2_router.post("/policy/evaluate")
def api_policy_evaluate(req: PolicyEvaluateRequest):
    return evaluate_policy(req.run_config, req.mode)


@governance_v2_router.post("/policy/apply")
def api_policy_apply(req: PolicyApplyRequest):
    return apply_policy(req.run_config, req.mode)


@governance_v2_router.post("/narrative/validate")
def api_narrative_validate(req: NarrativeValidateRequest):
    return validate_narrative(req.narrative, req.computed_results, req.tolerance)
