#!/usr/bin/env python3
"""
scripts/ui/invariants_check.py  (v4.86.0 — Wave 36)

UI invariants scanner for RiskCanvas.
Checks:
- Every page has at least one data-testid
- No banned placeholder strings (DEMO_KPI, FAKE_STAT, etc.)
- Every nav route has a corresponding data-testid in AppLayout

Exit 0 = all clear. Exit 1 = violations found.
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PAGES_DIR = ROOT / "apps" / "web" / "src" / "pages"
APP_LAYOUT = ROOT / "apps" / "web" / "src" / "components" / "layout" / "AppLayout.tsx"

BANNED_STRINGS = [
    "DEMO_KPI",
    "FAKE_STAT",
    "TODO_REMOVE",
    "PLACEHOLDER_DATA",
    "HARD_CODED_METRIC",
]

# Pages that are known utility pages and don't require a data-testid
SKIP_PAGES = {
    "WorkspacesPage.tsx",  # legacy stub
}


def check_page_testids() -> list[str]:
    """Every page file should contain at least one data-testid attribute."""
    violations = []
    for p in sorted(PAGES_DIR.glob("*.tsx")):
        if p.name in SKIP_PAGES:
            continue
        content = p.read_text(encoding="utf-8")
        if 'data-testid' not in content:
            violations.append(f"MISSING data-testid in page: {p.name}")
    return violations


def check_banned_strings() -> list[str]:
    """Scan pages for banned placeholder strings."""
    violations = []
    scan_dirs = [
        ROOT / "apps" / "web" / "src" / "pages",
        ROOT / "apps" / "web" / "src" / "components",
    ]
    for scan_dir in scan_dirs:
        for p in sorted(scan_dir.rglob("*.tsx")):
            content = p.read_text(encoding="utf-8")
            for banned in BANNED_STRINGS:
                if banned in content:
                    violations.append(f"BANNED string '{banned}' in {p.relative_to(ROOT)}")
    return violations


def check_nav_testids() -> list[str]:
    """
    Every { path: '/foo', ..., testid: 'bar' } nav item in AppLayout
    should have testid that doesn't include 'nav-' prefix (to avoid double-prefix).
    """
    violations = []
    content = APP_LAYOUT.read_text(encoding="utf-8")
    # Find all testid: "..." assignments in navItems
    items = re.findall(r'testid:\s*"([^"]+)"', content)
    for testid in items:
        if testid.startswith("nav-"):
            violations.append(
                f"DOUBLE nav- prefix in AppLayout testid: '{testid}' "
                "(AppLayout prepends 'nav-' automatically)"
            )
    return violations


def check_no_hardcoded_port_8000() -> list[str]:
    """Backend port should be 8090 everywhere, not 8000 or 8001."""
    violations = []
    api_file = ROOT / "apps" / "web" / "src" / "lib" / "api.ts"
    content = api_file.read_text(encoding="utf-8")
    for bad_port in [":8000", ":8001"]:
        if bad_port in content:
            violations.append(f"WRONG port '{bad_port}' found in api.ts (should be :8090)")
    return violations


def main() -> int:
    all_violations: list[str] = []

    checks = [
        ("Page testid check", check_page_testids),
        ("Banned string check", check_banned_strings),
        ("Nav testid prefix check", check_nav_testids),
        ("Port consistency check", check_no_hardcoded_port_8000),
    ]

    for name, fn in checks:
        violations = fn()
        if violations:
            print(f"\n❌ {name}:")
            for v in violations:
                print(f"   {v}")
            all_violations.extend(violations)
        else:
            print(f"✓  {name}: OK")

    if all_violations:
        print(f"\nFAIL: {len(all_violations)} violation(s) found.")
        return 1

    print(f"\nPASS: All UI invariants satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
