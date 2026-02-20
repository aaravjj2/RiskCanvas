"""
test_stab_contract.py — Stabilization contract tests (v5.55.0)

Verifies real behavior across the 3 judge flows:
  - Flow A: Dataset ingest → list → get → sha256 determinism
  - Flow B: Scenario create → run → replay → output_hash determinism
  - Flow C: Review DRAFT → IN_REVIEW → APPROVED → decision_hash + attestation_id
  - Flow D: Decision packet generate → verify → manifest_hash determinism
  - Flow E: HealthResponse schema has v5.53.1 fields

No mocking. Tests exercise in-memory stores directly.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datasets import ingest_dataset, list_datasets, get_dataset, DATASET_STORE
from scenarios_v2 import (
    create_scenario, run_scenario, replay_scenario,
    get_scenario, get_scenario_runs, list_scenarios,
    SCENARIO_STORE,
)
from reviews import (
    create_review, submit_review, decide_review,
    get_review, list_reviews, REVIEW_STORE,
)
from decision_packet import (
    generate_decision_packet, list_packets, get_packet, verify_packet, PACKET_STORE,
)

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_stores():
    """Save stores snapshot, clear for test, restore after so seeds survive for other modules."""
    saved_ds = dict(DATASET_STORE)
    saved_sc = dict(SCENARIO_STORE)
    saved_rv = dict(REVIEW_STORE)
    saved_pk = dict(PACKET_STORE)
    DATASET_STORE.clear()
    SCENARIO_STORE.clear()
    REVIEW_STORE.clear()
    PACKET_STORE.clear()
    yield
    DATASET_STORE.clear()
    DATASET_STORE.update(saved_ds)
    SCENARIO_STORE.clear()
    SCENARIO_STORE.update(saved_sc)
    REVIEW_STORE.clear()
    REVIEW_STORE.update(saved_rv)
    PACKET_STORE.clear()
    PACKET_STORE.update(saved_pk)


DEMO_PAYLOAD = {
    "positions": [
        {"ticker": "AAPL", "quantity": 100, "cost_basis": 178.5},
        {"ticker": "MSFT", "quantity": 50,  "cost_basis": 415.0},
        {"ticker": "GOOGL","quantity": 25,  "cost_basis": 175.0},
    ]
}


def _ingest(payload=None, kind="portfolio", name="TestDS", tenant="t1"):
    """Call ingest_dataset; assert no errors; return dataset dict."""
    ds, errors = ingest_dataset(tenant, kind, name, payload or DEMO_PAYLOAD, "u@rc.io")
    assert not errors, f"Unexpected ingest errors: {errors}"
    return ds


def _scenario(name="TestScn", kind="stress", tenant="t1"):
    params = {"shock_pct": 0.20, "apply_to": ["equity"], "correlation_shift": 0.1}
    return create_scenario(tenant, name, kind, params, "u@rc.io")


def _review(tenant="t1", subj_type="dataset", subj_id="ds-001"):
    return create_review(tenant, subj_type, subj_id, "u@rc.io", notes="Contract test")


# ════════════════ FLOW A: DATASETS ════════════════════════════════════════════

class TestDatasetContracts:

    def test_ingest_returns_tuple(self):
        result = ingest_dataset("t1", "portfolio", "DS", DEMO_PAYLOAD, "u@rc.io")
        assert isinstance(result, tuple), "ingest_dataset must return (dataset, errors)"
        ds, errors = result
        assert isinstance(errors, list)

    def test_ingest_required_fields(self):
        ds = _ingest()
        assert ds["dataset_id"]
        assert ds["sha256"]
        assert len(ds["sha256"]) == 64, "sha256 must be 64-char hex"
        assert ds["row_count"] == 3
        assert ds["kind"] == "portfolio"

    def test_sha256_deterministic(self):
        ds1 = _ingest(name="Same")
        DATASET_STORE.clear()
        ds2 = _ingest(name="Same")
        assert ds1["sha256"] == ds2["sha256"], "Same payload must yield same sha256"

    def test_different_payloads_different_sha256(self):
        pa = {"positions": [{"ticker": "AAPL", "quantity": 1, "cost_basis": 1.0}]}
        pb = {"positions": [{"ticker": "MSFT", "quantity": 2, "cost_basis": 2.0}]}
        da = _ingest(payload=pa, name="A")
        DATASET_STORE.clear()
        db = _ingest(payload=pb, name="B")
        assert da["sha256"] != db["sha256"]

    def test_invalid_payload_returns_errors(self):
        _, errors = ingest_dataset("t1", "portfolio", "Bad", {"wrong_key": []}, "u")
        assert len(errors) > 0

    def test_list_datasets_contains_ingested(self):
        ds = _ingest(name="ListMe")
        rows = list_datasets("t1")
        assert any(r["name"] == "ListMe" for r in rows)

    def test_get_dataset_matches_ingest(self):
        ds = _ingest(name="GetMe")
        fetched = get_dataset(ds["dataset_id"])
        assert fetched["dataset_id"] == ds["dataset_id"]
        assert fetched["sha256"] == ds["sha256"]

    def test_row_count_reflects_positions_length(self):
        small = {"positions": [{"ticker": "X", "quantity": 1, "cost_basis": 1.0}]}
        ds = _ingest(payload=small, name="Small")
        assert ds["row_count"] == 1


# ════════════════ FLOW B: SCENARIOS ═══════════════════════════════════════════

class TestScenarioContracts:

    def test_create_required_fields(self):
        s = _scenario()
        assert s["scenario_id"]
        assert s["payload_hash"]
        assert len(s["payload_hash"]) == 64
        assert s["kind"] == "stress"
        assert s["name"] == "TestScn"

    def test_payload_hash_deterministic(self):
        s1 = _scenario(name="Det")
        SCENARIO_STORE.clear()
        s2 = _scenario(name="Det")
        assert s1["payload_hash"] == s2["payload_hash"]

    def test_run_returns_output_hash(self):
        s = _scenario()
        run = run_scenario(s["scenario_id"], "u@rc.io")
        assert run["run_id"]
        assert run["output_hash"]
        assert len(run["output_hash"]) == 64

    def test_replay_output_hash_equals_run(self):
        """Core determinism proof: replay == first run."""
        s = _scenario(name="RepDet")
        r1 = run_scenario(s["scenario_id"], "u@rc.io")
        r2 = replay_scenario(s["scenario_id"], "u@rc.io")
        assert r1["output_hash"] == r2["output_hash"], (
            f"output_hash mismatch: {r1['output_hash'][:16]}... != {r2['output_hash'][:16]}..."
        )

    def test_runs_accumulate(self):
        s = _scenario(name="Acc")
        run_scenario(s["scenario_id"], "u@rc.io")
        run_scenario(s["scenario_id"], "u@rc.io")
        assert len(get_scenario_runs(s["scenario_id"])) >= 2

    def test_list_contains_created(self):
        s = _scenario(name="ListMe")
        found = list_scenarios("t1")
        assert any(x["scenario_id"] == s["scenario_id"] for x in found)

    def test_get_by_id_matches(self):
        s = _scenario(name="GetMe")
        fetched = get_scenario(s["scenario_id"])
        assert fetched["payload_hash"] == s["payload_hash"]


# ════════════════ FLOW C: REVIEWS ═════════════════════════════════════════════

class TestReviewContracts:

    def test_create_draft(self):
        r = _review()
        assert r["review_id"]
        assert r["status"] == "DRAFT"
        assert r["subject_type"] == "dataset"
        assert r["subject_id"] == "ds-001"

    def test_submit_transitions_to_in_review(self):
        r = _review()
        s = submit_review(r["review_id"])
        assert s["status"] == "IN_REVIEW"

    def test_decide_approved_has_hash_and_attestation(self):
        r = _review()
        submit_review(r["review_id"])
        d = decide_review(r["review_id"], "APPROVED", "approver@rc.io")
        assert d["status"] == "APPROVED"
        assert d["decision_hash"], "decision_hash required"
        assert len(d["decision_hash"]) == 64
        assert d["attestation_id"], "attestation_id required"

    def test_decide_rejected_sets_status(self):
        r = _review(subj_id="ds-002")
        submit_review(r["review_id"])
        d = decide_review(r["review_id"], "REJECTED", "approver@rc.io")
        assert d["status"] == "REJECTED"

    def test_decision_hash_deterministic(self):
        r1 = create_review("t1", "dataset", "ds-det", "u@rc.io", notes="N")
        submit_review(r1["review_id"])
        d1 = decide_review(r1["review_id"], "APPROVED", "a@rc.io")
        REVIEW_STORE.clear()
        r2 = create_review("t1", "dataset", "ds-det", "u@rc.io", notes="N")
        submit_review(r2["review_id"])
        d2 = decide_review(r2["review_id"], "APPROVED", "a@rc.io")
        assert d1["decision_hash"] == d2["decision_hash"], "decision_hash must be deterministic"

    def test_full_state_machine(self):
        r = _review()
        assert get_review(r["review_id"])["status"] == "DRAFT"
        submit_review(r["review_id"])
        assert get_review(r["review_id"])["status"] == "IN_REVIEW"
        decide_review(r["review_id"], "APPROVED", "a@rc.io")
        assert get_review(r["review_id"])["status"] == "APPROVED"

    def test_list_contains_created(self):
        r = _review()
        assert any(x["review_id"] == r["review_id"] for x in list_reviews("t1"))

    def test_get_by_id_matches(self):
        r = _review()
        fetched = get_review(r["review_id"])
        assert fetched["status"] == "DRAFT"
        assert fetched["subject_id"] == "ds-001"


# ════════════════ FLOW D: DECISION PACKETS ════════════════════════════════════

class TestDecisionPacketContracts:

    def test_generate_required_fields(self):
        p = generate_decision_packet("t1", "dataset", "ds-001", "u@rc.io")
        assert p["packet_id"]
        assert p["manifest_hash"]
        assert len(p["manifest_hash"]) == 64
        assert p["subject_type"] == "dataset"
        assert p["subject_id"] == "ds-001"

    def test_manifest_hash_deterministic(self):
        p1 = generate_decision_packet("t1", "dataset", "ds-det", "u@rc.io")
        PACKET_STORE.clear()
        p2 = generate_decision_packet("t1", "dataset", "ds-det", "u@rc.io")
        assert p1["manifest_hash"] == p2["manifest_hash"]

    def test_verify_returns_true(self):
        p = generate_decision_packet("t1", "dataset", "ds-v", "u@rc.io")
        result = verify_packet(p["packet_id"])
        assert result["verified"] is True

    def test_list_contains_generated(self):
        p = generate_decision_packet("t1", "dataset", "ds-l", "u@rc.io")
        assert any(x["packet_id"] == p["packet_id"] for x in list_packets("t1"))

    def test_get_by_id(self):
        p = generate_decision_packet("t1", "dataset", "ds-g", "u@rc.io")
        fetched = get_packet(p["packet_id"])
        assert fetched["manifest_hash"] == p["manifest_hash"]

    def test_different_subjects_different_hash(self):
        p1 = generate_decision_packet("t1", "dataset", "ds-a", "u@rc.io")
        PACKET_STORE.clear()
        p2 = generate_decision_packet("t1", "dataset", "ds-b", "u@rc.io")
        assert p1["manifest_hash"] != p2["manifest_hash"]


# ════════════════ HEALTH SCHEMA ═══════════════════════════════════════════════

class TestHealthContract:

    def test_schema_has_v5531_fields(self):
        from schemas import HealthResponse
        r = HealthResponse(status="healthy", version="5.55.0")
        assert r.status == "healthy"
        assert r.version == "5.55.0"
        assert hasattr(r, "demo_mode"), "demo_mode added in v5.53.1"
        assert hasattr(r, "storage_backend"), "storage_backend added in v5.53.1"
        assert hasattr(r, "job_backend"), "job_backend added in v5.53.1"
        assert r.demo_mode is False
        assert r.storage_backend == "memory"
        assert r.job_backend == "sync"
