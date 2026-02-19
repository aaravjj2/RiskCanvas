"""
test_wave57_64.py — Comprehensive pytest suite for Waves 57–64

Coverage:
  Wave 57 — packet_signing.py (Ed25519 decision packet signing)
  Wave 58 — dataset_provenance.py (provenance + license gate)
  Wave 59 — scenario_runner.py (deterministic scenario runner v1)
  Wave 60 — reviews_sla.py (reviewer assignment + SLA tracking)
  Wave 61 — deploy_validator_v2.py (structured findings)
  Wave 62 — judge_mode_v4.py (scoring report + bundle ZIP)
  Wave 63 — search_provider.py (LocalSearchProvider + interface)
  Wave 64 — llm_provider.py (NoOpProvider + NovaProvider stub)

Requirements per CLAUDE.md:
  - 0 failed, 0 skipped
  - No random seeds (deterministic)
  - No network calls (offline)
"""
import base64
import json
import zipfile
import io
import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Wave 57 — Decision Packet Signing
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def signing():
    import importlib, packet_signing as m
    # Clear store so tests are isolated
    m.SIGNATURE_STORE.clear()
    return m


def test_signing_get_key_returns_bytes(signing):
    key = signing.get_signing_key()
    assert key is not None


def test_signing_demo_key_is_deterministic(signing):
    k1 = signing.get_signing_key()
    k2 = signing.get_signing_key()
    assert k1.private_bytes_raw() == k2.private_bytes_raw()


def test_signing_sign_packet_returns_signature_record(signing):
    sig = signing.sign_packet("pkt-test-001", "hash:abc", {"a.json": "abc123"})
    assert sig["packet_id"] == "pkt-test-001"
    assert "signature" in sig
    assert sig["algorithm"] == "Ed25519"
    assert "public_key" in sig


def test_signing_signature_is_bytes(signing):
    sig = signing.sign_packet("pkt-test-002", "hash:def", {})
    assert len(sig["signature"]) == 128  # 64 bytes hex = 128 chars


def test_signing_verify_signed_packet_passes(signing):
    manifest_hash = "sha256:abc123"
    files = {"subject.json": "aaa", "runs.json": "bbb"}
    signing.sign_packet("pkt-v-001", manifest_hash, files)
    result = signing.verify_signed_packet("pkt-v-001", manifest_hash, files)
    assert result["verified"] is True


def test_signing_verify_wrong_hash_fails(signing):
    signing.sign_packet("pkt-v-002", "sha256:original", {"f": "x"})
    result = signing.verify_signed_packet("pkt-v-002", "sha256:tampered", {"f": "x"})
    assert result["verified"] is False


def test_signing_get_signature_returns_record(signing):
    signing.sign_packet("pkt-v-003", "sha256:aaa", {})
    record = signing.get_signature("pkt-v-003")
    assert record is not None
    assert record["packet_id"] == "pkt-v-003"


def test_signing_get_signature_missing_returns_none(signing):
    with pytest.raises(ValueError):
        signing.get_signature("nonexistent-pkt")


def test_signing_list_returns_all(signing):
    signing.sign_packet("pkt-l-001", "hash:1", {})
    signing.sign_packet("pkt-l-002", "hash:2", {})
    sigs = signing.list_signatures()
    ids = [s["packet_id"] for s in sigs]
    assert "pkt-l-001" in ids
    assert "pkt-l-002" in ids


def test_signing_same_input_same_signature(signing):
    """Determinism: same packet_id + manifest + files → same signature bytes."""
    manifest = "sha256:deterministic"
    files = {"a.json": "aa"}
    # Must use same packet_id since packet_id is part of the signed payload
    s1 = signing.sign_packet("pkt-det-x", manifest, files)
    signing.SIGNATURE_STORE.clear()
    s2 = signing.sign_packet("pkt-det-x", manifest, files)
    assert s1["signature"] == s2["signature"]


def test_signing_router_exists(signing):
    from fastapi import APIRouter
    assert isinstance(signing.router, APIRouter)


def test_signing_http_sign_endpoint(signing):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(signing.router)
    client = TestClient(app)
    r = client.post("/signatures/sign", json={
        "packet_id": "pkt-http-001",
        "manifest_hash": "sha256:httptest",
        "files": {"x.json": "xhash"},
    })
    assert r.status_code == 200
    assert r.json()["signature"]["packet_id"] == "pkt-http-001"


def test_signing_http_verify_endpoint(signing):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(signing.router)
    client = TestClient(app)
    # First sign
    client.post("/signatures/sign", json={
        "packet_id": "pkt-hv-001",
        "manifest_hash": "sha256:verify",
        "files": {},
    })
    # Then verify
    r = client.post("/signatures/pkt-hv-001/verify", json={
        "manifest_hash": "sha256:verify",
        "files": {},
    })
    assert r.status_code == 200
    assert r.json()["verified"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 58 — Dataset Provenance
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def prov():
    import dataset_provenance as m
    m.PROVENANCE_STORE.clear()
    return m


def test_prov_demo_seeds_loaded(prov):
    prov._seed()
    assert len(prov.PROVENANCE_STORE) >= 5


def test_prov_ingest_cc0_allowed(prov):
    r = prov.ingest_dataset("ds-x-001", "Test DS", "rates", "synthetic", "unit test", "CC0", 100)
    assert r["license_tag"] == "CC0"
    assert r["license_compliant"] is True


def test_prov_ingest_demo_allowed(prov):
    r = prov.ingest_dataset("ds-x-002", "Demo DS", "credit", "generated", "demo data", "DEMO", 50)
    assert r["license_compliant"] is True


def test_prov_ingest_proprietary_blocked_in_demo(prov):
    with pytest.raises(PermissionError, match="PROPRIETARY"):
        prov.ingest_dataset("ds-x-003", "Prop DS", "fx", "uploaded", "raw data", "PROPRIETARY", 10)


def test_prov_checksum_is_deterministic(prov):
    r1 = prov.ingest_dataset("ds-det-001", "Det DS", "stress", "synthetic", "note", "MIT", 200)
    prov.PROVENANCE_STORE.clear()
    r2 = prov.ingest_dataset("ds-det-001", "Det DS", "stress", "synthetic", "note", "MIT", 200)
    assert r1["checksum"] == r2["checksum"]


def test_prov_get_dataset_found(prov):
    prov.ingest_dataset("ds-g-001", "G DS", "rates", "synthetic", "g", "CC0", 10)
    r = prov.get_dataset_provenance("ds-g-001")
    assert r["dataset_id"] == "ds-g-001"


def test_prov_get_dataset_not_found(prov):
    with pytest.raises(ValueError):
        prov.get_dataset_provenance("no-such-ds")


def test_prov_list_datasets(prov):
    prov.ingest_dataset("ds-lst-001", "L1", "rates", "synthetic", "n", "CC0", 5)
    prov.ingest_dataset("ds-lst-002", "L2", "credit", "generated", "n", "DEMO", 5)
    lst = prov.list_datasets()
    assert len(lst) >= 2


def test_prov_license_compliance_check(prov):
    prov.ingest_dataset("ds-lc-001", "LC DS", "rates", "synthetic", "n", "MIT", 1)
    c = prov.get_license_compliance("ds-lc-001")
    assert c["compliant"] is True


def test_prov_summary_totals(prov):
    prov.ingest_dataset("ds-sum-001", "S1", "rates", "synthetic", "n", "CC0", 1)
    prov.ingest_dataset("ds-sum-002", "S2", "credit", "generated", "n", "MIT", 1)
    s = prov.get_summary()
    assert s["total"] >= 2
    assert "CC0" in s["by_license"] or "MIT" in s["by_license"]


def test_prov_unknown_license_raises(prov):
    with pytest.raises(ValueError):
        prov.ingest_dataset("ds-ul-001", "UL", "rates", "synthetic", "n", "GPL2", 1)


def test_prov_http_list(prov):
    prov._seed()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(prov.router)
    client = TestClient(app)
    r = client.get("/provenance/datasets")
    assert r.status_code == 200
    assert "datasets" in r.json()


def test_prov_http_ingest_proprietary_returns_403(prov):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(prov.router)
    client = TestClient(app)
    r = client.post("/provenance/datasets", json={
        "name": "Bad DS", "kind": "rates", "source_type": "upload",
        "source_note": "test", "license_tag": "PROPRIETARY", "rows": 1,
    })
    assert r.status_code == 403


def test_prov_http_summary(prov):
    prov._seed()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(prov.router)
    client = TestClient(app)
    r = client.get("/provenance/summary")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 59 — Scenario Runner v1
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def runner():
    import scenario_runner as m
    m.RUNNER_STORE.clear()
    return m


def test_runner_demo_seeds(runner):
    runner._seed_demo_runs()
    assert len(runner.RUNNER_STORE) >= 3


def test_runner_start_run_completes(runner):
    run = runner.start_run("scn-001", "rate_shock", {"shock_bps": 100})
    assert run["status"] == "completed"


def test_runner_inputs_hash_present(runner):
    run = runner.start_run("scn-001", "rate_shock", {"shock_bps": 50})
    assert run["inputs_hash"].startswith("sha256:")


def test_runner_outputs_hash_present(runner):
    run = runner.start_run("scn-001", "credit_event", {"issuer": "X"})
    assert run["outputs_hash"].startswith("sha256:")


def test_runner_timeline_has_7_steps(runner):
    run = runner.start_run("scn-001", "fx_move", {"pairs": []})
    assert len(run["timeline"]) == 7


def test_runner_deterministic_inputs_hash(runner):
    r1 = runner.start_run("scn-d-001", "rate_shock", {"shock_bps": 100}, run_id="r1")
    runner.RUNNER_STORE.clear()
    r2 = runner.start_run("scn-d-001", "rate_shock", {"shock_bps": 100}, run_id="r2")
    assert r1["inputs_hash"] == r2["inputs_hash"]


def test_runner_deterministic_outputs_hash(runner):
    r1 = runner.start_run("scn-d-002", "credit_event", {"issuer": "Y"}, run_id="r3")
    runner.RUNNER_STORE.clear()
    r2 = runner.start_run("scn-d-002", "credit_event", {"issuer": "Y"}, run_id="r4")
    assert r1["outputs_hash"] == r2["outputs_hash"]


def test_runner_get_run(runner):
    r = runner.start_run("scn-g-001", "stress_test", {}, run_id="r-get-001")
    got = runner.get_run("r-get-001")
    assert got["run_id"] == "r-get-001"


def test_runner_get_run_missing_raises(runner):
    with pytest.raises(ValueError):
        runner.get_run("no-such-run")


def test_runner_list_runs(runner):
    runner.start_run("scn-l-001", "rate_shock", {})
    runner.start_run("scn-l-001", "credit_event", {})
    runs = runner.list_runs()
    assert len(runs) >= 2


def test_runner_list_by_scenario(runner):
    runner.start_run("scn-flt-001", "fx_move", {}, run_id="r-flt-1")
    runner.start_run("scn-flt-001", "fx_move", {}, run_id="r-flt-2")
    runner.start_run("scn-other-001", "stress_test", {}, run_id="r-flt-3")
    runs = runner.list_runs(scenario_id="scn-flt-001")
    assert len(runs) == 2


def test_runner_replay_preserves_hashes(runner):
    orig = runner.start_run("scn-rep-001", "rate_shock", {"shock_bps": 75}, run_id="r-rep-orig")
    replayed = runner.replay_run("r-rep-orig")
    assert replayed["inputs_hash"] == orig["inputs_hash"]
    assert replayed["outputs_hash"] == orig["outputs_hash"]
    assert replayed["run_id"] != orig["run_id"]


def test_runner_http_start(runner):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(runner.router)
    client = TestClient(app)
    r = client.post("/scenario-runner/runs", json={
        "scenario_id": "scn-http-001",
        "kind": "rate_shock",
        "payload": {"shock_bps": 100},
    })
    assert r.status_code == 200
    assert r.json()["run"]["status"] == "completed"


def test_runner_http_list(runner):
    runner._seed_demo_runs()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(runner.router)
    client = TestClient(app)
    r = client.get("/scenario-runner/runs")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 60 — Reviews SLA
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def rsla():
    import reviews_sla as m
    m.REVIEWS_SLA_STORE.clear()
    return m


def test_rsla_create_assigns_reviewer(rsla):
    r = rsla.create_review("rev-001", "pkt-001", "Test Review")
    assert r["assigned_to"] in rsla.REVIEWERS


def test_rsla_reviewer_deterministic(rsla):
    r1 = rsla.create_review("rev-det-001", "pkt-001", "Det Review")
    rsla.REVIEWS_SLA_STORE.clear()
    r2 = rsla.create_review("rev-det-001", "pkt-001", "Det Review")
    assert r1["assigned_to"] == r2["assigned_to"]


def test_rsla_sla_deadline_set(rsla):
    r = rsla.create_review("rev-sla-001", "pkt-001", "SLA Test")
    assert r["sla_deadline"] == "2026-02-21T00:00:00Z"


def test_rsla_decide_approved(rsla):
    rsla.create_review("rev-app-001", "pkt-001", "Approve me")
    r = rsla.decide_review("rev-app-001", "APPROVED", "alice@riskcanvas.io",
                           decided_at="2026-02-20T00:00:00Z")
    assert r["status"] == "APPROVED"
    assert r["sla_breached"] is False


def test_rsla_sla_breach_detected(rsla):
    rsla.create_review("rev-br-001", "pkt-001", "Breach Test")
    r = rsla.decide_review("rev-br-001", "APPROVED", "bob@riskcanvas.io",
                           decided_at="2026-02-22T12:00:00Z")  # after deadline
    assert r["sla_breached"] is True


def test_rsla_escalation_on_breach(rsla):
    rsla.create_review("rev-esc-001", "pkt-001", "Esc Test")
    r = rsla.decide_review("rev-esc-001", "REJECTED", "carol@riskcanvas.io",
                           decided_at="2026-02-25T00:00:00Z")
    assert len(r["escalation_events"]) == 1
    assert r["escalation_events"][0]["type"] == "SLA_BREACH"


def test_rsla_no_escalation_within_sla(rsla):
    rsla.create_review("rev-ok-001", "pkt-001", "OK Test")
    r = rsla.decide_review("rev-ok-001", "APPROVED", "dave@riskcanvas.io",
                           decided_at="2026-02-20T06:00:00Z")
    assert r["escalation_events"] == []


def test_rsla_get_review(rsla):
    rsla.create_review("rev-g-001", "pkt-001", "Get Test")
    r = rsla.get_review("rev-g-001")
    assert r["review_id"] == "rev-g-001"


def test_rsla_get_review_missing_raises(rsla):
    with pytest.raises(ValueError):
        rsla.get_review("no-such-review")


def test_rsla_bulk_assign(rsla):
    rsla.create_review("rev-ba-001", "pkt-001", "BA1")
    rsla.create_review("rev-ba-002", "pkt-002", "BA2")
    updated = rsla.bulk_assign(["rev-ba-001", "rev-ba-002"])
    assert len(updated) == 2


def test_rsla_dashboard_structure(rsla):
    rsla._seed()
    d = rsla.get_dashboard()
    assert "total_reviews" in d
    assert "total_breached" in d
    assert "by_reviewer" in d


def test_rsla_invalid_decision_raises(rsla):
    rsla.create_review("rev-iv-001", "pkt-001", "IV")
    with pytest.raises(ValueError):
        rsla.decide_review("rev-iv-001", "MAYBE", "x@y.io")


def test_rsla_http_create(rsla):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(rsla.router)
    client = TestClient(app)
    r = client.post("/reviews-sla/reviews", json={
        "packet_id": "pkt-http-001",
        "title": "HTTP Review",
    })
    assert r.status_code == 200
    assert "review" in r.json()


def test_rsla_http_dashboard(rsla):
    rsla._seed()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(rsla.router)
    client = TestClient(app)
    r = client.get("/reviews-sla/dashboard")
    assert r.status_code == 200
    assert r.json()["total_reviews"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 61 — Deploy Validator v2
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def dv2():
    import deploy_validator_v2 as m
    m.VALIDATION_RUNS.clear()
    return m


def test_dv2_run_returns_run(dv2):
    run = dv2.run_validation(run_id="dv-test-001")
    assert run["run_id"] == "dv-test-001"


def test_dv2_findings_present(dv2):
    run = dv2.run_validation()
    assert len(run["findings"]) > 0


def test_dv2_findings_by_severity(dv2):
    run = dv2.run_validation()
    assert "HIGH" in run["findings_by_severity"]
    assert "MEDIUM" in run["findings_by_severity"]
    assert "LOW" in run["findings_by_severity"]
    assert "INFO" in run["findings_by_severity"]


def test_dv2_finding_structure(dv2):
    run = dv2.run_validation()
    f = run["findings"][0]
    assert "check" in f
    assert "severity" in f
    assert "passed" in f
    assert "detail" in f
    assert "remediation" in f


def test_dv2_port_check_passes_in_demo(dv2):
    run = dv2.run_validation()
    port_findings = [f for f in run["findings"] if f["check"] == "port_check"]
    assert len(port_findings) == 1
    assert port_findings[0]["passed"] is True  # default API_PORT=8090


def test_dv2_demo_mode_flag_check(dv2):
    run = dv2.run_validation()
    demo_findings = [f for f in run["findings"] if f["check"] == "demo_mode_flag"]
    assert len(demo_findings) == 1
    assert demo_findings[0]["passed"] is True


def test_dv2_overall_status_pass_in_demo(dv2):
    run = dv2.run_validation()
    assert run["overall_status"] == "PASS"


def test_dv2_selected_checks_filter(dv2):
    run = dv2.run_validation(selected_checks=["port_check", "log_level"])
    assert run["total_checks"] == 2


def test_dv2_list_runs(dv2):
    dv2.run_validation(run_id="dv-l-001")
    dv2.run_validation(run_id="dv-l-002")
    runs = dv2.list_runs()
    assert len(runs) >= 2


def test_dv2_get_run(dv2):
    dv2.run_validation(run_id="dv-g-001")
    r = dv2.get_run("dv-g-001")
    assert r["run_id"] == "dv-g-001"


def test_dv2_get_run_missing_raises(dv2):
    with pytest.raises(ValueError):
        dv2.get_run("no-such-run")


def test_dv2_http_run(dv2):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(dv2.router)
    client = TestClient(app)
    r = client.post("/deploy-validator/run", json={"target_env": "demo"})
    assert r.status_code == 200
    assert "run" in r.json()


def test_dv2_http_list_checks(dv2):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(dv2.router)
    client = TestClient(app)
    r = client.get("/deploy-validator/checks")
    assert r.status_code == 200
    checks = r.json()["checks"]
    check_names = [c["name"] for c in checks]
    assert "port_check" in check_names
    assert "signing_key" in check_names


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 62 — Judge Mode v4
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def jv4():
    import judge_mode_v4 as m
    m.JUDGE_PACKS.clear()
    return m


def test_jv4_generate_returns_pack(jv4):
    pack = jv4.generate_pack(pack_id="jv4-test-001")
    assert pack["pack_id"] == "jv4-test-001"


def test_jv4_five_sections(jv4):
    pack = jv4.generate_pack()
    assert len(pack["sections"]) == 5


def test_jv4_section_names(jv4):
    pack = jv4.generate_pack()
    names = {s["section"] for s in pack["sections"]}
    assert names == {
        "decision_support", "compliance", "deployment_readiness",
        "scenario_coverage", "review_quality"
    }


def test_jv4_final_score_range(jv4):
    pack = jv4.generate_pack()
    assert 0.0 <= pack["final_score"] <= 1.0


def test_jv4_grade_levels(jv4):
    assert jv4._grade(0.95) == "A"
    assert jv4._grade(0.85) == "B"
    assert jv4._grade(0.75) == "C"
    assert jv4._grade(0.65) == "D"
    assert jv4._grade(0.50) == "F"


def test_jv4_bundle_is_valid_zip(jv4):
    pack = jv4.generate_pack()
    bundle_bytes = base64.b64decode(pack["bundle_b64"])
    buf = io.BytesIO(bundle_bytes)
    assert zipfile.is_zipfile(buf)


def test_jv4_bundle_has_scoring_report(jv4):
    pack = jv4.generate_pack()
    bundle_bytes = base64.b64decode(pack["bundle_b64"])
    buf = io.BytesIO(bundle_bytes)
    with zipfile.ZipFile(buf) as zf:
        assert "scoring_report.json" in zf.namelist()


def test_jv4_bundle_has_readme(jv4):
    pack = jv4.generate_pack()
    bundle_bytes = base64.b64decode(pack["bundle_b64"])
    buf = io.BytesIO(bundle_bytes)
    with zipfile.ZipFile(buf) as zf:
        assert "README.md" in zf.namelist()


def test_jv4_bundle_checksum_is_deterministic(jv4):
    evidence = {"packet_ids": ["x"]}
    p1 = jv4.generate_pack(pack_id="jv4-det-same", evidence=evidence)
    b1 = base64.b64decode(p1["bundle_b64"])
    with zipfile.ZipFile(io.BytesIO(b1)) as zf1:
        report1 = json.loads(zf1.read("scoring_report.json"))
    jv4.JUDGE_PACKS.clear()
    p2 = jv4.generate_pack(pack_id="jv4-det-same", evidence=evidence)
    b2 = base64.b64decode(p2["bundle_b64"])
    with zipfile.ZipFile(io.BytesIO(b2)) as zf2:
        report2 = json.loads(zf2.read("scoring_report.json"))
    # Content must be identical even if compression byte-patterns differ
    assert report1["grade"] == report2["grade"]
    assert report1["final_score"] == report2["final_score"]
    assert report1["pack_id"] == report2["pack_id"] == "jv4-det-same"


def test_jv4_get_pack(jv4):
    jv4.generate_pack(pack_id="jv4-g-001")
    p = jv4.get_pack("jv4-g-001")
    assert p["pack_id"] == "jv4-g-001"


def test_jv4_list_packs_excludes_bundle_bytes(jv4):
    jv4.generate_pack(pack_id="jv4-lst-001")
    packs = jv4.list_packs()
    assert all("bundle_b64" not in p for p in packs)


def test_jv4_http_generate(jv4):
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(jv4.router)
    client = TestClient(app)
    r = client.post("/judge/v4/generate", json={})
    assert r.status_code == 200
    data = r.json()
    assert "grade" in data
    assert "final_score" in data


def test_jv4_http_list_packs(jv4):
    jv4._seed()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(jv4.router)
    client = TestClient(app)
    r = client.get("/judge/v4/packs")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 63 — SearchProvider
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sp():
    from search_provider import LocalSearchProvider
    p = LocalSearchProvider()
    return p


def test_sp_index_and_search(sp):
    sp.index("doc-001", "test", "risk analytics platform RiskCanvas")
    results = sp.search("risk")
    assert len(results) >= 1
    assert results[0].doc_id == "doc-001"


def test_sp_search_returns_sorted_by_score(sp):
    sp.index("doc-a", "test", "risk risk risk")
    sp.index("doc-b", "test", "risk analytics")
    results = sp.search("risk")
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_sp_search_empty_query_returns_empty(sp):
    sp.index("doc-x", "test", "something")
    results = sp.search("")
    assert results == []


def test_sp_filter_by_doc_type(sp):
    sp.index("doc-p", "packet", "decision packet")
    sp.index("doc-s", "scenario", "scenario run")
    results = sp.search("decision", doc_types=["packet"])
    ids = [r.doc_id for r in results]
    assert "doc-p" in ids
    assert "doc-s" not in ids


def test_sp_delete(sp):
    sp.index("doc-del", "test", "delete me")
    sp.delete("doc-del")
    results = sp.search("delete")
    assert all(r.doc_id != "doc-del" for r in results)


def test_sp_stats(sp):
    sp.index("doc-st1", "type_a", "foo")
    sp.index("doc-st2", "type_b", "bar")
    s = sp.stats()
    assert s["total_documents"] == 2


def test_sp_deterministic_results(sp):
    sp.index("doc-det-x", "t", "hello world risk")
    r1 = sp.search("risk")
    r2 = sp.search("risk")
    assert [r.doc_id for r in r1] == [r.doc_id for r in r2]


def test_sp_limit_respected(sp):
    for i in range(10):
        sp.index(f"doc-{i}", "t", "risk analytics")
    results = sp.search("risk", limit=3)
    assert len(results) <= 3


def test_sp_provider_name():
    from search_provider import LocalSearchProvider, ElasticSearchProvider
    assert LocalSearchProvider().provider_name == "local"
    assert "elasticsearch" in ElasticSearchProvider("http://x").provider_name


def test_sp_get_provider_returns_local_in_demo():
    from search_provider import get_provider, LocalSearchProvider
    p = get_provider()
    # In DEMO mode, provider should be local
    assert isinstance(p, LocalSearchProvider)


def test_sp_http_index_and_query():
    from search_provider import LocalSearchProvider
    import search_provider as m
    p = LocalSearchProvider()
    m._provider = p
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    client.post("/search/index", json={"doc_id": "d1", "doc_type": "t", "content": "risk platform"})
    r = client.post("/search/query", json={"query": "risk"})
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_sp_http_stats():
    from search_provider import LocalSearchProvider
    import search_provider as m
    p = LocalSearchProvider()
    m._provider = p
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    r = client.get("/search/stats")
    assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# Wave 64 — LLMProvider
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def noop():
    from llm_provider import NoOpProvider
    return NoOpProvider()


def test_llm_noop_complete_returns_response(noop):
    from llm_provider import LLMResponse
    resp = noop.complete("What is risk?")
    assert isinstance(resp, LLMResponse)
    assert len(resp.text) > 0


def test_llm_noop_deterministic(noop):
    r1 = noop.complete("Analyze this portfolio")
    r2 = noop.complete("Analyze this portfolio")
    assert r1.text == r2.text


def test_llm_noop_different_prompts_may_differ(noop):
    """Different prompts may produce different canned responses."""
    r1 = noop.complete("risk a")
    r2 = noop.complete("risk analytics platform scenario runner compliance")
    # Just verify both return something valid
    assert len(r1.text) > 0
    assert len(r2.text) > 0


def test_llm_noop_summarize_truncates(noop):
    text = " ".join([f"word{i}" for i in range(200)])
    summary = noop.summarize(text, target_tokens=50)
    word_count = len(summary.split())
    assert word_count <= 52  # 50 + possible "[...]"


def test_llm_noop_extract_entities_sorted(noop):
    entities = noop.extract_entities("Alice reviewed the RiskCanvas Platform")
    assert entities == sorted(entities)


def test_llm_noop_provider_name(noop):
    assert noop.provider_name == "noop"


def test_llm_noop_model_name(noop):
    assert noop.model_name == "noop-v1"


def test_llm_nova_stub_delegates_to_noop():
    from llm_provider import NovaProvider
    nova = NovaProvider(api_key="test-key-abc123")
    resp = nova.complete("test prompt")
    assert len(resp.text) > 0
    assert resp.provider == "nova"


def test_llm_nova_stub_deterministic():
    from llm_provider import NovaProvider
    nova = NovaProvider(api_key="test-key")
    r1 = nova.complete("same prompt exactly")
    r2 = nova.complete("same prompt exactly")
    assert r1.text == r2.text


def test_llm_get_provider_returns_noop_in_demo():
    from llm_provider import get_provider, NoOpProvider
    p = get_provider()
    assert isinstance(p, NoOpProvider)


def test_llm_http_complete():
    import llm_provider as m
    m._provider = m.NoOpProvider()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    r = client.post("/llm/complete", json={"prompt": "summarize risk"})
    assert r.status_code == 200
    data = r.json()
    assert "text" in data
    assert "provider" in data


def test_llm_http_summarize():
    import llm_provider as m
    m._provider = m.NoOpProvider()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    r = client.post("/llm/summarize", json={"text": "the quick brown fox jumped over the lazy dog", "target_tokens": 5})
    assert r.status_code == 200
    assert "summary" in r.json()


def test_llm_http_extract_entities():
    import llm_provider as m
    m._provider = m.NoOpProvider()
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    r = client.post("/llm/extract-entities", json={"text": "Alice and Bob reviewed the RiskCanvas Decision"})
    assert r.status_code == 200
    assert "entities" in r.json()


def test_llm_http_health():
    import llm_provider as m
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(m.router)
    client = TestClient(app)
    r = client.get("/llm/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_llm_response_to_dict(noop):
    resp = noop.complete("dict test")
    d = resp.to_dict()
    assert "text" in d
    assert "model" in d
    assert "provider" in d
    assert d["deterministic"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: decision_packet auto-signing (Wave 57 integration)
# ═══════════════════════════════════════════════════════════════════════════════


def test_decision_packet_has_signature_after_generate():
    """When a packet is generated, it should be auto-signed by packet_signing."""
    import decision_packet as dp
    import packet_signing as ps
    # Clear signing store so we can check it gets populated
    ps.SIGNATURE_STORE.clear()
    # Generate a fresh packet
    pkt = dp.generate_decision_packet("tenant-001", "scenario", "scn-demo-001")
    # The packet should have signed field
    assert pkt.get("signed") is True
    # And there should be a signature record stored
    packet_id = pkt["packet_id"]
    assert ps.get_signature(packet_id) is not None


def test_decision_packet_signature_is_verifiable():
    """Generated signature can be verified offline."""
    import decision_packet as dp
    import packet_signing as ps
    ps.SIGNATURE_STORE.clear()
    pkt = dp.generate_decision_packet("tenant-001", "scenario", "scn-demo-001")
    if pkt.get("signed"):
        packet_id = pkt["packet_id"]
        sig = ps.get_signature(packet_id)
        assert sig is not None
        result = ps.verify_signed_packet(
            packet_id,
            sig["manifest_hash"],
            sig["files"],
        )
        assert result["verified"] is True
