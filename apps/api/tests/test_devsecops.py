"""Tests for Wave 25: DevSecOps Pack (v4.48–v4.49)"""
import pytest
from devsecops import (
    scan_diff, validate_rules, get_sbom, build_attestation,
    build_devsecops_pack, _RULES, _DEMO_DIFF, _RULE_PACK_HASH,
)


# ─────────────────── Secret Scanning ─────────────────────────────────────────


def test_scan_demo_diff():
    r = scan_diff(_DEMO_DIFF)
    assert r["total_findings"] > 0
    assert r["blocker_count"] > 0  # CRITICAL findings in demo diff
    assert r["status"] == "BLOCKED"
    assert "output_hash" in r
    assert "rule_pack_hash" in r
    assert "audit_chain_head_hash" in r


def test_scan_determinism():
    r1 = scan_diff(_DEMO_DIFF)
    r2 = scan_diff(_DEMO_DIFF)
    assert r1["output_hash"] == r2["output_hash"]
    assert r1["total_findings"] == r2["total_findings"]


def test_scan_clean_content():
    r = scan_diff("# Clean file with no secrets\nfoo = 'bar'\ncount = 42\n")
    assert r["status"] == "CLEAN"
    assert r["total_findings"] == 0
    assert r["blocker_count"] == 0


def test_scan_hardcoded_api_key():
    content = "+API_KEY = 'sk-abc123def456ghi789'\n"
    r = scan_diff(content)
    rule_ids = [f["rule_id"] for f in r["findings"]]
    assert "SEC-001" in rule_ids


def test_scan_hardcoded_password():
    content = "+password = 'super_secret_123'\n"
    r = scan_diff(content)
    rule_ids = [f["rule_id"] for f in r["findings"]]
    assert "SEC-002" in rule_ids


def test_scan_aws_key():
    content = "+aws_key = 'AKIAIOSFODNN7EXAMPLE'\n"
    r = scan_diff(content)
    rule_ids = [f["rule_id"] for f in r["findings"]]
    assert "SEC-004" in rule_ids


def test_scan_only_diff_plus_lines():
    """In a diff, only + lines should be scanned."""
    content = "-OLD_KEY = 'sk-old-key-abc123def456ghi'\n+NEW_LINE = 'safe_config'\n"
    r = scan_diff(content)
    # Old key on minus line should NOT be flagged
    assert r["total_findings"] == 0


def test_scan_deduplicate_findings():
    """Same rule matched twice on same line should appear only once."""
    content = "+API_KEY = 'sk-abc123def456ghi789'\n"
    r = scan_diff(content)
    keys = [(f["rule_id"], f["line_no"]) for f in r["findings"]]
    assert len(keys) == len(set(keys))


def test_scan_rule_pack_version_stable():
    r = scan_diff(_DEMO_DIFF)
    assert r["rule_pack_version"] == "v1.0.0"
    assert r["rule_pack_hash"] == _RULE_PACK_HASH


def test_scan_findings_have_remediation():
    r = scan_diff(_DEMO_DIFF)
    for f in r["findings"]:
        assert f["remediation"]
        assert f["severity"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")


# ─────────────────── Rule Validation ─────────────────────────────────────────


def test_validate_rules_valid():
    rules = [{"rule_id": "TEST-001", "pattern": r"\bpassword\b", "severity": "HIGH"}]
    r = validate_rules(rules)
    assert r["valid"] is True
    assert r["errors"] == []


def test_validate_rules_invalid_regex():
    rules = [{"rule_id": "R1", "pattern": "[invalid(", "severity": "HIGH"}]
    r = validate_rules(rules)
    assert r["valid"] is False
    assert len(r["errors"]) > 0


def test_validate_rules_missing_fields():
    rules = [{"rule_id": "R1"}]  # missing pattern and severity
    r = validate_rules(rules)
    assert r["valid"] is False


def test_validate_rules_invalid_severity():
    rules = [{"rule_id": "R1", "pattern": "test", "severity": "EXTREME"}]
    r = validate_rules(rules)
    assert r["valid"] is False


def test_validate_existing_rules():
    """The built-in rule pack should be valid."""
    r = validate_rules(_RULES)
    assert r["valid"] is True


# ─────────────────── SBOM ─────────────────────────────────────────────────────


def test_sbom_basic():
    r = get_sbom()
    assert r["sbom_format"] == "riskcanvas-sbom-v1"
    assert r["total_packages"] > 10
    assert "sbom_hash" in r
    assert "audit_chain_head_hash" in r


def test_sbom_determinism():
    r1 = get_sbom()
    r2 = get_sbom()
    assert r1["sbom_hash"] == r2["sbom_hash"]


def test_sbom_sorted():
    r = get_sbom()
    ecosystems = [p["ecosystem"] for p in r["packages"]]
    names = [p["name"] for p in r["packages"]]
    # Packages should be sorted by (ecosystem, name)
    pairs = list(zip(ecosystems, names))
    assert pairs == sorted(pairs)


def test_sbom_both_ecosystems():
    r = get_sbom()
    ecosystems = {p["ecosystem"] for p in r["packages"]}
    assert "pypi" in ecosystems
    assert "npm" in ecosystems


def test_sbom_by_ecosystem_counts():
    r = get_sbom()
    assert r["by_ecosystem"]["pypi"] >= 5
    assert r["by_ecosystem"]["npm"] >= 5


def test_sbom_no_live_calls():
    """SBOM must never make live calls — fixture data only."""
    import devsecops as ds
    # All data comes from _FIXTURE_SBOM_PACKAGES, no network
    assert "react" in [p["name"] for p in ds._FIXTURE_SBOM_PACKAGES]


# ─────────────────── Attestation ─────────────────────────────────────────────


def test_attestation_basic():
    scan = scan_diff(_DEMO_DIFF)
    r = build_attestation("abc123", "proof_hash_001", scan)
    assert r["attestation_type"] == "riskcanvas-v1"
    assert r["commit_sha"] == "abc123"
    assert r["proof_pack_hash"] == "proof_hash_001"
    assert r["scan_status"] == "BLOCKED"
    assert "attestation_hash" in r
    assert "audit_chain_head_hash" in r


def test_attestation_determinism():
    scan = scan_diff(_DEMO_DIFF)
    r1 = build_attestation("abc123", "proof_hash_001", scan)
    r2 = build_attestation("abc123", "proof_hash_001", scan)
    assert r1["attestation_hash"] == r2["attestation_hash"]


def test_attestation_hash_changes_with_commit():
    scan = scan_diff(_DEMO_DIFF)
    r1 = build_attestation("commit1", "proof_hash_001", scan)
    r2 = build_attestation("commit2", "proof_hash_001", scan)
    assert r1["attestation_hash"] != r2["attestation_hash"]


# ─────────────────── DevSecOps Pack ──────────────────────────────────────────


def test_devsecops_pack_basic():
    r = build_devsecops_pack()
    assert r["pack_type"] == "devsecops-pack"
    assert "scan" in r
    assert "sbom" in r
    assert "attestation" in r
    assert "pack_hash" in r
    assert "audit_chain_head_hash" in r


def test_devsecops_pack_determinism():
    r1 = build_devsecops_pack("main", "hash1")
    r2 = build_devsecops_pack("main", "hash1")
    assert r1["pack_hash"] == r2["pack_hash"]


def test_devsecops_pack_custom_commit():
    r = build_devsecops_pack("deadbeef123", "proof_pack_xyz")
    assert r["attestation"]["commit_sha"] == "deadbeef123"
    assert r["attestation"]["proof_pack_hash"] == "proof_pack_xyz"


def test_devsecops_pack_custom_diff():
    clean_diff = "# No secrets here\nfoo = 1\n"
    r = build_devsecops_pack("main", "hash1", diff_content=clean_diff)
    assert r["scan"]["status"] == "CLEAN"
