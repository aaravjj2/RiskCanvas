"""Tests for Wave 22: Approval Workflows (v4.38–v4.40)"""
import pytest
from approvals import (
    create_approval, submit_approval, decide_approval,
    list_approvals, get_approval, build_approval_pack,
    reset_approvals, _APPROVAL_STORE,
)


@pytest.fixture(autouse=True)
def clean_store():
    reset_approvals()
    yield
    reset_approvals()


# ─────────────────── Create ───────────────────────────────────────────────────


def test_create_approval_basic():
    a = create_approval("Test Approval", "A test description", "risk_manager")
    assert a["approval_id"]
    assert len(a["approval_id"]) == 32
    assert a["state"] == "DRAFT"
    assert a["title"] == "Test Approval"
    assert "content_hash" in a
    assert "audit_chain_head_hash" in a


def test_create_approval_deterministic_id():
    a1 = create_approval("Title A", "Desc A", "risk_manager", actor="user1")
    reset_approvals()
    a2 = create_approval("Title A", "Desc A", "risk_manager", actor="user1")
    assert a1["approval_id"] == a2["approval_id"]


def test_create_approval_different_inputs_different_ids():
    a1 = create_approval("Title A", "Desc", "risk_manager")
    a2 = create_approval("Title B", "Desc", "risk_manager")
    assert a1["approval_id"] != a2["approval_id"]


def test_create_approval_idempotent():
    """Creating the same approval twice returns the existing one."""
    a1 = create_approval("Same Title", "Same Desc", "risk_manager", actor="user1")
    a2 = create_approval("Same Title", "Same Desc", "risk_manager", actor="user1")
    assert a1["approval_id"] == a2["approval_id"]
    assert len(_APPROVAL_STORE) == 1


# ─────────────────── Submit ───────────────────────────────────────────────────


def test_submit_approval():
    a = create_approval("To Submit", "Desc", "risk_manager")
    s = submit_approval(a["approval_id"])
    assert s["state"] == "SUBMITTED"


def test_submit_approval_wrong_state():
    a = create_approval("Test", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    with pytest.raises(ValueError, match="Cannot submit"):
        submit_approval(a["approval_id"])


def test_submit_nonexistent():
    with pytest.raises(ValueError, match="not found"):
        submit_approval("nonexistent_id_xxx")


# ─────────────────── Decide ───────────────────────────────────────────────────


def test_decide_approve():
    a = create_approval("To Decide", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    d = decide_approval(a["approval_id"], "approved", "Looks good")
    assert d["state"] == "APPROVED"
    assert d["decision_reason"] == "Looks good"


def test_decide_reject():
    a = create_approval("To Reject", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    d = decide_approval(a["approval_id"], "rejected", "Does not meet criteria")
    assert d["state"] == "REJECTED"


def test_decide_case_insensitive():
    a = create_approval("Test", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    d = decide_approval(a["approval_id"], "APPROVED", "OK")
    assert d["state"] == "APPROVED"


def test_decide_invalid_decision():
    a = create_approval("Test", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    with pytest.raises(ValueError, match="Invalid decision"):
        decide_approval(a["approval_id"], "MAYBE", "unclear")


def test_decide_from_draft_fails():
    a = create_approval("Test", "Desc", "risk_manager")
    with pytest.raises(ValueError, match="Cannot decide"):
        decide_approval(a["approval_id"], "APPROVED", "reason")


def test_decide_approved_is_terminal():
    a = create_approval("Test", "Desc", "risk_manager")
    submit_approval(a["approval_id"])
    decide_approval(a["approval_id"], "APPROVED", "OK")
    with pytest.raises(ValueError, match="Cannot decide"):
        decide_approval(a["approval_id"], "REJECTED", "Changed mind")


# ─────────────────── List + Get ───────────────────────────────────────────────


def test_list_approvals_all():
    create_approval("A1", "D", "rm")
    create_approval("A2", "D", "rm", actor="user2")
    r = list_approvals()
    assert r["total"] == 2


def test_list_approvals_by_state():
    a1 = create_approval("A1", "D", "rm")
    a2 = create_approval("A2", "D", "rm", actor="user2")
    submit_approval(a1["approval_id"])
    r = list_approvals("SUBMITTED")
    assert r["total"] == 1
    assert r["approvals"][0]["approval_id"] == a1["approval_id"]


def test_get_existing():
    a = create_approval("Get Me", "D", "rm")
    r = get_approval(a["approval_id"])
    assert r["title"] == "Get Me"


def test_get_nonexistent():
    with pytest.raises(ValueError, match="not found"):
        get_approval("nonexistent")


# ─────────────────── Pack ─────────────────────────────────────────────────────


def test_approval_pack():
    a = create_approval("Pack Test", "D", "rm")
    submit_approval(a["approval_id"])
    decide_approval(a["approval_id"], "APPROVED", "good")
    pack = build_approval_pack(a["approval_id"])
    assert pack["pack_type"] == "approval-pack"
    assert pack["approval"]["state"] == "APPROVED"
    assert len(pack["audit_trail"]) >= 3  # CREATED, SUBMITTED, APPROVED
    assert "pack_hash" in pack


def test_approval_pack_determinism():
    a = create_approval("Pack Det", "D", "rm")
    submit_approval(a["approval_id"])
    decide_approval(a["approval_id"], "APPROVED", "OK")
    p1 = build_approval_pack(a["approval_id"])
    p2 = build_approval_pack(a["approval_id"])
    assert p1["pack_hash"] == p2["pack_hash"]
