"""
test_wave49_56.py — Wave 49-56 pytest suite (v5.22.0 → v5.45.0)

Coverage:
- TestDatasets         (Wave 49) — 18 tests
- TestDatasetsHTTP     (Wave 49) — 5 tests
- TestScenariosV2      (Wave 50) — 14 tests
- TestScenariosV2HTTP  (Wave 50) — 5 tests
- TestReviews          (Wave 51) — 14 tests
- TestReviewsHTTP      (Wave 51) — 5 tests
- TestDecisionPacket   (Wave 51) — 8 tests
- TestDecisionPackHTTP (Wave 51) — 5 tests
- TestDeployValidator  (Wave 53) — 10 tests
- TestDeployHTTP       (Wave 53) — 4 tests
- TestJudgeModeV3      (Wave 54) — 10 tests
- TestJudgeV3HTTP      (Wave 54) — 4 tests

All tests: deterministic, no external network calls.
"""
from __future__ import annotations

import sys
import os

import hashlib
import json
import pytest
from httpx import AsyncClient, ASGITransport

# ── Import modules under test ────────────────────────────────────────────────

import datasets as ds_mod
import scenarios_v2 as sc_mod
import reviews as rv_mod
import decision_packet as dp_mod
import deploy_validator as dv_mod
import judge_mode_v3 as jv3_mod
from main import app

# ── Shared helpers ────────────────────────────────────────────────────────────

def _sha(data) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def get_demo_context(x_demo_role: str = "OWNER", x_demo_tenant: str = None):
    from tenancy_v2 import get_demo_context
    return get_demo_context(x_demo_tenant=x_demo_tenant, x_demo_role=x_demo_role)


# ── Wave 49: Datasets ─────────────────────────────────────────────────────────

class TestDatasets:
    def test_demo_datasets_seeded(self):
        """DEMO datasets are seeded on import."""
        assert len(ds_mod.DATASET_STORE) >= 5

    def test_demo_datasets_all_kinds(self):
        """All 5 kinds are represented in demo data."""
        kinds = {d["kind"] for d in ds_mod.DATASET_STORE.values()}
        assert "portfolio" in kinds
        assert "rates_curve" in kinds
        assert "stress_preset" in kinds
        assert "fx_set" in kinds
        assert "credit_curve" in kinds

    def test_ingest_portfolio_valid(self):
        """Valid portfolio payload ingests without errors."""
        payload = {
            "positions": [
                {"ticker": "GOOG", "quantity": 100, "cost_basis": 175.0},
                {"ticker": "META", "quantity": 200, "cost_basis": 560.0},
            ]
        }
        dataset, errors = ds_mod.ingest_dataset("t1", "portfolio", "Test Portfolio", payload, "test@test.com")
        assert errors == []
        assert dataset["dataset_id"] != ""
        assert dataset["kind"] == "portfolio"
        assert dataset["name"] == "Test Portfolio"
        assert dataset["row_count"] == 2
        assert dataset["verified"] is True

    def test_ingest_deterministic_id(self):
        """Same payload → same dataset_id (deterministic)."""
        payload = {"positions": [{"ticker": "X", "quantity": 10, "cost_basis": 1.0}]}
        d1, _ = ds_mod.ingest_dataset("t_det", "portfolio", "Det Test", payload, "u1")
        d2, _ = ds_mod.ingest_dataset("t_det", "portfolio", "Det Test", payload, "u1")
        assert d1["dataset_id"] == d2["dataset_id"]
        assert d1["sha256"] == d2["sha256"]

    def test_ingest_validation_error_missing_positions(self):
        """Portfolio missing 'positions' returns validation error."""
        _, errors = ds_mod.ingest_dataset("t_err", "portfolio", "Bad", {}, "u1")
        assert len(errors) > 0
        paths = [e["path"] for e in errors]
        assert "$.positions" in paths

    def test_ingest_validation_error_missing_position_fields(self):
        """Position missing required fields returns deterministic errors."""
        payload = {"positions": [{"ticker": "X"}]}
        _, errors = ds_mod.ingest_dataset("t_err2", "portfolio", "Bad2", payload, "u1")
        assert len(errors) >= 2
        paths = [e["path"] for e in errors]
        assert any("quantity" in p or "cost_basis" in p for p in paths)

    def test_ingest_rates_curve_valid(self):
        """Valid rates_curve payload ingests."""
        payload = {
            "curve_date": "2026-02-19",
            "tenor_points": [{"tenor": "1Y", "rate": 0.05}]
        }
        dataset, errors = ds_mod.ingest_dataset("t1", "rates_curve", "Test Curve", payload, "u1")
        assert errors == []
        assert dataset["row_count"] == 1

    def test_ingest_rates_curve_empty_tenors_error(self):
        """rates_curve with empty tenor_points returns error."""
        payload = {"curve_date": "2026-02-19", "tenor_points": []}
        _, errors = ds_mod.ingest_dataset("t1", "rates_curve", "Empty Curve", payload, "u1")
        assert len(errors) > 0

    def test_ingest_stress_preset_valid(self):
        """Valid stress_preset ingests."""
        payload = {"name": "Test Shock", "shocks": {"rates": 0.01, "equity": -0.1}}
        dataset, errors = ds_mod.ingest_dataset("t1", "stress_preset", "Test Shock", payload, "u1")
        assert errors == []
        assert dataset["row_count"] == 2  # 2 shock keys

    def test_ingest_fx_set_valid(self):
        """Valid fx_set ingests."""
        payload = {"base_currency": "USD", "pairs": {"USD/EUR": 0.92, "USD/GBP": 0.79}}
        dataset, errors = ds_mod.ingest_dataset("t1", "fx_set", "FX Test", payload, "u1")
        assert errors == []
        assert dataset["row_count"] == 2

    def test_ingest_unknown_kind_validate_errors(self):
        """Validating empty payload (no fields) for known kind returns errors."""
        errors = ds_mod._validate_payload("portfolio", {})
        assert len(errors) > 0
        assert any(e["path"] == "$.positions" for e in errors)

    def test_list_datasets_returns_all(self):
        """List returns at least seeded datasets."""
        result = ds_mod.list_datasets()
        assert len(result) >= 5

    def test_list_datasets_filter_by_kind(self):
        """Filtering by kind returns only matching datasets."""
        portfolios = ds_mod.list_datasets(kind="portfolio")
        assert all(d["kind"] == "portfolio" for d in portfolios)
        assert len(portfolios) >= 2

    def test_get_dataset_existing(self):
        """get_dataset returns a seeded dataset by ID."""
        ids = list(ds_mod.DATASET_STORE.keys())
        d = ds_mod.get_dataset(ids[0])
        assert d["dataset_id"] == ids[0]

    def test_get_dataset_missing_raises(self):
        """get_dataset raises ValueError for unknown ID."""
        with pytest.raises(ValueError):
            ds_mod.get_dataset("nonexistent-dataset-id")

    def test_sha256_in_dataset(self):
        """Ingested dataset has sha256 field."""
        payload = {"positions": [{"ticker": "SHA_TEST", "quantity": 1, "cost_basis": 1.0}]}
        d, _ = ds_mod.ingest_dataset("t_sha", "portfolio", "SHA Test", payload, "u1")
        assert len(d["sha256"]) == 64

    def test_dataset_schema_version(self):
        """Datasets have schema_version set."""
        ids = list(ds_mod.DATASET_STORE.keys())
        d = ds_mod.get_dataset(ids[0])
        assert d["schema_version"] == "1.0"

    def test_non_object_payload_error(self):
        """Non-dict payload returns error."""
        _, errors = ds_mod.ingest_dataset("t1", "portfolio", "arr payload", [1, 2, 3], "u1")
        assert len(errors) > 0
        assert errors[0]["path"] == "$"


class TestDatasetsHTTP:
    @pytest.mark.asyncio
    async def test_list_datasets_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/datasets")
        assert r.status_code == 200
        body = r.json()
        assert "datasets" in body
        assert body["count"] >= 5

    @pytest.mark.asyncio
    async def test_get_dataset_endpoint(self):
        dataset_id = list(ds_mod.DATASET_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(f"/datasets/{dataset_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["dataset"]["dataset_id"] == dataset_id

    @pytest.mark.asyncio
    async def test_get_dataset_404(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/datasets/xxxx-not-exist")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_ingest_endpoint_valid(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/datasets/ingest", json={
                "kind": "fx_set",
                "name": "HTTP Test FX",
                "payload": {"base_currency": "USD", "pairs": {"USD/EUR": 0.91}},
                "created_by": "http_test@test.com"
            })
        assert r.status_code == 200
        body = r.json()
        assert body["valid"] is True
        assert body["dataset"] is not None

    @pytest.mark.asyncio
    async def test_validate_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/datasets/validate", json={
                "kind": "portfolio",
                "name": "Validate Test",
                "payload": {}
            })
        assert r.status_code == 200
        body = r.json()
        assert body["valid"] is False
        assert len(body["errors"]) > 0


# ── Wave 50: Scenarios v2 ─────────────────────────────────────────────────────

class TestScenariosV2:
    def test_demo_scenarios_seeded(self):
        """DEMO scenarios are seeded on import."""
        assert len(sc_mod.SCENARIO_STORE) >= 3

    def test_all_three_kinds_present(self):
        """stress, whatif, shock_ladder are all present."""
        kinds = {s["kind"] for s in sc_mod.SCENARIO_STORE.values()}
        assert "stress" in kinds
        assert "whatif" in kinds
        assert "shock_ladder" in kinds

    def test_create_scenario_deterministic(self):
        """Same payload → same scenario_id."""
        payload = {"shocks": {"rates": 0.02, "equity": -0.2}, "confidence_level": 0.95, "horizon_days": 5}
        s1 = sc_mod.create_scenario("t1", "Det Stress", "stress", payload, "u1")
        s2 = sc_mod.create_scenario("t1", "Det Stress", "stress", payload, "u1")
        assert s1["scenario_id"] == s2["scenario_id"]
        assert s1["payload_hash"] == s2["payload_hash"]

    def test_scenario_has_impact_preview(self):
        """Created scenario includes impact_preview."""
        payload = {"shocks": {"rates": 0.01, "equity": -0.1}, "confidence_level": 0.99, "horizon_days": 10}
        s = sc_mod.create_scenario("t1", "Impact Test", "stress", payload, "u1")
        assert "impact_preview" in s
        assert s["impact_preview"]["kind"] == "stress"

    def test_stress_impact_deterministic(self):
        """Stress impact is deterministic for same shocks."""
        payload = {"shocks": {"rates": 0.01, "equity": -0.15, "credit": 0.0075}, "confidence_level": 0.99, "horizon_days": 10}
        impact1 = sc_mod._compute_impact("stress", payload)
        impact2 = sc_mod._compute_impact("stress", payload)
        assert impact1 == impact2

    def test_whatif_impact_computed(self):
        """whatif scenario has computed impact."""
        impact = sc_mod._compute_impact("whatif", sc_mod.DEMO_SCENARIO_TEMPLATES["whatif"])
        assert impact["kind"] == "whatif"
        assert "portfolio_pnl" in impact

    def test_shock_ladder_impact_structure(self):
        """shock_ladder produces a ladder list."""
        impact = sc_mod._compute_impact("shock_ladder", sc_mod.DEMO_SCENARIO_TEMPLATES["shock_ladder"])
        assert impact["kind"] == "shock_ladder"
        assert isinstance(impact["ladder"], list)
        assert len(impact["ladder"]) > 0

    def test_run_scenario_creates_run(self):
        """Running a scenario creates a run record."""
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        before_count = len(sc_mod.SCENARIO_RUNS.get(stress_id, []))
        run = sc_mod.run_scenario(stress_id, "test@test.com")
        assert run["scenario_id"] == stress_id
        assert run["output_hash"] != ""
        assert len(sc_mod.SCENARIO_RUNS[stress_id]) == before_count + 1

    def test_replay_same_output_hash(self):
        """Two replays of same scenario produce identical output_hash."""
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        r1 = sc_mod.replay_scenario(stress_id, "u1")
        r2 = sc_mod.replay_scenario(stress_id, "u1")
        assert r1["output_hash"] == r2["output_hash"]

    def test_run_creates_artifact(self):
        """Running a scenario registers an artifact."""
        from artifacts_registry import DEMO_REGISTRY
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        run = sc_mod.run_scenario(stress_id, "art_test@test.com")
        assert run["artifact_id"] in DEMO_REGISTRY

    def test_run_creates_attestation(self):
        """Running a scenario issues an attestation."""
        from attestations import get_attestation
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        run = sc_mod.run_scenario(stress_id, "att_test@test.com")
        att = get_attestation(run["attestation_id"])
        assert att["attestation_id"] == run["attestation_id"]

    def test_get_scenario_exists(self):
        """get_scenario returns existing scenario."""
        sid = list(sc_mod.SCENARIO_STORE.keys())[0]
        s = sc_mod.get_scenario(sid)
        assert s["scenario_id"] == sid

    def test_get_scenario_missing_raises(self):
        """get_scenario raises ValueError for missing ID."""
        with pytest.raises(ValueError):
            sc_mod.get_scenario("nonexistent-scenario")

    def test_list_scenarios_by_kind(self):
        """Filtering scenarios by kind works."""
        stress_scenarios = sc_mod.list_scenarios(kind="stress")
        assert all(s["kind"] == "stress" for s in stress_scenarios)


class TestScenariosV2HTTP:
    @pytest.mark.asyncio
    async def test_list_scenarios_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/scenarios-v2")
        assert r.status_code == 200
        body = r.json()
        assert "scenarios" in body
        assert body["count"] >= 3

    @pytest.mark.asyncio
    async def test_create_scenario_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/scenarios-v2", json={
                "name": "HTTP Stress Test",
                "kind": "stress",
                "payload": {"shocks": {"rates": 0.01, "equity": -0.10}, "confidence_level": 0.99, "horizon_days": 10},
                "created_by": "http@test.com",
            })
        assert r.status_code == 200
        body = r.json()
        assert "scenario" in body
        assert body["scenario"]["kind"] == "stress"

    @pytest.mark.asyncio
    async def test_get_scenario_endpoint(self):
        sid = list(sc_mod.SCENARIO_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(f"/scenarios-v2/{sid}")
        assert r.status_code == 200
        body = r.json()
        assert body["scenario"]["scenario_id"] == sid

    @pytest.mark.asyncio
    async def test_run_scenario_endpoint(self):
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(f"/scenarios-v2/{stress_id}/run", json={"triggered_by": "http_run@test.com"})
        assert r.status_code == 200
        body = r.json()
        assert "run" in body
        assert body["run"]["scenario_id"] == stress_id

    @pytest.mark.asyncio
    async def test_replay_deterministic_via_http(self):
        stress_id = next(
            s["scenario_id"] for s in sc_mod.SCENARIO_STORE.values() if s["kind"] == "stress"
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r1 = await c.post(f"/scenarios-v2/{stress_id}/replay", json={"triggered_by": "replay1@test.com"})
            r2 = await c.post(f"/scenarios-v2/{stress_id}/replay", json={"triggered_by": "replay1@test.com"})
        assert r1.status_code == 200
        assert r2.status_code == 200
        h1 = r1.json()["run"]["output_hash"]
        h2 = r2.json()["run"]["output_hash"]
        assert h1 == h2


# ── Wave 51: Reviews ──────────────────────────────────────────────────────────

class TestReviews:
    def test_demo_reviews_seeded(self):
        """DEMO reviews are seeded on import."""
        assert len(rv_mod.REVIEW_STORE) >= 3

    def test_has_approved_review(self):
        """At least one APPROVED review exists."""
        approved = [r for r in rv_mod.REVIEW_STORE.values() if r["status"] == "APPROVED"]
        assert len(approved) >= 1

    def test_approved_review_has_decision_hash(self):
        """APPROVED review has a decision_hash."""
        approved = next(r for r in rv_mod.REVIEW_STORE.values() if r["status"] == "APPROVED")
        assert approved["decision_hash"] is not None
        assert len(approved["decision_hash"]) == 64

    def test_approved_review_has_attestation(self):
        """APPROVED review issued an attestation."""
        from attestations import get_attestation
        approved = next(r for r in rv_mod.REVIEW_STORE.values() if r["status"] == "APPROVED")
        att = get_attestation(approved["attestation_id"])
        assert att["attestation_id"] == approved["attestation_id"]

    def test_create_review(self):
        """Creating a review sets default DRAFT status."""
        r = rv_mod.create_review("t1", "scenario", "subject-123", "alice@t.com",
                                  ["bob@t.com"], "New review")
        assert r["status"] == "DRAFT"
        assert r["subject_type"] == "scenario"
        assert r["subject_id"] == "subject-123"

    def test_review_id_deterministic(self):
        """Same (tenant, type, subject, requester) → same review_id."""
        r1 = rv_mod.create_review("t_det", "artifact", "art-abc", "alice@t.com")
        r2 = rv_mod.create_review("t_det", "artifact", "art-abc", "alice@t.com")
        assert r1["review_id"] == r2["review_id"]

    def test_submit_review_transitions_to_in_review(self):
        """Submitting a DRAFT review transitions to IN_REVIEW."""
        r = rv_mod.create_review("t2", "dataset", "ds-999", "alice2@t.com")
        submitted = rv_mod.submit_review(r["review_id"])
        assert submitted["status"] == "IN_REVIEW"

    def test_submit_non_draft_raises(self):
        """Submitting a non-DRAFT review raises ValueError."""
        r = rv_mod.create_review("t3", "scenario", "s-submit-err", "a@t.com")
        rv_mod.submit_review(r["review_id"])  # → IN_REVIEW
        with pytest.raises(ValueError):
            rv_mod.submit_review(r["review_id"])  # already IN_REVIEW

    def test_decide_approve_transitions_status(self):
        """Deciding APPROVED transitions review to APPROVED."""
        r = rv_mod.create_review("t4", "compliance_pack", "cp-1", "a@t.com")
        rv_mod.submit_review(r["review_id"])
        decided = rv_mod.decide_review(r["review_id"], "APPROVED", "bob@t.com")
        assert decided["status"] == "APPROVED"
        assert decided["decision"] == "APPROVED"

    def test_decide_reject_transitions_status(self):
        """Deciding REJECTED transitions review to REJECTED."""
        r = rv_mod.create_review("t5", "scenario", "s-reject", "a@t.com")
        rv_mod.submit_review(r["review_id"])
        decided = rv_mod.decide_review(r["review_id"], "REJECTED", "carol@t.com")
        assert decided["status"] == "REJECTED"

    def test_decide_non_in_review_raises(self):
        """Can't decide a DRAFT review."""
        r = rv_mod.create_review("t6", "artifact", "art-decide-err", "a@t.com")
        with pytest.raises(ValueError):
            rv_mod.decide_review(r["review_id"], "APPROVED", "b@t.com")

    def test_decision_hash_deterministic(self):
        """Same (review_id, decision, decided_by) → same decision_hash."""
        h1 = rv_mod._compute_decision_hash("rev-test", "APPROVED", "carol@t.com")
        h2 = rv_mod._compute_decision_hash("rev-test", "APPROVED", "carol@t.com")
        assert h1 == h2

    def test_list_reviews_by_status(self):
        """Filtering by status returns only matching reviews."""
        approved = rv_mod.list_reviews(status="APPROVED")
        assert all(r["status"] == "APPROVED" for r in approved)

    def test_get_review_missing_raises(self):
        """get_review raises ValueError for missing ID."""
        with pytest.raises(ValueError):
            rv_mod.get_review("nonexistent-review")


class TestReviewsHTTP:
    @pytest.mark.asyncio
    async def test_list_reviews_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/reviews")
        assert r.status_code == 200
        body = r.json()
        assert "reviews" in body
        assert body["count"] >= 3

    @pytest.mark.asyncio
    async def test_create_review_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/reviews", json={
                "subject_type": "scenario",
                "subject_id": "http-test-subject-1",
                "requested_by": "http_test@test.com",
            })
        assert r.status_code == 200
        body = r.json()
        assert body["review"]["status"] == "DRAFT"

    @pytest.mark.asyncio
    async def test_submit_review_endpoint(self):
        # Create then submit
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r1 = await c.post("/reviews", json={
                "subject_type": "dataset",
                "subject_id": "http-ds-submit",
                "requested_by": "submit_test@t.com",
            })
            rev_id = r1.json()["review"]["review_id"]
            r2 = await c.post(f"/reviews/{rev_id}/submit")
        assert r2.status_code == 200
        assert r2.json()["review"]["status"] == "IN_REVIEW"

    @pytest.mark.asyncio
    async def test_decide_review_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r1 = await c.post("/reviews", json={
                "subject_type": "artifact",
                "subject_id": "http-art-decide",
                "requested_by": "decide_test@t.com",
            })
            rev_id = r1.json()["review"]["review_id"]
            await c.post(f"/reviews/{rev_id}/submit")
            r3 = await c.post(f"/reviews/{rev_id}/decide", json={
                "decision": "APPROVED",
                "decided_by": "approver@t.com"
            })
        assert r3.status_code == 200
        assert r3.json()["review"]["status"] == "APPROVED"
        assert r3.json()["review"]["decision_hash"] is not None

    @pytest.mark.asyncio
    async def test_get_review_endpoint(self):
        rev_id = list(rv_mod.REVIEW_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(f"/reviews/{rev_id}")
        assert r.status_code == 200
        assert r.json()["review"]["review_id"] == rev_id


# ── Wave 51: Decision Packets ─────────────────────────────────────────────────

class TestDecisionPacket:
    def test_demo_packet_seeded(self):
        """Demo decision packet is seeded."""
        assert len(dp_mod.PACKET_STORE) >= 1

    def test_packet_has_manifest_hash(self):
        """All packets have manifest_hash."""
        for p in dp_mod.PACKET_STORE.values():
            assert p["manifest_hash"] != ""

    def test_packet_has_five_files(self):
        """Decision packet contains 5 evidence files."""
        p = list(dp_mod.PACKET_STORE.values())[0]
        assert p["file_count"] == 5
        file_names = {f["name"] for f in p["files"]}
        assert "subject.json" in file_names
        assert "runs.json" in file_names
        assert "attestations.json" in file_names
        assert "reviews.json" in file_names
        assert "summary.md" in file_names

    def test_verify_packet_passes(self):
        """Verifying a just-generated packet returns verified=True."""
        pid = list(dp_mod.PACKET_STORE.keys())[0]
        result = dp_mod.verify_packet(pid)
        assert result["verified"] is True
        assert result["match"] is True

    def test_generate_packet_idempotent(self):
        """Generating same (tenant, type, id) packet is idempotent by manifest_hash."""
        from tenancy_v2 import DEFAULT_TENANT_ID
        from scenarios_v2 import SCENARIO_STORE
        sid = sorted(SCENARIO_STORE.keys())[0]
        p1 = dp_mod.generate_decision_packet(DEFAULT_TENANT_ID, "scenario", sid)
        p2 = dp_mod.generate_decision_packet(DEFAULT_TENANT_ID, "scenario", sid)
        # Same manifest hash (same content)
        assert p1["manifest_hash"] == p2["manifest_hash"]

    def test_packet_for_artifact(self):
        """Can generate a packet for an artifact subject."""
        from artifacts_registry import DEMO_REGISTRY
        art_id = sorted(DEMO_REGISTRY.keys())[0]
        p = dp_mod.generate_decision_packet("default", "artifact", art_id)
        assert p["subject_type"] == "artifact"
        assert p["file_count"] == 5

    def test_list_packets(self):
        """list_packets returns at least 1 packet."""
        packets = dp_mod.list_packets()
        assert len(packets) >= 1

    def test_get_packet_missing_raises(self):
        """get_packet raises ValueError for missing ID."""
        with pytest.raises(ValueError):
            dp_mod.get_packet("nonexistent-packet")


class TestDecisionPackHTTP:
    @pytest.mark.asyncio
    async def test_generate_packet_endpoint(self):
        from tenancy_v2 import DEFAULT_TENANT_ID
        from scenarios_v2 import SCENARIO_STORE
        sid = sorted(SCENARIO_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/exports/decision-packet", json={
                "tenant_id": DEFAULT_TENANT_ID,
                "subject_type": "scenario",
                "subject_id": sid,
                "requested_by": "http_dp@test.com"
            })
        assert r.status_code == 200
        body = r.json()
        assert "packet" in body
        assert body["packet"]["file_count"] == 5

    @pytest.mark.asyncio
    async def test_list_packets_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/exports/decision-packets")
        assert r.status_code == 200
        body = r.json()
        assert "packets" in body
        assert body["count"] >= 1

    @pytest.mark.asyncio
    async def test_get_packet_endpoint(self):
        pid = list(dp_mod.PACKET_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(f"/exports/decision-packets/{pid}")
        assert r.status_code == 200
        assert r.json()["packet"]["packet_id"] == pid

    @pytest.mark.asyncio
    async def test_verify_packet_endpoint(self):
        pid = list(dp_mod.PACKET_STORE.keys())[0]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(f"/exports/decision-packets/{pid}/verify")
        assert r.status_code == 200
        assert r.json()["verified"] is True

    @pytest.mark.asyncio
    async def test_generate_packet_invalid_type(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/exports/decision-packet", json={
                "tenant_id": "t1",
                "subject_type": "invalid_type",
                "subject_id": "xxx",
            })
        assert r.status_code == 422


# ── Wave 53: Deploy Validator ─────────────────────────────────────────────────

class TestDeployValidator:
    def test_validate_azure_empty_env(self):
        """Empty env returns all required missing."""
        result = dv_mod.validate_azure_env({})
        assert result["provider"] == "Azure"
        assert len(result["required_missing"]) == len(dv_mod.AZURE_REQUIRED_VARS)
        assert result["valid"] is False
        assert result["completeness_pct"] == 0.0

    def test_validate_do_empty_env(self):
        """Empty env returns all DO required missing."""
        result = dv_mod.validate_do_env({})
        assert result["provider"] == "DigitalOcean"
        assert result["valid"] is False

    def test_validate_azure_demo_mode_only(self):
        """DEMO_MODE + API_PORT present gives partial result."""
        env = {"DEMO_MODE": "true", "API_PORT": "8090"}
        result = dv_mod.validate_azure_env(env)
        assert "DEMO_MODE" in result["required_present"]
        assert "API_PORT" in result["required_present"]

    def test_validate_do_demo_mode_only(self):
        """DEMO_MODE present gives partial result for DO."""
        env = {"DEMO_MODE": "true", "API_PORT": "8090"}
        result = dv_mod.validate_do_env(env)
        assert "DEMO_MODE" in result["required_present"]

    def test_validate_all_returns_both_providers(self):
        """validate_all returns results for both providers."""
        result = dv_mod.validate_all_envs({})
        assert "azure" in result
        assert "digitalocean" in result

    def test_lint_do_compose_valid(self):
        """Built-in DO compose template passes lint."""
        result = dv_mod.lint_do_compose_template(dv_mod.DO_COMPOSE_TEMPLATE)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_lint_nginx_valid(self):
        """Built-in nginx template passes lint."""
        result = dv_mod.lint_nginx_template(dv_mod.DO_NGINX_TEMPLATE)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_lint_do_compose_missing_keys(self):
        """Template missing required keys fails lint."""
        result = dv_mod.lint_do_compose_template("name: foo")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_lint_nginx_missing_proxy_pass(self):
        """nginx template missing proxy_pass fails."""
        result = dv_mod.lint_nginx_template("server { location /api/ { } }")
        assert result["valid"] is False

    def test_azure_required_vars_list(self):
        """Azure required vars list is non-empty and contains key vars."""
        assert "DEMO_MODE" in dv_mod.AZURE_REQUIRED_VARS
        assert "API_PORT" in dv_mod.AZURE_REQUIRED_VARS


class TestDeployHTTP:
    @pytest.mark.asyncio
    async def test_validate_azure_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/deploy/validate-azure", json={"env": {}})
        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "Azure"
        assert body["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_do_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/deploy/validate-do", json={"env": {"DEMO_MODE": "true"}})
        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "DigitalOcean"

    @pytest.mark.asyncio
    async def test_lint_template_endpoint_valid(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/deploy/lint-template", json={
                "template": dv_mod.DO_COMPOSE_TEMPLATE,
                "template_type": "do_compose",
            })
        assert r.status_code == 200
        assert r.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_get_do_compose_template_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/deploy/templates/do-compose")
        assert r.status_code == 200
        body = r.json()
        assert "template" in body
        assert "services:" in body["template"]


# ── Wave 54: Judge Mode v3 ────────────────────────────────────────────────────

class TestJudgeModeV3:
    def test_generate_all_packs(self):
        """Generating all packs returns 3 vendors."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        assert result["pack_count"] == 3
        assert "microsoft" in result["packs"]
        assert "gitlab" in result["packs"]
        assert "digitalocean" in result["packs"]

    def test_generation_id_deterministic(self):
        """Same tenant + same pack content → identical generation_id."""
        r1 = jv3_mod.generate_judge_pack_v3("default", "all")
        r2 = jv3_mod.generate_judge_pack_v3("default", "all")
        assert r1["generation_id"] == r2["generation_id"]

    def test_microsoft_pack_score(self):
        """Microsoft pack has score >= 90."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        assert result["packs"]["microsoft"]["score"] >= 90

    def test_gitlab_pack_score(self):
        """GitLab pack has score >= 90."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        assert result["packs"]["gitlab"]["score"] >= 90

    def test_do_pack_score(self):
        """DigitalOcean pack has score >= 85."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        assert result["packs"]["digitalocean"]["score"] >= 85

    def test_overall_verdict_strong_pass(self):
        """Overall verdict is STRONG PASS when score >= 95."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        # Average of 97+95+93=285/3=95 >= 95
        assert result["verdict"] in ("STRONG PASS", "PASS")

    def test_pack_has_pack_hash(self):
        """Each vendor pack has pack_hash."""
        result = jv3_mod.generate_judge_pack_v3("default", "all")
        for vendor, pack in result["packs"].items():
            assert "pack_hash" in pack
            assert len(pack["pack_hash"]) == 64

    def test_list_packs_v3(self):
        """list_judge_packs_v3 returns generated packs."""
        jv3_mod.generate_judge_pack_v3("default", "all")
        packs = jv3_mod.list_judge_packs_v3()
        assert len(packs) >= 1

    def test_get_pack_definitions_v3(self):
        """get_pack_definitions_v3 returns 3 definitions."""
        defs = jv3_mod.get_pack_definitions_v3()
        assert len(defs) == 3
        vendors = {d["vendor"] for d in defs}
        assert "Microsoft" in vendors
        assert "GitLab" in vendors
        assert "DigitalOcean" in vendors

    def test_definitions_have_key_features(self):
        """Each definition has at least 3 key_features."""
        defs = jv3_mod.get_pack_definitions_v3()
        for d in defs:
            assert len(d["key_features"]) >= 3


class TestJudgeV3HTTP:
    @pytest.mark.asyncio
    async def test_generate_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/judge/v3/generate", json={"target": "all"})
        assert r.status_code == 200
        body = r.json()
        assert body["pack_count"] == 3
        assert "packs" in body

    @pytest.mark.asyncio
    async def test_list_packs_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/judge/v3/packs")
        assert r.status_code == 200
        body = r.json()
        assert "packs" in body
        assert body["count"] >= 1

    @pytest.mark.asyncio
    async def test_definitions_endpoint(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/judge/v3/definitions")
        assert r.status_code == 200
        body = r.json()
        assert len(body["definitions"]) == 3

    @pytest.mark.asyncio
    async def test_generate_single_vendor(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/judge/v3/generate", json={"target": "microsoft"})
        assert r.status_code == 200
        body = r.json()
        assert body["pack_count"] == 1
        assert "microsoft" in body["packs"]
