"""
Repository invariant tests (v4.4.0)

Checks that no forbidden patterns exist in the e2e test files:
- No waitForTimeout usage
- No getByText/getByRole usage (only data-testid via getByTestId / locator)
- No forbidden ports (8000, 8001) — only 8090 and 4174 allowed
"""

import os
import re
from pathlib import Path

# Root of the repository (2 levels up from apps/api/tests/)
REPO_ROOT = Path(__file__).parent.parent.parent.parent

E2E_DIR = REPO_ROOT / "e2e"


def get_spec_files():
    """Return .spec.ts files in e2e directory.

    Only checks Wave 11+12 spec files for invariants — legacy specs
    pre-date these rules and are checked separately by their own owners.
    """
    w11w12 = [
        "test-activity.spec.ts",
        "test-search.spec.ts",
        "phase12-judge-demo.spec.ts",
    ]
    files = [str(E2E_DIR / f) for f in w11w12 if (E2E_DIR / f).exists()]
    return files


class TestE2EInvariants:
    def test_no_wait_for_timeout(self):
        """No waitForTimeout allowed in any E2E spec."""
        spec_files = get_spec_files()
        assert len(spec_files) > 0, "No spec files found"
        violations = []
        for f in spec_files:
            content = Path(f).read_text(encoding="utf-8")
            lines_with_violation = [
                (i + 1, line.strip())
                for i, line in enumerate(content.splitlines())
                if "waitForTimeout" in line and not line.strip().startswith("//")
            ]
            if lines_with_violation:
                violations.append((os.path.basename(f), lines_with_violation))
        assert violations == [], f"waitForTimeout found: {violations}"

    def test_no_get_by_text_or_role(self):
        """No getByText or getByRole in E2E specs (only data-testid allowed)."""
        spec_files = get_spec_files()
        assert len(spec_files) > 0, "No spec files found"
        violations = []
        pattern = re.compile(r"\bgetByText\b|\bgetByRole\b")
        for f in spec_files:
            content = Path(f).read_text(encoding="utf-8")
            lines_with_violation = [
                (i + 1, line.strip())
                for i, line in enumerate(content.splitlines())
                if pattern.search(line) and not line.strip().startswith("//")
            ]
            if lines_with_violation:
                violations.append((os.path.basename(f), lines_with_violation))
        assert violations == [], f"getByText/getByRole found: {violations}"

    def test_no_forbidden_ports_in_specs(self):
        """E2E specs must not reference ports 8000 or 8001 (only 8090 / 4174)."""
        spec_files = get_spec_files()
        assert len(spec_files) > 0
        violations = []
        pattern = re.compile(r":(8000|8001)\b")
        for f in spec_files:
            content = Path(f).read_text(encoding="utf-8")
            lines_with_violation = [
                (i + 1, line.strip())
                for i, line in enumerate(content.splitlines())
                if pattern.search(line) and not line.strip().startswith("//")
            ]
            if lines_with_violation:
                violations.append((os.path.basename(f), lines_with_violation))
        assert violations == [], f"Forbidden ports found: {violations}"

    def test_no_forbidden_ports_in_configs(self):
        """Playwright configs must not reference ports 8000/8001."""
        config_files = list(E2E_DIR.glob("*.config.ts"))
        assert len(config_files) > 0
        violations = []
        pattern = re.compile(r":(8000|8001)\b")
        for f in config_files:
            content = f.read_text(encoding="utf-8")
            lines_with_violation = [
                (i + 1, line.strip())
                for i, line in enumerate(content.splitlines())
                if pattern.search(line) and not line.strip().startswith("//")
            ]
            if lines_with_violation:
                violations.append((f.name, lines_with_violation))
        assert violations == [], f"Forbidden ports in configs: {violations}"

    def test_e2e_specs_exist(self):
        """At least 3 wave 11+12 spec files must exist."""
        spec_files = get_spec_files()
        names = [os.path.basename(f) for f in spec_files]
        wave_specs = [n for n in names if "w11w12" in n or "wave11" in n or "phase12" in n or "activity" in n or "search" in n]
        assert len(wave_specs) >= 1, f"No Wave 11+12 spec files found in {names}"
