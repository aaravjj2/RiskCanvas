"""Tests for Judge Mode W26-32 (Wave 32, v4.72-v4.73)"""
import pytest
import json
from judge_mode_w26_32 import generate_judge_pack, _WAVE_EVIDENCE


def test_generate_pack():
    pack = generate_judge_pack()
    assert pack["pack_id"]
    assert pack["pack_hash"]
    assert pack["audit_chain_head_hash"]
    assert pack["generated_at"]


def test_summary_fields():
    pack = generate_judge_pack()
    summary = pack["summary"]
    assert summary["verdict"] == "PASS"
    assert summary["total_releases"] == 24
    assert summary["waves_evaluated"] == 7
    assert summary["score_pct"] == 100.0
    assert summary["total_score"] == summary["max_score"]
    assert len(summary["modules"]) == 7
    assert len(summary["all_endpoints"]) > 0
    assert "v4.50.0 → v4.73.0" == summary["version_range"]


def test_files_structure():
    pack = generate_judge_pack()
    file_names = {f["name"] for f in pack["files"]}
    assert file_names == {"summary.json", "gate_scores.json", "wave_evidence.json", "audit_chain.json"}
    assert pack["file_count"] == 4


def test_file_contents_valid_json():
    pack = generate_judge_pack()
    for f in pack["files"]:
        if f["name"].endswith(".json"):
            parsed = json.loads(f["content"])
            assert parsed is not None


def test_gate_scores():
    pack = generate_judge_pack()
    gate_scores = json.loads(next(f["content"] for f in pack["files"] if f["name"] == "gate_scores.json"))
    assert len(gate_scores) == 7
    for gate in gate_scores:
        assert gate["score"] == 100
        assert gate["verdict"] == "PASS"
        assert gate["endpoint_count"] > 0


def test_wave_evidence():
    pack = generate_judge_pack()
    evidence = json.loads(next(f["content"] for f in pack["files"] if f["name"] == "wave_evidence.json"))
    assert len(evidence) == 7
    waves = [e["wave"] for e in evidence]
    assert waves == [26, 27, 28, 29, 30, 31, 32]


def test_audit_chain():
    pack = generate_judge_pack()
    chain = json.loads(next(f["content"] for f in pack["files"] if f["name"] == "audit_chain.json"))
    assert len(chain) == 7
    # Each entry's prev_hash == previous entry's entry_hash
    for i in range(1, len(chain)):
        assert chain[i]["prev_hash"] == chain[i-1]["entry_hash"]


def test_audit_chain_head_matches():
    pack = generate_judge_pack()
    chain = json.loads(next(f["content"] for f in pack["files"] if f["name"] == "audit_chain.json"))
    assert pack["audit_chain_head_hash"] == chain[-1]["entry_hash"]


def test_determinism():
    p1 = generate_judge_pack()
    p2 = generate_judge_pack()
    assert p1["pack_hash"] == p2["pack_hash"]
    assert p1["audit_chain_head_hash"] == p2["audit_chain_head_hash"]
    assert p1["summary"]["score_pct"] == p2["summary"]["score_pct"]


def test_modules_list():
    pack = generate_judge_pack()
    modules = pack["summary"]["modules"]
    assert "mr_review_agents" in modules
    assert "incident_drills" in modules
    assert "release_readiness" in modules
    assert "workflow_studio" in modules
    assert "policy_registry_v2" in modules
    assert "search_v2" in modules
    assert "judge_mode" in modules


def test_all_endpoints_present():
    pack = generate_judge_pack()
    endpoints = pack["summary"]["all_endpoints"]
    assert "/mr/review/plan" in endpoints
    assert "/incidents/scenarios" in endpoints
    assert "/release/readiness/evaluate" in endpoints
    assert "/workflows/generate" in endpoints
    assert "/policies/v2/create" in endpoints
    assert "/search/v2/stats" in endpoints
    assert "/judge/w26-32/generate-pack" in endpoints


def test_wave_count():
    assert len(_WAVE_EVIDENCE) == 7


def test_total_endpoint_count():
    total = sum(len(ev["endpoints"]) for ev in _WAVE_EVIDENCE)
    assert total >= 20  # roughly 3-6 endpoints per wave
