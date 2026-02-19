"""
tests/test_ui_invariants.py  (v4.86.0 — Wave 36)

Pytest-based UI invariants gate. Runs the invariants_check.py script
deterministically. All checks must pass with 0 violations.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT = ROOT / "scripts" / "ui" / "invariants_check.py"


def _run_check(check_name: str) -> list[str]:
    """Run the invariants check script and return violations for a named check."""
    # We'll import directly rather than subprocess to keep it fast + deterministic
    import importlib.util
    spec = importlib.util.spec_from_file_location("invariants_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    fn = getattr(mod, check_name)
    return fn()


def test_page_testids():
    """Every page file must have at least one data-testid."""
    violations = _run_check("check_page_testids")
    assert violations == [], f"Page testid violations:\n" + "\n".join(violations)


def test_banned_strings():
    """No banned placeholder strings in pages or components."""
    violations = _run_check("check_banned_strings")
    assert violations == [], f"Banned string violations:\n" + "\n".join(violations)


def test_nav_testid_no_nav_prefix():
    """Nav items must not have 'nav-' prefix in their testid field."""
    violations = _run_check("check_nav_testids")
    assert violations == [], f"Nav testid violations:\n" + "\n".join(violations)


def test_no_hardcoded_wrong_port():
    """api.ts must use port 8090, not 8000 or 8001."""
    violations = _run_check("check_no_hardcoded_port_8000")
    assert violations == [], f"Port violations:\n" + "\n".join(violations)


def test_invariants_script_exits_zero():
    """Complete invariants check exits with code 0."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Invariants check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_testid_catalog_generation():
    """Testid catalog script runs and generates docs/TESTIDS.md."""
    catalog_script = ROOT / "scripts" / "ui" / "testid_catalog.py"
    result = subprocess.run(
        [sys.executable, str(catalog_script)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Testid catalog failed:\n{result.stdout}\n{result.stderr}"
    )
    output_file = ROOT / "docs" / "TESTIDS.md"
    assert output_file.exists(), "TESTIDS.md was not generated"
    content = output_file.read_text()
    assert "data-testid" in content.lower() or "testid" in content.lower()
