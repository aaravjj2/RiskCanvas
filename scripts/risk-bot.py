#!/usr/bin/env python3
"""
RiskCanvas Risk Bot — Agentic DevOps assistant for MR/PR review.

Scans merge-request diffs for risk-related changes and posts
automated risk commentary. Designed to run in GitLab CI or as
a GitHub Actions step.

Usage (CI):
    python scripts/risk-bot.py --diff <diff-file> [--output json|markdown]

Usage (standalone):
    git diff main...HEAD > /tmp/diff.txt
    python scripts/risk-bot.py --diff /tmp/diff.txt
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Risk patterns to scan for
RISK_PATTERNS = [
    {
        "id": "SEED_CHANGE",
        "pattern": r"FIXED_SEED|random\.seed|np\.random\.seed",
        "severity": "high",
        "message": "Random seed or fixed-seed constant was modified. This may break determinism.",
    },
    {
        "id": "PRECISION_CHANGE",
        "pattern": r"NUMERIC_PRECISION|round_to_precision|\.round\(",
        "severity": "high",
        "message": "Numeric precision logic was modified. Verify determinism checks still pass.",
    },
    {
        "id": "NEW_DEPENDENCY",
        "pattern": r"^\+.*(?:import |require\(|from .+ import)",
        "severity": "medium",
        "message": "New import detected. Ensure dependency is pinned and audited.",
    },
    {
        "id": "ENV_VAR",
        "pattern": r"os\.getenv|process\.env\.",
        "severity": "medium",
        "message": "Environment variable access modified. Verify defaults are safe for DEMO_MODE.",
    },
    {
        "id": "API_ROUTE_CHANGE",
        "pattern": r"@app\.(get|post|put|delete|patch)\(",
        "severity": "medium",
        "message": "API route changed. Update docs/api.md and verify E2E tests.",
    },
    {
        "id": "DOCKER_CHANGE",
        "pattern": r"^[\+\-].*(?:FROM|EXPOSE|CMD|ENTRYPOINT|ENV)",
        "severity": "low",
        "message": "Dockerfile changed. Rebuild and test container images.",
    },
]


def scan_diff(diff_text: str) -> list[dict[str, Any]]:
    """Scan a unified diff for risk patterns."""
    findings: list[dict[str, Any]] = []
    current_file = ""

    for line in diff_text.splitlines():
        # Track current file
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue

        # Only scan added/modified lines
        if not line.startswith("+") or line.startswith("+++"):
            continue

        for pattern_def in RISK_PATTERNS:
            if re.search(pattern_def["pattern"], line):
                findings.append(
                    {
                        "rule": pattern_def["id"],
                        "severity": pattern_def["severity"],
                        "file": current_file,
                        "line": line.strip(),
                        "message": pattern_def["message"],
                    }
                )
                break  # one finding per line

    return findings


def format_markdown(findings: list[dict[str, Any]]) -> str:
    """Format findings as Markdown for MR/PR comments."""
    if not findings:
        return "## RiskCanvas Risk Bot\n\nNo risk-related changes detected."

    lines = ["## RiskCanvas Risk Bot\n"]
    lines.append(f"Found **{len(findings)}** risk-related change(s):\n")

    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵"}

    for f in sorted(findings, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]]):
        emoji = severity_emoji.get(f["severity"], "⚪")
        lines.append(f"- {emoji} **{f['rule']}** ({f['severity']}) in `{f['file']}`")
        lines.append(f"  > {f['message']}")
        lines.append("")

    return "\n".join(lines)


def format_json(findings: list[dict[str, Any]]) -> str:
    """Format findings as JSON."""
    return json.dumps({"findings": findings, "count": len(findings)}, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="RiskCanvas Risk Bot")
    parser.add_argument("--diff", required=True, help="Path to unified diff file")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    diff_path = Path(args.diff)
    if not diff_path.exists():
        print(f"Error: diff file not found: {diff_path}", file=sys.stderr)
        return 1

    diff_text = diff_path.read_text(encoding="utf-8", errors="replace")
    findings = scan_diff(diff_text)

    if args.output == "json":
        print(format_json(findings))
    else:
        print(format_markdown(findings))

    # Exit code: 1 if high-severity findings
    if any(f["severity"] == "high" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
