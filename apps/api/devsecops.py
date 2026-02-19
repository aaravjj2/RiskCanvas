"""
RiskCanvas v4.48.0–v4.49.0 — DevSecOps Pack (Wave 25)

Provides:
- Deterministic secret scanning (regex rules on provided text/diffs)
- Rule packs versioned + exportable
- Deterministic SBOM generator from fixture dependency graph (NO live npm/pip calls)
- Attestation pack (commit sha + proof pack hash + policy scan results)
- /exports/devsecops-pack

No external calls at all. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
SEC_VERSION = "v1.0"
ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _sha256_full(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _chain_head() -> str:
    return "devsec_f6a7b8c9d0"


# ─────────────────── Secret Scanning Rule Pack ────────────────────────────────

_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "SEC-001",
        "name": "Hardcoded API Key",
        "severity": "CRITICAL",
        "pattern": r"(?i)(api[-_]?key|apikey)\s*=\s*['\"][A-Za-z0-9\-_]{16,}['\"]",
        "description": "Hardcoded API key detected in source code",
        "remediation": "Move secret to environment variable or secrets manager",
    },
    {
        "rule_id": "SEC-002",
        "name": "Hardcoded Password",
        "severity": "CRITICAL",
        "pattern": r"(?i)(password|passwd|pwd)\s*=\s*['\"][^\s'\"]{8,}['\"]",
        "description": "Hardcoded password detected",
        "remediation": "Replace with environment variable: os.getenv('PASSWORD')",
    },
    {
        "rule_id": "SEC-003",
        "name": "Bearer Token",
        "severity": "HIGH",
        "pattern": r"[Bb]earer\s+[A-Za-z0-9\-_\.]{20,}",
        "description": "Bearer token found in code/diff",
        "remediation": "Revoke token and store in secrets manager",
    },
    {
        "rule_id": "SEC-004",
        "name": "AWS Access Key",
        "severity": "CRITICAL",
        "pattern": r"AKIA[0-9A-Z]{16}",
        "description": "AWS access key ID detected",
        "remediation": "Revoke key immediately and rotate. Use IAM roles instead.",
    },
    {
        "rule_id": "SEC-005",
        "name": "Private Key Block",
        "severity": "CRITICAL",
        "pattern": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "description": "Private key material detected",
        "remediation": "Remove from code, rotate key, and use secrets manager",
    },
    {
        "rule_id": "SEC-006",
        "name": "Database Connection String",
        "severity": "HIGH",
        "pattern": r"(?i)(postgres|mysql|mongodb|redis)://[^\s'\",;]{8,}",
        "description": "Database connection string with credentials",
        "remediation": "Use DATABASE_URL env var, never hardcode credentials",
    },
    {
        "rule_id": "SEC-007",
        "name": "GitHub Personal Token",
        "severity": "HIGH",
        "pattern": r"ghp_[A-Za-z0-9]{36}",
        "description": "GitHub personal access token detected",
        "remediation": "Revoke this token and use short-lived tokens via GitHub Actions",
    },
    {
        "rule_id": "SEC-008",
        "name": "Generic Secret Assignment",
        "severity": "MEDIUM",
        "pattern": r"(?i)(secret|token|auth[-_]?key)\s*=\s*['\"][A-Za-z0-9\-_]{12,}['\"]",
        "description": "Generic secret/token assignment detected",
        "remediation": "Verify this is not a real secret; if so, use environment variables",
    },
]

_RULE_PACK_VERSION = "v1.0.0"
_RULE_PACK_HASH = _sha256({"rules": [r["rule_id"] for r in sorted(_RULES, key=lambda r: r["rule_id"])], "version": _RULE_PACK_VERSION})

# ─────────────────── Demo Fixture Diff ────────────────────────────────────────

_DEMO_DIFF = """\
diff --git a/apps/api/config.py b/apps/api/config.py
index abc123..def456 100644
--- a/apps/api/config.py
+++ b/apps/api/config.py
@@ -1,4 +1,7 @@
 # Configuration loader
-# placeholder credentials
+API_KEY = 'sk-abc123def456ghi789jkl012mno34'
+PASSWORD = 'super_secret_pass_999'
+DATABASE_URL = 'postgresql://admin:insecure_pw123@localhost:5432/riskcanvas'
"""


def scan_diff(content: str) -> Dict[str, Any]:
    """
    Scan content (diff or file text) for secret rule matches.
    Deterministic: same input → same output + hash.
    """
    findings = []
    lines = content.splitlines()

    for rule in sorted(_RULES, key=lambda r: r["rule_id"]):
        pattern = re.compile(rule["pattern"])
        for line_no, line in enumerate(lines, 1):
            # Only scan added lines in diffs (+ lines), or all lines if not a diff
            is_diff = any(l.startswith("+") or l.startswith("-") for l in lines[:5])
            if is_diff and not line.startswith("+"):
                continue
            clean_line = line.lstrip("+").lstrip("-")
            match = pattern.search(clean_line)
            if match:
                findings.append({
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["name"],
                    "severity": rule["severity"],
                    "line_no": line_no,
                    "line_snippet": clean_line[:80] + ("..." if len(clean_line) > 80 else ""),
                    "description": rule["description"],
                    "remediation": rule["remediation"],
                })

    # Deduplicate by (rule_id, line_no)
    seen = set()
    deduped = []
    for f in findings:
        key = (f["rule_id"], f["line_no"])
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    blocker_count = sum(1 for f in deduped if f["severity"] == "CRITICAL")
    warning_count = sum(1 for f in deduped if f["severity"] in ("HIGH", "MEDIUM"))

    result = {
        "scan_input_hash": _sha256({"content": content}),
        "findings": deduped,
        "total_findings": len(deduped),
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "status": "BLOCKED" if blocker_count > 0 else ("WARNINGS" if warning_count > 0 else "CLEAN"),
        "rule_pack_version": _RULE_PACK_VERSION,
        "rule_pack_hash": _RULE_PACK_HASH,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    result["output_hash"] = _sha256(result)
    return result


def validate_rules(rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a set of proposed rule objects for well-formedness."""
    errors = []
    for i, r in enumerate(rules):
        if "rule_id" not in r:
            errors.append(f"Rule[{i}]: missing rule_id")
        if "pattern" not in r:
            errors.append(f"Rule[{i}]: missing pattern")
        elif r["pattern"]:
            try:
                re.compile(r["pattern"])
            except re.error as e:
                errors.append(f"Rule[{i}] invalid regex: {e}")
        if "severity" not in r:
            errors.append(f"Rule[{i}]: missing severity")
        elif r["severity"] not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            errors.append(f"Rule[{i}]: invalid severity '{r['severity']}'")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "rules_checked": len(rules),
        "asof": ASOF,
    }


# ─────────────────── Fixture SBOM ────────────────────────────────────────────

_FIXTURE_SBOM_PACKAGES: List[Dict[str, Any]] = [
    # Python backend
    {"name": "fastapi", "version": "0.104.1", "ecosystem": "pypi", "license": "MIT"},
    {"name": "pydantic", "version": "2.5.0", "ecosystem": "pypi", "license": "MIT"},
    {"name": "uvicorn", "version": "0.24.0", "ecosystem": "pypi", "license": "BSD-3-Clause"},
    {"name": "httpx", "version": "0.25.2", "ecosystem": "pypi", "license": "BSD-3-Clause"},
    {"name": "cryptography", "version": "41.0.7", "ecosystem": "pypi", "license": "Apache-2.0"},
    # Frontend npm
    {"name": "react", "version": "18.2.0", "ecosystem": "npm", "license": "MIT"},
    {"name": "react-dom", "version": "18.2.0", "ecosystem": "npm", "license": "MIT"},
    {"name": "react-router-dom", "version": "6.21.0", "ecosystem": "npm", "license": "MIT"},
    {"name": "typescript", "version": "5.3.3", "ecosystem": "npm", "license": "Apache-2.0"},
    {"name": "vite", "version": "7.3.1", "ecosystem": "npm", "license": "MIT"},
    {"name": "tailwindcss", "version": "3.4.0", "ecosystem": "npm", "license": "MIT"},
    {"name": "@playwright/test", "version": "1.48.0", "ecosystem": "npm", "license": "Apache-2.0"},
    {"name": "lucide-react", "version": "0.344.0", "ecosystem": "npm", "license": "ISC"},
]


def get_sbom() -> Dict[str, Any]:
    """Return deterministic SBOM from fixture dependency graph. No live npm/pip calls."""
    packages = sorted(_FIXTURE_SBOM_PACKAGES, key=lambda p: (p["ecosystem"], p["name"]))
    sbom = {
        "sbom_format": "riskcanvas-sbom-v1",
        "version": SEC_VERSION,
        "component": "riskcanvas",
        "packages": packages,
        "total_packages": len(packages),
        "by_ecosystem": {
            "pypi": sum(1 for p in packages if p["ecosystem"] == "pypi"),
            "npm": sum(1 for p in packages if p["ecosystem"] == "npm"),
        },
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    sbom["sbom_hash"] = _sha256({"packages": [f"{p['name']}@{p['version']}" for p in sorted(packages, key=lambda p: p['name'])]})
    return sbom


def build_attestation(
    commit_sha: str,
    proof_pack_hash: str,
    scan_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a deterministic attestation pack tying:
    - commit_sha
    - proof_pack_hash
    - policy scan results
    """
    attestation = {
        "attestation_type": "riskcanvas-v1",
        "commit_sha": commit_sha,
        "proof_pack_hash": proof_pack_hash,
        "scan_status": scan_results.get("status") if scan_results else "NOT_RUN",
        "scan_output_hash": scan_results.get("output_hash") if scan_results else None,
        "sbom_hash": get_sbom()["sbom_hash"],
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    attestation["attestation_hash"] = _sha256_full(attestation)
    return attestation


def build_devsecops_pack(
    commit_sha: str = "main",
    proof_pack_hash: str = "proof_pack_demo_hash_0000",
    diff_content: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the full DevSecOps pack."""
    if diff_content is None:
        diff_content = _DEMO_DIFF
    scan = scan_diff(diff_content)
    sbom = get_sbom()
    attestation = build_attestation(commit_sha, proof_pack_hash, scan)
    pack = {
        "pack_type": "devsecops-pack",
        "version": SEC_VERSION,
        "scan": scan,
        "sbom": sbom,
        "attestation": attestation,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    pack["pack_hash"] = _sha256(pack)
    return pack


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class ScanDiffRequest(BaseModel):
    content: str = Field(default=_DEMO_DIFF, description="Diff or file content to scan")


class RulesValidateRequest(BaseModel):
    rules: List[Dict[str, Any]]


class DevSecOpsPackRequest(BaseModel):
    commit_sha: str = "main"
    proof_pack_hash: str = "proof_pack_demo_hash_0000"
    diff_content: Optional[str] = None


class AttestationRequest(BaseModel):
    commit_sha: str = "main"
    proof_pack_hash: str = "proof_pack_demo_hash_0000"


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

security_router = APIRouter(prefix="/sec", tags=["security"])


@security_router.get("/rules")
def api_get_rules():
    return {
        "rules": sorted(_RULES, key=lambda r: r["rule_id"]),
        "rule_pack_version": _RULE_PACK_VERSION,
        "rule_pack_hash": _RULE_PACK_HASH,
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


@security_router.post("/scan/diff")
def api_scan_diff(req: ScanDiffRequest):
    return scan_diff(req.content)


@security_router.get("/sbom")
def api_get_sbom():
    return get_sbom()


@security_router.post("/rules/validate")
def api_validate_rules(req: RulesValidateRequest):
    return validate_rules(req.rules)


security_exports_router = APIRouter(prefix="/exports", tags=["security-exports"])


@security_exports_router.post("/devsecops-pack")
def api_devsecops_pack(req: DevSecOpsPackRequest):
    return build_devsecops_pack(
        commit_sha=req.commit_sha,
        proof_pack_hash=req.proof_pack_hash,
        diff_content=req.diff_content,
    )


@security_exports_router.post("/attestation")
def api_attestation(req: AttestationRequest):
    scan = scan_diff(_DEMO_DIFF)
    return build_attestation(req.commit_sha, req.proof_pack_hash, scan)
