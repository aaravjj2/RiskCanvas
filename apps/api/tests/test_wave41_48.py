"""
Wave 41-48 Enterprise Layer Tests (v4.98.0 → v5.21.0)
"""
import pytest
from httpx import AsyncClient, ASGITransport

from tenancy_v2 import (
    list_tenants, list_members, add_member, get_demo_context, require_perm,
    get_tenant, has_permission, DEFAULT_TENANT_ID, ROLE_PERMISSIONS,
    DEMO_TENANTS, DEMO_USERS,
)
from artifacts_registry import list_artifacts, get_artifact, get_download_descriptor
from attestations import (
    issue_attestation, list_attestations, get_attestation,
    get_chain_head, build_receipts_pack,
)
from compliance_pack import generate_compliance_pack, list_compliance_packs
from judge_mode_v2 import (
    generate_judge_pack_v2, list_judge_packs_v2, get_pack_definitions, PACK_DEFS,
)
from main import app


@pytest.fixture()
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# =============================================================================
# Wave 41 — Tenancy v2
# =============================================================================
class TestTenancyV2:
    def test_list_tenants_returns_list(self):
        tenants = list_tenants()
        assert isinstance(tenants, list)
        assert len(tenants) >= 1

    def test_default_tenant_exists(self):
        ids = [t["tenant_id"] for t in list_tenants()]
        assert DEFAULT_TENANT_ID in ids

    def test_tenant_has_required_fields(self):
        for t in list_tenants():
            assert "tenant_id" in t
            assert "name" in t
            assert "slug" in t

    def test_get_tenant_returns_dict(self):
        t = get_tenant(DEFAULT_TENANT_ID)
        assert isinstance(t, dict)
        assert t["tenant_id"] == DEFAULT_TENANT_ID

    def test_get_tenant_unknown_raises(self):
        with pytest.raises(Exception):
            get_tenant("nonexistent-tenant-xyz-000")

    def test_list_members_default_tenant(self):
        members = list_members(DEFAULT_TENANT_ID)
        assert isinstance(members, list)
        assert len(members) >= 1

    def test_member_has_required_fields(self):
        for m in list_members(DEFAULT_TENANT_ID):
            assert "user_id" in m
            assert "email" in m
            assert "role" in m

    def test_add_member_returns_member(self):
        result = add_member(DEFAULT_TENANT_ID, "newuser@example.com", "ANALYST")
        assert result["email"] == "newuser@example.com"
        assert result["role"] == "ANALYST"
        assert "user_id" in result

    def test_add_member_invalid_role_raises(self):
        with pytest.raises(Exception):
            add_member(DEFAULT_TENANT_ID, "x@x.com", "SUPERADMIN_INVALID")

    def test_get_demo_context_returns_dict(self):
        ctx = get_demo_context(x_demo_role="OWNER")
        assert "role" in ctx
        assert ctx["role"] == "OWNER"

    def test_get_demo_context_includes_permissions(self):
        ctx = get_demo_context(x_demo_role="OWNER")
        assert "permissions" in ctx
        assert isinstance(ctx["permissions"], list)

    def test_role_permissions_structure(self):
        assert isinstance(ROLE_PERMISSIONS, dict)
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(perms, list)

    def test_has_permission_owner_has_admin_write(self):
        assert has_permission("OWNER", "admin.write") is True

    def test_has_permission_viewer_denied_admin_write(self):
        assert has_permission("VIEWER", "admin.write") is False

    def test_require_perm_owner_ctx_passes(self):
        ctx = get_demo_context(x_demo_role="OWNER")
        require_perm(ctx, "admin.write")  # should not raise

    def test_require_perm_viewer_ctx_denied(self):
        ctx = get_demo_context(x_demo_role="VIEWER")
        with pytest.raises(Exception):
            require_perm(ctx, "admin.write")

    def test_demo_tenants_deterministic(self):
        t1 = list_tenants()
        t2 = list_tenants()
        assert [t["tenant_id"] for t in t1] == [t["tenant_id"] for t in t2]

    def test_demo_users_non_empty(self):
        assert len(DEMO_USERS) >= 4

    def test_demo_tenants_non_empty(self):
        assert len(DEMO_TENANTS) >= 1


class TestTenancyV2HTTP:
    async def test_get_tenants_200(self, client):
        resp = await client.get("/tenants", headers={"x-demo-role": "OWNER"})
        assert resp.status_code == 200
        body = resp.json()
        # API wraps tenants in {"tenants": [...], "current_role": ...}
        assert "tenants" in body or isinstance(body, list)

    async def test_get_members_200(self, client):
        resp = await client.get(
            f"/tenants/{DEFAULT_TENANT_ID}/members",
            headers={"x-demo-role": "OWNER"},
        )
        assert resp.status_code == 200
        body = resp.json()
        # API may return {"members": [...]} or a list directly
        members = body.get("members", body) if isinstance(body, dict) else body
        assert isinstance(members, list)

    async def test_post_member_returns_email(self, client):
        resp = await client.post(
            f"/tenants/{DEFAULT_TENANT_ID}/members",
            json={"email": "wave41http@example.com", "role": "ANALYST"},
            headers={"x-demo-role": "OWNER"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["email"] == "wave41http@example.com"

    async def test_get_context_200(self, client):
        resp = await client.get("/tenants/~context", headers={"x-demo-role": "ANALYST"})
        assert resp.status_code == 200
        assert "role" in resp.json()


# =============================================================================
# Wave 42 — Artifact Registry
# =============================================================================
class TestArtifactsRegistry:
    def test_list_artifacts_nonempty(self):
        results = list_artifacts()
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_artifact_has_required_fields(self):
        for a in list_artifacts():
            assert "artifact_id" in a
            assert "type" in a
            assert "sha256" in a
            assert "created_at" in a

    def test_get_artifact_by_id(self):
        first = list_artifacts()[0]
        fetched = get_artifact(first["artifact_id"])
        assert fetched["artifact_id"] == first["artifact_id"]

    def test_get_artifact_unknown_raises(self):
        with pytest.raises(Exception):
            get_artifact("no-such-artifact-000-zzz")

    def test_artifact_sha256_deterministic(self):
        a1 = list_artifacts()
        a2 = list_artifacts()
        for x, y in zip(a1, a2):
            assert x["sha256"] == y["sha256"]

    def test_download_descriptor_has_url(self):
        first = list_artifacts()[0]
        desc = get_download_descriptor(first["artifact_id"])
        assert "url" in desc

    def test_download_descriptor_has_sha256(self):
        first = list_artifacts()[0]
        desc = get_download_descriptor(first["artifact_id"])
        assert "sha256" in desc

    def test_list_artifacts_filter_by_tenant(self):
        all_arts = list_artifacts()
        tenant_id = all_arts[0].get("tenant_id", DEFAULT_TENANT_ID)
        filtered = list_artifacts(tenant_id=tenant_id)
        assert all(a.get("tenant_id") == tenant_id for a in filtered)


class TestArtifactsHTTP:
    async def test_list_artifacts_200(self, client):
        resp = await client.get("/artifacts")
        assert resp.status_code == 200
        body = resp.json()
        arts = body.get("artifacts", body) if isinstance(body, dict) else body
        assert isinstance(arts, list)

    async def test_get_artifact_200(self, client):
        arts = list_artifacts()
        resp = await client.get(f"/artifacts/{arts[0]['artifact_id']}")
        assert resp.status_code == 200

    async def test_get_artifact_404(self, client):
        resp = await client.get("/artifacts/no-such-artifact-zzz-000")
        assert resp.status_code == 404

    async def test_get_artifact_downloads_200(self, client):
        arts = list_artifacts()
        resp = await client.get(f"/artifacts/{arts[0]['artifact_id']}/downloads")
        assert resp.status_code == 200


# =============================================================================
# Wave 43 — Attestations
# =============================================================================
class TestAttestations:
    def test_list_attestations_nonempty(self):
        items = list_attestations(DEFAULT_TENANT_ID)
        assert isinstance(items, list)
        assert len(items) >= 1

    def test_attestation_has_required_fields(self):
        for a in list_attestations(DEFAULT_TENANT_ID):
            assert "attestation_id" in a
            assert "issued_at" in a

    def test_get_attestation_by_id(self):
        first = list_attestations(DEFAULT_TENANT_ID)[0]
        fetched = get_attestation(first["attestation_id"])
        assert fetched["attestation_id"] == first["attestation_id"]

    def test_get_attestation_unknown_raises(self):
        with pytest.raises(Exception):
            get_attestation("no-such-attestation-000-zzz")

    def test_chain_head_returns_string_or_none(self):
        head = get_chain_head(DEFAULT_TENANT_ID)
        assert head is None or isinstance(head, str)

    def test_chain_head_nonempty_for_seeded_tenant(self):
        head = get_chain_head(DEFAULT_TENANT_ID)
        assert head is not None

    def test_attestations_deterministic_count(self):
        a1 = list_attestations(DEFAULT_TENANT_ID)
        a2 = list_attestations(DEFAULT_TENANT_ID)
        assert len(a1) == len(a2)

    def test_build_receipts_pack_has_tenant_id(self):
        pack = build_receipts_pack(DEFAULT_TENANT_ID)
        assert isinstance(pack, dict)
        assert pack["tenant_id"] == DEFAULT_TENANT_ID

    def test_issue_attestation_returns_id(self):
        att = issue_attestation(
            tenant_id=DEFAULT_TENANT_ID,
            subject="test-artifact-001",
            statement_type="test_event",
            issued_by="test_suite",
            input_hash="abc123",
            output_hash="def456",
        )
        assert "attestation_id" in att


class TestAttestationsHTTP:
    async def test_list_attestations_200(self, client):
        resp = await client.get("/attestations")
        assert resp.status_code == 200
        body = resp.json()
        atts = body.get("attestations", body) if isinstance(body, dict) else body
        assert isinstance(atts, list)

    async def test_get_attestation_200(self, client):
        atts = list_attestations(DEFAULT_TENANT_ID)
        resp = await client.get(f"/attestations/{atts[0]['attestation_id']}")
        assert resp.status_code == 200

    async def test_get_attestation_404(self, client):
        resp = await client.get("/attestations/no-such-att-zzz-000")
        assert resp.status_code == 404

    async def test_post_receipts_pack_200(self, client):
        resp = await client.post("/attestations/receipts-pack")
        assert resp.status_code == 200
        body = resp.json()
        assert "tenant_id" in body


# =============================================================================
# Wave 44 — Compliance Pack
# =============================================================================
class TestCompliancePack:
    def test_generate_pack_returns_dict(self):
        pack = generate_compliance_pack(DEFAULT_TENANT_ID)
        assert isinstance(pack, dict)
        assert "pack_id" in pack

    def test_pack_has_files_list(self):
        pack = generate_compliance_pack(DEFAULT_TENANT_ID)
        assert "files" in pack
        assert isinstance(pack["files"], list)
        assert len(pack["files"]) >= 1

    def test_pack_file_has_name_and_content(self):
        pack = generate_compliance_pack(DEFAULT_TENANT_ID)
        for f in pack["files"]:
            assert "name" in f
            assert "content" in f
            assert "sha256" in f

    def test_list_packs_nonempty_after_generate(self):
        generate_compliance_pack(DEFAULT_TENANT_ID)
        packs = list_compliance_packs(DEFAULT_TENANT_ID)
        assert isinstance(packs, list)
        assert len(packs) >= 1

    def test_pack_id_is_string(self):
        p = generate_compliance_pack(DEFAULT_TENANT_ID)
        assert isinstance(p["pack_id"], str) and len(p["pack_id"]) > 0

    def test_pack_contains_system_overview(self):
        pack = generate_compliance_pack(DEFAULT_TENANT_ID)
        names = [f["name"] for f in pack["files"]]
        assert any("system_overview" in n for n in names)

    def test_pack_has_tenant_id(self):
        pack = generate_compliance_pack(DEFAULT_TENANT_ID)
        assert pack.get("tenant_id") == DEFAULT_TENANT_ID


class TestComplianceHTTP:
    async def test_post_generate_pack_200(self, client):
        resp = await client.post(
            "/compliance/generate-pack", json={"window": "last_30_demo_days"},
        )
        assert resp.status_code == 200
        assert "pack_id" in resp.json()

    async def test_list_packs_200(self, client):
        await client.post("/compliance/generate-pack", json={"window": "last_30_demo_days"})
        resp = await client.get("/compliance/packs")
        assert resp.status_code == 200
        body = resp.json()
        packs = body.get("packs", body) if isinstance(body, dict) else body
        assert isinstance(packs, list)

    async def test_get_pack_by_id_200(self, client):
        gen = await client.post("/compliance/generate-pack", json={"window": "last_30_demo_days"})
        pack_id = gen.json()["pack_id"]
        resp = await client.get(f"/compliance/packs/{pack_id}")
        assert resp.status_code == 200

    async def test_verify_pack_200(self, client):
        gen = await client.post("/compliance/generate-pack", json={"window": "last_30_demo_days"})
        pack_id = gen.json()["pack_id"]
        resp = await client.post(f"/compliance/packs/{pack_id}/verify")
        assert resp.status_code == 200


# =============================================================================
# Wave 47 — Judge Mode v2
# =============================================================================
class TestJudgeModeV2:
    def test_pack_definitions_nonempty(self):
        defs = get_pack_definitions()
        assert isinstance(defs, list)
        assert len(defs) >= 1

    def test_definitions_have_vendor(self):
        for d in get_pack_definitions():
            assert "vendor" in d

    def test_definitions_have_key_features(self):
        for d in get_pack_definitions():
            assert "key_features" in d

    def test_pack_defs_has_microsoft(self):
        assert "microsoft" in PACK_DEFS

    def test_generate_all_packs_returns_generation_id(self):
        result = generate_judge_pack_v2(target="all")
        assert isinstance(result, dict)
        assert "generation_id" in result

    def test_generate_all_packs_has_packs(self):
        result = generate_judge_pack_v2(target="all")
        assert "packs" in result
        assert isinstance(result["packs"], dict)

    def test_generate_specific_vendor(self):
        defs = get_pack_definitions()
        vendor = defs[0]["vendor"]
        result = generate_judge_pack_v2(target=vendor)
        assert isinstance(result, dict)
        assert "generation_id" in result

    def test_list_packs_after_generate(self):
        generate_judge_pack_v2(target="all")
        packs = list_judge_packs_v2()
        assert isinstance(packs, list)
        assert len(packs) >= 1

    def test_list_packs_have_pack_id(self):
        generate_judge_pack_v2(target="all")
        packs = list_judge_packs_v2()
        for p in packs:
            assert "pack_id" in p


class TestJudgeV2HTTP:
    async def test_post_generate_all_200(self, client):
        resp = await client.post("/judge/v2/generate", json={"target": "all"})
        assert resp.status_code == 200
        body = resp.json()
        assert "generation_id" in body

    async def test_list_packs_200(self, client):
        await client.post("/judge/v2/generate", json={"target": "all"})
        resp = await client.get("/judge/v2/packs")
        assert resp.status_code == 200
        body = resp.json()
        packs = body.get("packs", body) if isinstance(body, dict) else body
        assert isinstance(packs, list)

    async def test_get_definitions_200(self, client):
        resp = await client.get("/judge/v2/definitions")
        assert resp.status_code == 200
        body = resp.json()
        assert "definitions" in body

    async def test_get_pack_by_id_200(self, client):
        packs = list_judge_packs_v2()
        if packs:
            pack_id = packs[0]["pack_id"]
            resp = await client.get(f"/judge/v2/packs/{pack_id}")
            assert resp.status_code == 200
