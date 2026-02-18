"""
Tests for platform health, readiness, liveness, and infra validation (v2.9).

All tests are offline/deterministic — no network calls.
"""

import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure DEMO_MODE for deterministic responses
os.environ["DEMO_MODE"] = "true"

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_demo_mode(monkeypatch):
    """Guarantee DEMO_MODE=true for every test in this module."""
    monkeypatch.setenv("DEMO_MODE", "true")


# ─── /platform/health/details ─────────────────────────────────────────────────

class TestPlatformHealthDetails:
    def test_health_details_returns_200(self):
        r = client.get("/platform/health/details")
        assert r.status_code == 200

    def test_health_details_status_healthy(self):
        r = client.get("/platform/health/details")
        data = r.json()
        assert data["status"] == "healthy"

    def test_health_details_port_8090(self):
        r = client.get("/platform/health/details")
        data = r.json()
        assert data["port"] == 8090

    def test_health_details_demo_mode_flag(self):
        r = client.get("/platform/health/details")
        data = r.json()
        # In test env DEMO_MODE=true
        assert data["demo_mode"] is True

    def test_health_details_services_present(self):
        r = client.get("/platform/health/details")
        data = r.json()
        assert "services" in data
        assert len(data["services"]) >= 2

    def test_health_details_services_all_ok(self):
        r = client.get("/platform/health/details")
        data = r.json()
        for svc in data["services"]:
            assert svc["status"] == "ok", f"Service {svc['name']} not ok"

    def test_health_details_deterministic_in_demo(self):
        """Same input → same output in DEMO mode."""
        r1 = client.get("/platform/health/details")
        r2 = client.get("/platform/health/details")
        d1 = r1.json()
        d2 = r2.json()
        # Timestamp must be stable (deterministic) in DEMO mode
        assert d1["timestamp"] == d2["timestamp"]
        assert d1["port"] == d2["port"]

    def test_health_details_api_version(self):
        r = client.get("/platform/health/details")
        data = r.json()
        assert "api_version" in data
        assert data["api_version"] != ""


# ─── /platform/readiness ──────────────────────────────────────────────────────

class TestPlatformReadiness:
    def test_readiness_returns_200(self):
        r = client.get("/platform/readiness")
        assert r.status_code == 200

    def test_readiness_ready_true(self):
        r = client.get("/platform/readiness")
        data = r.json()
        assert data["ready"] is True

    def test_readiness_checks_dict(self):
        r = client.get("/platform/readiness")
        data = r.json()
        assert isinstance(data["checks"], dict)
        assert len(data["checks"]) >= 3

    def test_readiness_all_checks_pass(self):
        r = client.get("/platform/readiness")
        data = r.json()
        for k, v in data["checks"].items():
            assert v is True, f"Readiness check '{k}' failed"


# ─── /platform/liveness ───────────────────────────────────────────────────────

class TestPlatformLiveness:
    def test_liveness_returns_200(self):
        r = client.get("/platform/liveness")
        assert r.status_code == 200

    def test_liveness_alive_true(self):
        r = client.get("/platform/liveness")
        data = r.json()
        assert data["alive"] is True

    def test_liveness_has_timestamp(self):
        r = client.get("/platform/liveness")
        data = r.json()
        assert "timestamp" in data

    def test_liveness_deterministic_in_demo(self):
        r1 = client.get("/platform/liveness")
        r2 = client.get("/platform/liveness")
        assert r1.json()["timestamp"] == r2.json()["timestamp"]


# ─── /platform/infra/validate ─────────────────────────────────────────────────

class TestInfraValidation:
    def test_infra_validate_returns_200(self):
        r = client.get("/platform/infra/validate")
        assert r.status_code == 200

    def test_infra_validate_has_checks(self):
        r = client.get("/platform/infra/validate")
        data = r.json()
        assert "checks" in data
        assert len(data["checks"]) >= 3

    def test_infra_validate_has_summary(self):
        r = client.get("/platform/infra/validate")
        data = r.json()
        assert "summary" in data
        assert "/" in data["summary"]  # "X/Y checks passed"

    def test_infra_compose_port_8090_check_passes(self):
        r = client.get("/platform/infra/validate")
        data = r.json()
        port_check = next(
            (c for c in data["checks"] if c["name"] == "compose_port_8090"),
            None
        )
        assert port_check is not None
        assert port_check["passed"] is True, port_check["detail"]

    def test_infra_port_consistency_check_passes(self):
        r = client.get("/platform/infra/validate")
        data = r.json()
        port_check = next(
            (c for c in data["checks"] if c["name"] == "port_consistency"),
            None
        )
        assert port_check is not None
        assert port_check["passed"] is True, port_check["detail"]

    def test_infra_files_exist_check_passes(self):
        r = client.get("/platform/infra/validate")
        data = r.json()
        files_check = next(
            (c for c in data["checks"] if c["name"] == "infra_files_exist"),
            None
        )
        assert files_check is not None
        assert files_check["passed"] is True, files_check["detail"]


# ─── Unit tests for infra validation functions ────────────────────────────────

class TestInfraValidationUnit:
    def test_run_infra_validation_import(self):
        from platform_health import run_infra_validation
        result = run_infra_validation()
        assert result is not None
        assert isinstance(result.checks, list)

    def test_check_port_consistency(self):
        from platform_health import _check_port_consistency
        result = _check_port_consistency()
        assert result.passed is True, result.detail

    def test_check_compose_port_8090(self):
        from platform_health import _check_api_port_8090_in_compose
        result = _check_api_port_8090_in_compose()
        assert result.passed is True, result.detail

    def test_check_infra_files_exist(self):
        from platform_health import _check_infra_files_exist
        result = _check_infra_files_exist()
        assert result.passed is True, result.detail
