"""
test_judge_mode_w33_40.py (Wave 40)

Tests for /judge/w33-40/generate-pack and /judge/w33-40/files endpoints.
All deterministic — no random data.
"""
import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_generate_pack_status():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_generate_pack_verdict_pass():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert body["summary"]["verdict"] == "PASS"


@pytest.mark.asyncio
async def test_generate_pack_waves_count():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert body["summary"]["waves_evaluated"] == 8


@pytest.mark.asyncio
async def test_generate_pack_score_pct():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert body["summary"]["score_pct"] == 100.0


@pytest.mark.asyncio
async def test_generate_pack_score_totals():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert body["summary"]["total_score"] == 800
    assert body["summary"]["total_max"] == 800


@pytest.mark.asyncio
async def test_generate_pack_has_pack_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert "pack_id" in body["summary"]
    assert "proof-wave33-40" in body["summary"]["pack_id"]


@pytest.mark.asyncio
async def test_generate_pack_has_checksum():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert len(body["summary"]["checksum"]) == 64  # SHA-256 hex


@pytest.mark.asyncio
async def test_generate_pack_waves_list():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    waves = body["waves"]
    assert len(waves) == 8
    wave_numbers = [w["wave"] for w in waves]
    assert wave_numbers == list(range(33, 41))


@pytest.mark.asyncio
async def test_generate_pack_all_waves_pass():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    for wave in body["waves"]:
        assert wave["status"] == "PASS", f"Wave {wave['wave']} not PASS"


@pytest.mark.asyncio
async def test_generate_pack_message_contains_score():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/judge/w33-40/generate-pack")
    body = resp.json()
    assert "100.0" in body["message"]
    assert "PASS" in body["message"]


@pytest.mark.asyncio
async def test_generate_pack_deterministic():
    """Same input always produces same checksum."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        r1 = await client.post("/judge/w33-40/generate-pack")
        r2 = await client.post("/judge/w33-40/generate-pack")
    assert r1.json()["summary"]["checksum"] == r2.json()["summary"]["checksum"]


@pytest.mark.asyncio
async def test_get_files_status():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/judge/w33-40/files")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_files_count():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/judge/w33-40/files")
    body = resp.json()
    assert body["file_count"] > 20
    assert body["file_count"] == len(body["files"])


@pytest.mark.asyncio
async def test_get_files_includes_key_files():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/judge/w33-40/files")
    body = resp.json()
    files = body["files"]
    assert any("ExportsHubPage" in f for f in files)
    assert any("WorkbenchPage" in f for f in files)
    assert any("DataTable" in f for f in files)


@pytest.mark.asyncio
async def test_get_files_pack_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/judge/w33-40/files")
    body = resp.json()
    assert body["pack_id"] == "proof-wave33-40-v4.97.0"
