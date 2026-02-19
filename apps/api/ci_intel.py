"""
RiskCanvas v4.46.0–v4.47.0 — CI Intelligence v2 + Template Generator (Wave 24)

Provides:
- Deterministic pipeline analyzer (failure categories)
- Root cause hypothesis from fixture runbooks
- .gitlab-ci.yml template generator (deterministic, no external calls)
- CI template pack export
No external calls. Safe for DEMO, tests, CI.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
CI_INTEL_VERSION = "v1.0"
ASOF = "2026-02-19T09:00:00Z"


# ─────────────────── Helpers ─────────────────────────────────────────────────


def _sha256(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _chain_head() -> str:
    return "ci_intel_e5f6a7b8c9"


# ─────────────────── Failure Category Runbooks ────────────────────────────────

FAILURE_CATEGORIES = ["tests", "build", "lint", "infra", "flaky", "dependency"]

_RUNBOOKS: Dict[str, Dict[str, Any]] = {
    "tests": {
        "display": "Test Failures",
        "root_causes": [
            "New code broke existing test assertions",
            "Environment mismatch (wrong database seed / fixture data)",
            "Timing dependency in async tests",
        ],
        "recommended_actions": [
            "Review failing test output: check assertion vs actual values",
            "Ensure test fixtures match expected schema version",
            "Add deterministic seeding for async tests",
        ],
        "severity": "HIGH",
    },
    "build": {
        "display": "Build Failures",
        "root_causes": [
            "TypeScript compilation error in new/modified files",
            "Missing npm dependency in package.json",
            "Vite config misconfigured for new page route",
        ],
        "recommended_actions": [
            "Run `tsc --noEmit` locally to identify TS errors",
            "Check package.json versions for missing deps",
            "Review vite.config.ts alias configuration",
        ],
        "severity": "HIGH",
    },
    "lint": {
        "display": "Lint / Style Violations",
        "root_causes": [
            "ESLint rule violations in new code",
            "Unused imports or variables (TS6133)",
            "Missing trailing comma (Prettier mismatch)",
        ],
        "recommended_actions": [
            "Run `eslint . --fix` to auto-fix style issues",
            "Run `tsc --noEmit` for unused variable errors",
            "Run `prettier --check .` to detect formatting issues",
        ],
        "severity": "MEDIUM",
    },
    "infra": {
        "display": "Infrastructure / Deploy Failures",
        "root_causes": [
            "Kubernetes resource quota exceeded",
            "Docker registry credentials expired",
            "Missing environment variable in deployment secret",
        ],
        "recommended_actions": [
            "Check k8s resource limits in deployment manifest",
            "Rotate Docker registry token and update CI secret",
            "Verify all required env vars in .env.example are set in CI",
        ],
        "severity": "CRITICAL",
    },
    "flaky": {
        "display": "Flaky Tests",
        "root_causes": [
            "Race condition in test setup/teardown",
            "External API call in test without mock",
            "Non-deterministic random seed",
        ],
        "recommended_actions": [
            "Add proper teardown and isolation in test setup",
            "Mock all external dependencies (no live calls in tests)",
            "Fix random seed to constant for reproducibility",
        ],
        "severity": "MEDIUM",
    },
    "dependency": {
        "display": "Dependency / Package Issues",
        "root_causes": [
            "Upstream package yanked or version removed from registry",
            "Breaking change in minor version upgrade",
            "Peer dependency conflict after upgrade",
        ],
        "recommended_actions": [
            "Pin dependencies to exact versions in requirements.txt / package-lock.json",
            "Review CHANGELOG of upgraded packages for breaking changes",
            "Run `npm audit` and `pip-audit` to check for known vulnerabilities",
        ],
        "severity": "MEDIUM",
    },
}

# ─────────────────── Fixture Pipelines ───────────────────────────────────────

_FIXTURE_PIPELINES: List[Dict[str, Any]] = [
    {
        "id": "pipe_001",
        "ref": "feat/fx-exposure",
        "status": "failed",
        "duration_s": 142,
        "failure_category": "tests",
        "failed_job": "pytest-backend",
        "failed_stage": "test",
        "created_at": "2026-02-18T10:00:00Z",
        "mr_iid": 101,
    },
    {
        "id": "pipe_002",
        "ref": "fix/dv01-boundary",
        "status": "failed",
        "duration_s": 58,
        "failure_category": "lint",
        "failed_job": "tsc-check",
        "failed_stage": "lint",
        "created_at": "2026-02-18T11:30:00Z",
        "mr_iid": 102,
    },
    {
        "id": "pipe_003",
        "ref": "chore/ci-wave23",
        "status": "success",
        "duration_s": 215,
        "failure_category": None,
        "failed_job": None,
        "failed_stage": None,
        "created_at": "2026-02-15T09:00:00Z",
        "mr_iid": 103,
    },
    {
        "id": "pipe_004",
        "ref": "sec/remove-hardcoded-key",
        "status": "failed",
        "duration_s": 33,
        "failure_category": "build",
        "failed_job": "vite-build",
        "failed_stage": "build",
        "created_at": "2026-02-19T06:00:00Z",
        "mr_iid": 104,
    },
    {
        "id": "pipe_005",
        "ref": "main",
        "status": "success",
        "duration_s": 382,
        "failure_category": None,
        "failed_job": None,
        "failed_stage": None,
        "created_at": "2026-02-19T07:00:00Z",
        "mr_iid": None,
    },
]


def list_pipelines() -> Dict[str, Any]:
    return {
        "pipelines": _FIXTURE_PIPELINES,
        "total": len(_FIXTURE_PIPELINES),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }


def analyze_pipeline(pipeline_id: str) -> Dict[str, Any]:
    pipe = next((p for p in _FIXTURE_PIPELINES if p["id"] == pipeline_id), None)
    if not pipe:
        raise ValueError(f"Pipeline not found: {pipeline_id}")

    cat = pipe.get("failure_category")
    if cat and cat in _RUNBOOKS:
        rb = _RUNBOOKS[cat]
        analysis = {
            "pipeline_id": pipeline_id,
            "status": pipe["status"],
            "ref": pipe["ref"],
            "failure_category": cat,
            "category_display": rb["display"],
            "failed_job": pipe.get("failed_job"),
            "failed_stage": pipe.get("failed_stage"),
            "root_cause_hypotheses": rb["root_causes"],
            "recommended_actions": rb["recommended_actions"],
            "severity": rb["severity"],
            "asof": ASOF,
            "audit_chain_head_hash": _chain_head(),
        }
    else:
        analysis = {
            "pipeline_id": pipeline_id,
            "status": pipe["status"],
            "ref": pipe["ref"],
            "failure_category": None,
            "category_display": "N/A — Pipeline succeeded",
            "failed_job": None,
            "failed_stage": None,
            "root_cause_hypotheses": [],
            "recommended_actions": [],
            "severity": "NONE",
            "asof": ASOF,
            "audit_chain_head_hash": _chain_head(),
        }

    analysis["output_hash"] = _sha256(analysis)
    return analysis


# ─────────────────── CI Template Generator ────────────────────────────────────

# Available feature toggles
_TEMPLATE_FEATURES: Dict[str, str] = {
    "pytest":     "Run pytest backend + engine tests",
    "tsc":        "TypeScript typecheck (tsc --noEmit)",
    "vite_build": "Vite production build",
    "playwright": "Playwright E2E tests",
    "lint":       "ESLint + Prettier checks",
    "security":   "Secret scanning + SBOM generation",
    "docker":     "Docker build + push to registry",
    "compliance": "Compliance pack generation",
}

_STAGE_ORDERING = ["lint", "test", "build", "security", "deploy", "compliance"]


def _feature_to_yaml_block(feature: str) -> str:
    blocks = {
        "pytest": (
            "pytest-backend:\n"
            "  stage: test\n"
            "  image: python:3.10\n"
            "  script:\n"
            "    - cd apps/api && pip install -r requirements.txt\n"
            "    - pytest tests/ -v --tb=short\n"
            "  rules:\n"
            "    - if: '$CI_PIPELINE_SOURCE == \"merge_request_event\"'\n"
            "    - if: '$CI_COMMIT_BRANCH == \"main\"'\n"
        ),
        "tsc": (
            "typescript-check:\n"
            "  stage: lint\n"
            "  image: node:20\n"
            "  script:\n"
            "    - npm ci\n"
            "    - node_modules/.bin/tsc --noEmit\n"
            "  rules:\n"
            "    - if: '$CI_PIPELINE_SOURCE == \"merge_request_event\"'\n"
        ),
        "vite_build": (
            "vite-build:\n"
            "  stage: build\n"
            "  image: node:20\n"
            "  script:\n"
            "    - npm ci\n"
            "    - cd apps/web && npm run build\n"
            "  artifacts:\n"
            "    paths:\n"
            "      - apps/web/dist/\n"
        ),
        "playwright": (
            "playwright-e2e:\n"
            "  stage: test\n"
            "  image: mcr.microsoft.com/playwright:v1.48.0\n"
            "  script:\n"
            "    - npm ci\n"
            "    - node_modules/.bin/playwright test --workers=1 --retries=0\n"
            "  artifacts:\n"
            "    when: always\n"
            "    paths:\n"
            "      - playwright-report/\n"
        ),
        "lint": (
            "lint-check:\n"
            "  stage: lint\n"
            "  image: node:20\n"
            "  script:\n"
            "    - npm ci\n"
            "    - npx eslint . --max-warnings 0\n"
            "    - npx prettier --check .\n"
        ),
        "security": (
            "secret-scan:\n"
            "  stage: security\n"
            "  script:\n"
            "    - python apps/api/scripts/scan_diff.py\n"
            "  rules:\n"
            "    - if: '$CI_PIPELINE_SOURCE == \"merge_request_event\"'\n"
        ),
        "docker": (
            "docker-build-push:\n"
            "  stage: deploy\n"
            "  image: docker:24\n"
            "  services:\n"
            "    - docker:24-dind\n"
            "  script:\n"
            "    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY\n"
            "    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .\n"
            "    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA\n"
        ),
        "compliance": (
            "compliance-pack:\n"
            "  stage: compliance\n"
            "  script:\n"
            "    - python apps/api/scripts/gen_compliance_pack.py\n"
            "  artifacts:\n"
            "    paths:\n"
            "      - artifacts/compliance/\n"
        ),
    }
    return blocks.get(feature, f"# Feature '{feature}' not found\n")


def generate_ci_template(features: List[str]) -> Dict[str, Any]:
    """Generate a deterministic .gitlab-ci.yml template based on selected features."""
    features = sorted(set(f.lower() for f in features))
    unknown = [f for f in features if f not in _TEMPLATE_FEATURES]
    if unknown:
        raise ValueError(f"Unknown features: {unknown}. Available: {list(_TEMPLATE_FEATURES.keys())}")

    # Determine stages needed
    stage_set = set()
    for f in features:
        if f in ("tsc", "lint"):
            stage_set.add("lint")
        elif f in ("pytest", "playwright"):
            stage_set.add("test")
        elif f in ("vite_build",):
            stage_set.add("build")
        elif f == "security":
            stage_set.add("security")
        elif f == "docker":
            stage_set.add("deploy")
        elif f == "compliance":
            stage_set.add("compliance")

    stages = [s for s in _STAGE_ORDERING if s in stage_set]

    lines = ["# RiskCanvas CI Template — auto-generated by CI Intelligence v2\n"]
    lines.append(f"# Generated: {ASOF}\n")
    lines.append(f"# Features: {', '.join(features)}\n\n")
    lines.append("stages:\n")
    for s in stages:
        lines.append(f"  - {s}\n")
    lines.append("\n")
    for f in features:
        lines.append(_feature_to_yaml_block(f))
        lines.append("\n")

    template_content = "".join(lines)

    result = {
        "template": template_content,
        "features_selected": features,
        "stages": stages,
        "template_hash": _sha256({"content": template_content}),
        "asof": ASOF,
        "audit_chain_head_hash": _chain_head(),
    }
    return result


# ─────────────────── Pydantic Models ─────────────────────────────────────────


class CITemplateRequest(BaseModel):
    features: List[str] = Field(
        default_factory=lambda: ["pytest", "tsc", "vite_build", "playwright", "lint"]
    )


class CITemplatePackRequest(BaseModel):
    features: List[str] = Field(
        default_factory=lambda: ["pytest", "tsc", "vite_build", "playwright", "lint"]
    )


# ─────────────────── FastAPI Routers ──────────────────────────────────────────

ci_router = APIRouter(prefix="/ci", tags=["ci"])


@ci_router.get("/pipelines")
def api_list_pipelines():
    return list_pipelines()


@ci_router.get("/pipelines/{pipeline_id}/analysis")
def api_analyze_pipeline(pipeline_id: str):
    try:
        return analyze_pipeline(pipeline_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@ci_router.get("/template/features")
def api_template_features():
    return {
        "features": [
            {"id": k, "description": v}
            for k, v in sorted(_TEMPLATE_FEATURES.items())
        ],
        "asof": ASOF,
    }


@ci_router.post("/template/generate")
def api_generate_template(req: CITemplateRequest):
    try:
        return generate_ci_template(req.features)
    except ValueError as e:
        raise HTTPException(400, str(e))


ci_exports_router = APIRouter(prefix="/exports", tags=["ci-exports"])


@ci_exports_router.post("/ci-template-pack")
def api_ci_template_pack(req: CITemplatePackRequest):
    try:
        template = generate_ci_template(req.features)
        pack = {
            "pack_type": "ci-template-pack",
            "version": CI_INTEL_VERSION,
            "template": template,
            "pipeline_categories": {k: v["display"] for k, v in sorted(_RUNBOOKS.items())},
            "asof": ASOF,
            "audit_chain_head_hash": _chain_head(),
        }
        pack["pack_hash"] = _sha256(pack)
        return pack
    except ValueError as e:
        raise HTTPException(400, str(e))
