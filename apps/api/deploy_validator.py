"""
deploy_validator.py (v5.38.0-v5.39.0 — Wave 53)

Offline deploy validation: Azure + DigitalOcean.
No network calls. Pure static checking.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

# ── Azure ACA required env vars ───────────────────────────────────────────────

AZURE_REQUIRED_VARS: List[str] = [
    "AZURE_SUBSCRIPTION_ID",
    "AZURE_RESOURCE_GROUP",
    "AZURE_CONTAINER_APP_NAME",
    "AZURE_CONTAINER_REGISTRY",
    "AZURE_STORAGE_ACCOUNT",
    "AZURE_STORAGE_CONTAINER",
    "AZURE_CLIENT_ID",
    "DEMO_MODE",
    "API_PORT",
]

AZURE_OPTIONAL_VARS: List[str] = [
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_SECRET",
    "ENTRA_APP_ID",
    "LOG_ANALYTICS_WORKSPACE_ID",
]

# ── DigitalOcean required env vars ─────────────────────────────────────────────

DO_REQUIRED_VARS: List[str] = [
    "DO_APP_NAME",
    "DO_REGION",
    "DIGITALOCEAN_ACCESS_TOKEN",
    "DATABASE_URL",
    "DEMO_MODE",
    "API_PORT",
]

DO_OPTIONAL_VARS: List[str] = [
    "DO_REGISTRY_NAME",
    "DO_SPACES_BUCKET",
    "DO_SPACES_REGION",
    "DO_SPACES_KEY",
    "DO_SPACES_SECRET",
]


def validate_azure_env(env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Check Azure ACA environment variables for completeness (OFFLINE)."""
    env = env or {}
    missing = [v for v in AZURE_REQUIRED_VARS if v not in env and not os.getenv(v)]
    present = [v for v in AZURE_REQUIRED_VARS if v in env or os.getenv(v)]
    optional_present = [v for v in AZURE_OPTIONAL_VARS if v in env or os.getenv(v)]

    return {
        "provider": "Azure",
        "valid": len(missing) == 0,
        "required_present": present,
        "required_missing": missing,
        "optional_present": optional_present,
        "completeness_pct": round(len(present) / len(AZURE_REQUIRED_VARS) * 100, 1),
        "note": "Offline check only — no network calls made",
    }


def validate_do_env(env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Check DigitalOcean environment variables for completeness (OFFLINE)."""
    env = env or {}
    missing = [v for v in DO_REQUIRED_VARS if v not in env and not os.getenv(v)]
    present = [v for v in DO_REQUIRED_VARS if v in env or os.getenv(v)]
    optional_present = [v for v in DO_OPTIONAL_VARS if v in env or os.getenv(v)]

    return {
        "provider": "DigitalOcean",
        "valid": len(missing) == 0,
        "required_present": present,
        "required_missing": missing,
        "optional_present": optional_present,
        "completeness_pct": round(len(present) / len(DO_REQUIRED_VARS) * 100, 1),
        "note": "Offline check only — no network calls made",
    }


def validate_all_envs(env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    azure = validate_azure_env(env)
    do = validate_do_env(env)
    # In a clean local DEMO, both will have some missing vars — that's expected
    return {
        "azure": azure,
        "digitalocean": do,
        "any_critical_missing": bool(azure["required_missing"] or do["required_missing"]),
        "note": "Run with actual env file to get accurate results",
    }


# ── DigitalOcean template linting ─────────────────────────────────────────────

DO_COMPOSE_TEMPLATE = """# DigitalOcean App Platform — RiskCanvas

services:
  api:
    name: riskcanvas-api
    github:
      branch: main
      deploy_on_push: true
    run_command: uvicorn main:app --host 0.0.0.0 --port ${API_PORT:-8090}
    envs:
      - key: DEMO_MODE
        value: "false"
      - key: API_PORT
        value: "8090"
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
    http_port: 8090
    health_check:
      http_path: /health

  web:
    name: riskcanvas-web
    github:
      branch: main
      deploy_on_push: true
    build_command: npm run build
    output_dir: dist
    routes:
      - path: /
"""

DO_NGINX_TEMPLATE = """server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://api:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
"""


def lint_do_compose_template(template: str) -> Dict[str, Any]:
    """Lint a DigitalOcean compose template for required fields (OFFLINE)."""
    errors: List[str] = []
    warnings: List[str] = []

    required_keys = ["services:", "name:", "run_command:", "http_port:"]
    for key in required_keys:
        if key not in template:
            errors.append(f"Missing required key: '{key}'")

    if "DATABASE_URL" not in template:
        warnings.append("DATABASE_URL secret not configured")
    if "DEMO_MODE" not in template:
        warnings.append("DEMO_MODE not set")
    if "health_check:" not in template:
        warnings.append("Missing health_check configuration")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "template_length": len(template),
    }


def lint_nginx_template(template: str) -> Dict[str, Any]:
    """Lint an nginx config template (OFFLINE)."""
    errors: List[str] = []
    warnings: List[str] = []

    required = ["server {", "location /api/", "proxy_pass", "try_files"]
    for req in required:
        if req not in template:
            errors.append(f"Missing directive: '{req}'")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ── FastAPI router ────────────────────────────────────────────────────────────

router = APIRouter(prefix="/deploy", tags=["deploy"])


class ValidateEnvRequest(BaseModel):
    env: Optional[Dict[str, str]] = None


class LintTemplateRequest(BaseModel):
    template: str
    template_type: str = "do_compose"  # do_compose | nginx


@router.post("/validate-azure")
async def api_validate_azure(req: ValidateEnvRequest):
    return validate_azure_env(req.env)


@router.post("/validate-do")
async def api_validate_do(req: ValidateEnvRequest):
    return validate_do_env(req.env)


@router.post("/validate-all")
async def api_validate_all(req: ValidateEnvRequest):
    return validate_all_envs(req.env)


@router.post("/lint-template")
async def api_lint_template(req: LintTemplateRequest):
    if req.template_type == "do_compose":
        return lint_do_compose_template(req.template)
    elif req.template_type == "nginx":
        return lint_nginx_template(req.template)
    else:
        return {"valid": False, "errors": [f"Unknown template_type: {req.template_type}"], "warnings": []}


@router.get("/templates/do-compose")
async def api_get_do_compose_template():
    return {"template": DO_COMPOSE_TEMPLATE, "type": "do_compose"}


@router.get("/templates/nginx")
async def api_get_nginx_template():
    return {"template": DO_NGINX_TEMPLATE, "type": "nginx"}


@router.get("/templates/azure-required-vars")
async def api_get_azure_required_vars():
    return {
        "required": AZURE_REQUIRED_VARS,
        "optional": AZURE_OPTIONAL_VARS,
        "provider": "Azure",
    }


@router.get("/templates/do-required-vars")
async def api_get_do_required_vars():
    return {
        "required": DO_REQUIRED_VARS,
        "optional": DO_OPTIONAL_VARS,
        "provider": "DigitalOcean",
    }
