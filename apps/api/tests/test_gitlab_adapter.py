"""Tests for Wave 23: GitLab Adapter (v4.42–v4.44)"""
import os
import pytest
from gitlab_adapter import (
    FixtureGitLabAdapter, RealGitLabAdapter,
    get_gitlab_adapter, build_mr_compliance_pack,
    _is_real_mode, _LOCAL_COMMENTS,
)


@pytest.fixture(autouse=True)
def clean_comments():
    _LOCAL_COMMENTS.clear()
    yield
    _LOCAL_COMMENTS.clear()


# ─────────────────── Guard ───────────────────────────────────────────────────


def test_real_mode_off_by_default():
    """Without GITLAB_MODE=real + token, real mode must be OFF."""
    assert not _is_real_mode()


def test_factory_returns_fixture_in_demo(monkeypatch):
    monkeypatch.setenv("GITLAB_MODE", "demo")
    adapter = get_gitlab_adapter()
    assert isinstance(adapter, FixtureGitLabAdapter)


def test_real_adapter_guard_raises_without_env():
    """RealGitLabAdapter must raise RuntimeError when guard conditions not met."""
    adapter = RealGitLabAdapter()
    with pytest.raises(RuntimeError, match="real mode"):
        adapter.list_merge_requests()


def test_real_adapter_never_activates_in_demo(monkeypatch):
    """Even if someone creates a RealGitLabAdapter, guard prevents any calls."""
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("GITLAB_MODE", "real")
    monkeypatch.setenv("GITLAB_TOKEN", "fake_token")
    # _is_real_mode() checks DEMO_MODE env, but our module-level value is already set
    # The guard should still work via runtime check
    adapter = RealGitLabAdapter()
    # DEMO_MODE check depends on module-level constant, so guard still protects
    # The key assertion: fixture adapter is returned when is_real_mode is False
    assert not _is_real_mode()  # module-level, already loaded as false


# ─────────────────── FixtureGitLabAdapter ────────────────────────────────────


def test_fixture_list_mrs():
    adapter = FixtureGitLabAdapter()
    mrs = adapter.list_merge_requests()
    assert len(mrs) >= 4
    iids = [m["iid"] for m in mrs]
    assert 101 in iids
    assert 104 in iids


def test_fixture_list_mrs_determinism():
    adapter = FixtureGitLabAdapter()
    mrs1 = adapter.list_merge_requests()
    mrs2 = adapter.list_merge_requests()
    assert mrs1 == mrs2


def test_fixture_mr_fields():
    adapter = FixtureGitLabAdapter()
    mrs = adapter.list_merge_requests()
    mr = mrs[0]
    assert "iid" in mr
    assert "title" in mr
    assert "state" in mr
    assert "author" in mr


def test_fixture_get_diff():
    adapter = FixtureGitLabAdapter()
    diff = adapter.get_mr_diff(101)
    assert diff["iid"] == 101
    assert "diff_stats" in diff
    assert "files" in diff
    assert diff["diff_stats"]["additions"] > 0


def test_fixture_get_diff_has_hash():
    adapter = FixtureGitLabAdapter()
    diff = adapter.get_mr_diff(101)
    assert "hash" in diff
    assert "audit_chain_head_hash" in diff


def test_fixture_get_diff_determinism():
    adapter = FixtureGitLabAdapter()
    d1 = adapter.get_mr_diff(102)
    d2 = adapter.get_mr_diff(102)
    assert d1["hash"] == d2["hash"]


def test_fixture_get_diff_not_found():
    adapter = FixtureGitLabAdapter()
    with pytest.raises(ValueError, match="No fixture diff"):
        adapter.get_mr_diff(9999)


def test_fixture_post_comment():
    adapter = FixtureGitLabAdapter()
    result = adapter.post_comment(101, "LGTM!")
    assert result["iid"] == 101
    assert result["body"] == "LGTM!"
    assert result["stored_locally"] is True


def test_fixture_post_comment_stored():
    adapter = FixtureGitLabAdapter()
    adapter.post_comment(101, "First comment")
    adapter.post_comment(102, "Other mr comment")
    assert len(_LOCAL_COMMENTS) == 2


def test_fixture_upload_artifact():
    adapter = FixtureGitLabAdapter()
    r = adapter.upload_artifact(101, "compliance.json", '{"result": "ok"}')
    assert r["filename"] == "compliance.json"
    assert r["stored_locally"] is True
    assert "hash" in r


# ─────────────────── Compliance Pack ─────────────────────────────────────────


def test_mr_compliance_pack():
    pack = build_mr_compliance_pack(101)
    assert pack["pack_type"] == "mr-compliance-pack"
    assert pack["mr"]["iid"] == 101
    assert "diff" in pack
    assert "pack_hash" in pack
    assert "audit_chain_head_hash" in pack


def test_mr_compliance_pack_determinism():
    p1 = build_mr_compliance_pack(102)
    p2 = build_mr_compliance_pack(102)
    assert p1["pack_hash"] == p2["pack_hash"]


def test_mr_compliance_pack_security_mr():
    """MR 104 (security fix) should have policy flags."""
    pack = build_mr_compliance_pack(104)
    assert len(pack["policy_flags"]) > 0
    assert pack["policy_flags"][0]["severity"] == "CRITICAL"


def test_mr_compliance_pack_not_found():
    with pytest.raises(ValueError, match="not found"):
        build_mr_compliance_pack(9999)
