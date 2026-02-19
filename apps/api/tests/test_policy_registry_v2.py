"""Tests for Policy Registry V2 (Wave 30, v4.66-v4.69)"""
import pytest
from policy_registry_v2 import (
    reset_policies_v2, create_policy, publish_policy, rollback_policy,
    list_policies, get_policy_versions,
)


@pytest.fixture(autouse=True)
def clean():
    reset_policies_v2()
    yield
    reset_policies_v2()


def test_create_policy():
    p = create_policy("risk-policy", "Risk Policy", "All positions must be assessed.", ["risk"])
    assert p["slug"] == "risk-policy"
    assert p["version_number"] == 1
    assert p["status"] == "draft"
    assert p["content_hash"]
    assert p["audit_chain_hash"]


def test_create_version_increments():
    p1 = create_policy("risk-policy", "Risk Policy", "Body v1.", ["risk"])
    p2 = create_policy("risk-policy", "Risk Policy", "Body v2.", ["risk", "compliance"])
    assert p1["version_number"] == 1
    assert p2["version_number"] == 2


def test_create_different_slugs():
    p1 = create_policy("policy-a", "Policy A", "Body A.", [])
    p2 = create_policy("policy-b", "Policy B", "Body B.", [])
    assert p1["version_number"] == 1
    assert p2["version_number"] == 1


def test_publish_policy():
    create_policy("risk-policy", "Risk Policy", "Body.", ["risk"])
    published = publish_policy("risk-policy")
    assert published["status"] == "published"
    assert published["version_number"] == 1


def test_publish_idempotent():
    create_policy("risk-policy", "Risk Policy", "Body.", ["risk"])
    p1 = publish_policy("risk-policy")
    p2 = publish_policy("risk-policy")
    assert p1["status"] == "published"
    assert p2["status"] == "published"


def test_publish_specific_version():
    create_policy("risk-policy", "Risk Policy", "Body v1.", ["risk"])
    create_policy("risk-policy", "Risk Policy", "Body v2.", ["risk"])
    published = publish_policy("risk-policy", version_number=1)
    assert published["version_number"] == 1
    assert published["status"] == "published"


def test_publish_not_found():
    with pytest.raises(ValueError, match="not found"):
        publish_policy("nonexistent-slug")


def test_rollback_policy():
    create_policy("risk-policy", "Risk Policy", "Body v1.", ["risk"])
    create_policy("risk-policy", "Risk Policy", "Body v2.", ["risk"])
    rollback = rollback_policy("risk-policy", to_version=1)
    assert rollback["version_number"] == 3
    assert rollback["rollback_from_version"] == 1
    assert "Rolled back" in rollback["note"]


def test_rollback_not_found():
    with pytest.raises(ValueError, match="not found"):
        rollback_policy("nonexistent-slug", to_version=1)


def test_rollback_version_not_found():
    create_policy("risk-policy", "Risk Policy", "Body v1.", ["risk"])
    with pytest.raises(ValueError, match="not found"):
        rollback_policy("risk-policy", to_version=99)


def test_list_policies_empty():
    assert list_policies() == []


def test_list_policies():
    create_policy("policy-a", "Policy A", "Body A.", [])
    create_policy("policy-b", "Policy B", "Body B.", [])
    policies = list_policies()
    assert len(policies) == 2
    slugs = {p["slug"] for p in policies}
    assert slugs == {"policy-a", "policy-b"}


def test_get_versions():
    create_policy("risk-policy", "RP", "v1.", [])
    create_policy("risk-policy", "RP", "v2.", [])
    versions = get_policy_versions("risk-policy")
    assert len(versions) == 2
    assert versions[0]["version_number"] == 1
    assert versions[1]["version_number"] == 2


def test_get_versions_not_found():
    with pytest.raises(ValueError, match="not found"):
        get_policy_versions("nonexistent")


def test_hash_chain_consistency():
    p1 = create_policy("risk-policy", "RP", "v1.", [])
    p2 = create_policy("risk-policy", "RP", "v2.", [])
    # parent_hash of v2 should equal audit_chain_hash of v1
    assert p2["parent_hash"] == p1["audit_chain_hash"]


def test_content_hash_determinism():
    p1 = create_policy("risk-policy", "RP", "Body.", ["risk"])
    reset_policies_v2()
    p2 = create_policy("risk-policy", "RP", "Body.", ["risk"])
    assert p1["content_hash"] == p2["content_hash"]
    assert p1["policy_id"] == p2["policy_id"]
