"""
RiskCanvas v4.66.0-v4.69.0 — Policy Registry V2 (Wave 30)

Provides:
- Versioned policies: create → publish → rollback
- Policy V2 model: id, slug, version_number, status (draft/published/rolled_back)
- Immutable published versions with hash chain
- Rollback: creates a new version from a previous one
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
VERSION = "v4.69.0"
ASOF = "2026-02-19T11:00:00Z"


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _compact(data: Any) -> str:
    return _sha(data)[:16]


def _chain_head() -> str:
    return "policyv2_chain_e5f6a7b8"


# ─────────────────── Model ───────────────────────────────────────────────────

class PolicyV2:
    def __init__(self, slug: str, title: str, body: str, tags: List[str],
                 version_number: int = 1, status: str = "draft",
                 parent_hash: Optional[str] = None):
        self.slug = slug
        self.title = title
        self.body = body
        self.tags = tags
        self.version_number = version_number
        self.status = status
        canonical = {"slug": slug, "title": title, "body": body, "tags": sorted(tags), "v": version_number}
        self.content_hash = _sha(canonical)
        self.policy_id = self.content_hash[:24]
        self.created_at = ASOF
        self.parent_hash = parent_hash or _chain_head()
        self.audit_chain_hash = _sha({"content": self.content_hash, "parent": self.parent_hash})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "slug": self.slug,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "version_number": self.version_number,
            "status": self.status,
            "content_hash": self.content_hash,
            "audit_chain_hash": self.audit_chain_hash,
            "parent_hash": self.parent_hash,
            "created_at": self.created_at,
        }


# ─────────────────── In-memory store ─────────────────────────────────────────

# slug → list of PolicyV2 (ascending version_number)
_POLICIES: Dict[str, List[PolicyV2]] = {}


def reset_policies_v2() -> None:
    _POLICIES.clear()


# ─────────────────── Public API ───────────────────────────────────────────────

def create_policy(slug: str, title: str, body: str, tags: List[str]) -> Dict[str, Any]:
    existing = _POLICIES.get(slug, [])
    version_number = len(existing) + 1
    parent_hash = existing[-1].audit_chain_hash if existing else _chain_head()
    p = PolicyV2(slug, title, body, tags, version_number=version_number, parent_hash=parent_hash)
    if slug not in _POLICIES:
        _POLICIES[slug] = []
    _POLICIES[slug].append(p)
    return p.to_dict()


def publish_policy(slug: str, version_number: Optional[int] = None) -> Dict[str, Any]:
    versions = _POLICIES.get(slug, [])
    if not versions:
        raise ValueError(f"Policy not found: {slug}")
    if version_number is None:
        target = versions[-1]
    else:
        matches = [v for v in versions if v.version_number == version_number]
        if not matches:
            raise ValueError(f"Version {version_number} not found for policy: {slug}")
        target = matches[0]
    if target.status == "published":
        return target.to_dict()
    target.status = "published"
    return target.to_dict()


def rollback_policy(slug: str, to_version: int) -> Dict[str, Any]:
    versions = _POLICIES.get(slug, [])
    if not versions:
        raise ValueError(f"Policy not found: {slug}")
    matches = [v for v in versions if v.version_number == to_version]
    if not matches:
        raise ValueError(f"Version {to_version} not found for policy: {slug}")
    source = matches[0]
    # Mark current latest as rolled_back
    latest = versions[-1]
    latest.status = "rolled_back"
    # Create new version copying source content
    parent_hash = latest.audit_chain_hash
    new_version_number = len(versions) + 1
    new_p = PolicyV2(
        slug=slug, title=source.title, body=source.body, tags=source.tags,
        version_number=new_version_number, status="draft", parent_hash=parent_hash,
    )
    _POLICIES[slug].append(new_p)
    result = new_p.to_dict()
    result["rollback_from_version"] = to_version
    result["note"] = f"Rolled back from v{latest.version_number} to content of v{to_version}"
    return result


def list_policies() -> List[Dict[str, Any]]:
    result = []
    for slug, versions in _POLICIES.items():
        if versions:
            latest = versions[-1]
            result.append({
                "slug": slug,
                "title": latest.title,
                "latest_version": latest.version_number,
                "status": latest.status,
                "policy_id": latest.policy_id,
                "version_count": len(versions),
            })
    return result


def get_policy_versions(slug: str) -> List[Dict[str, Any]]:
    versions = _POLICIES.get(slug)
    if not versions:
        raise ValueError(f"Policy not found: {slug}")
    return [v.to_dict() for v in versions]


# ─────────────────── Router ──────────────────────────────────────────────────

policy_registry_v2_router = APIRouter(tags=["policy_registry_v2"])


class CreatePolicyRequest(BaseModel):
    slug: str = Field(default="risk-assessment-policy")
    title: str = Field(default="Risk Assessment Policy")
    body: str = Field(default="All positions must be assessed for market, credit, and operational risk daily.")
    tags: List[str] = Field(default_factory=lambda: ["risk", "compliance"])


class PublishRequest(BaseModel):
    slug: str
    version_number: Optional[int] = None


class RollbackRequest(BaseModel):
    slug: str
    to_version: int


@policy_registry_v2_router.post("/policies/v2/create")
def api_create(req: CreatePolicyRequest):
    return create_policy(req.slug, req.title, req.body, req.tags)


@policy_registry_v2_router.post("/policies/v2/publish")
def api_publish(req: PublishRequest):
    try:
        return publish_policy(req.slug, req.version_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@policy_registry_v2_router.post("/policies/v2/rollback")
def api_rollback(req: RollbackRequest):
    try:
        return rollback_policy(req.slug, req.to_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@policy_registry_v2_router.get("/policies/v2/list")
def api_list():
    return {"policies": list_policies()}


@policy_registry_v2_router.get("/policies/v2/versions/{slug}")
def api_versions(slug: str):
    try:
        return {"slug": slug, "versions": get_policy_versions(slug)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
