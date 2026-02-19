"""Tests for Exports Hub (Wave 34, v4.80.0)"""
import pytest
from fastapi.testclient import TestClient

# Import via main to get the full app with router registered
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exports_hub import router
from fastapi import FastAPI

# Standalone test app
_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app)


def test_get_recent_exports_status():
    resp = _client.get("/exports/recent")
    assert resp.status_code == 200


def test_get_recent_exports_structure():
    resp = _client.get("/exports/recent")
    data = resp.json()
    assert "packs" in data
    assert "total" in data
    assert isinstance(data["packs"], list)
    assert data["total"] > 0


def test_recent_exports_count():
    resp = _client.get("/exports/recent")
    data = resp.json()
    assert data["total"] == len(data["packs"])
    assert data["total"] >= 3


def test_pack_structure():
    resp = _client.get("/exports/recent")
    packs = resp.json()["packs"]
    required_fields = {"pack_id", "type", "label", "sha256", "status", "wave"}
    for p in packs:
        assert required_fields.issubset(set(p.keys())), f"Missing fields in {p}"


def test_pack_verified_status():
    resp = _client.get("/exports/recent")
    packs = resp.json()["packs"]
    verified = [p for p in packs if p["status"] == "verified"]
    assert len(verified) >= 3


def test_pack_sha256_nonempty():
    resp = _client.get("/exports/recent")
    packs = resp.json()["packs"]
    for p in packs:
        assert len(p["sha256"]) >= 32, f"SHA256 too short: {p['sha256']}"


def test_verify_existing_pack():
    resp = _client.get("/exports/verify/pack-mr-101-v53")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert len(data["sha256"]) >= 32
    assert "pack_id" in data


def test_verify_unknown_pack():
    resp = _client.get("/exports/verify/pack-does-not-exist")
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is False
    assert data["pack_id"] == "pack-does-not-exist"


def test_idempotency_recent():
    """Same call returns same result (deterministic)."""
    r1 = _client.get("/exports/recent").json()
    r2 = _client.get("/exports/recent").json()
    assert r1["total"] == r2["total"]
    ids1 = [p["pack_id"] for p in r1["packs"]]
    ids2 = [p["pack_id"] for p in r2["packs"]]
    assert ids1 == ids2


def test_idempotency_verify():
    """Verify is idempotent."""
    r1 = _client.get("/exports/verify/pack-judge-w26-32-final").json()
    r2 = _client.get("/exports/verify/pack-judge-w26-32-final").json()
    assert r1["sha256"] == r2["sha256"]
    assert r1["verified"] == r2["verified"]


def test_generated_at_field():
    resp = _client.get("/exports/recent")
    data = resp.json()
    assert "generated_at" in data
    assert "Z" in data["generated_at"]


def test_pack_size_positive():
    resp = _client.get("/exports/recent")
    packs = resp.json()["packs"]
    for p in packs:
        assert p["size_bytes"] > 0
