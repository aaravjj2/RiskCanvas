"""
tenancy_v2.py (v4.98.0-v5.01.0 — Wave 41)

Real multi-tenant model with RBAC — DEMO-safe, enterprise believable.

Models:
  Tenant  {tenant_id, name, created_at, seed}
  User    {user_id, email, display_name}
  Membership {tenant_id, user_id, role: OWNER|ADMIN|ANALYST|VIEWER}

Deterministic IDs: sha256(canonical json)[:32]
Permissions:
  tenant.read, tenant.write, audit.read, policy.write,
  exports.write, jobs.write, admin.read, admin.write
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

ASOF = "2026-02-19T00:00:00Z"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


# ── Deterministic helpers ───────────────────────────────────────────────────

def _sha(data: Any) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def _tid(name: str) -> str:
    return _sha({"type": "tenant", "name": name})[:32]


def _uid(email: str) -> str:
    return _sha({"type": "user", "email": email})[:32]


def _mid(tenant_id: str, user_id: str) -> str:
    return _sha({"type": "membership", "tenant_id": tenant_id, "user_id": user_id})[:32]


# ── Roles and permissions ───────────────────────────────────────────────────

ROLES = ["OWNER", "ADMIN", "ANALYST", "VIEWER"]

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "OWNER":   ["tenant.read", "tenant.write", "audit.read", "policy.write",
                "exports.write", "jobs.write", "admin.read", "admin.write",
                "artifacts.read", "artifacts.write", "attestations.read", "compliance.write"],
    "ADMIN":   ["tenant.read", "audit.read", "policy.write",
                "exports.write", "jobs.write", "admin.read",
                "artifacts.read", "artifacts.write", "attestations.read", "compliance.write"],
    "ANALYST": ["tenant.read", "audit.read", "exports.write", "jobs.write",
                "artifacts.read", "attestations.read"],
    "VIEWER":  ["tenant.read", "audit.read", "artifacts.read", "attestations.read"],
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])


# ── Fixtures ────────────────────────────────────────────────────────────────

DEMO_TENANTS: Dict[str, Dict[str, Any]] = {}
DEMO_USERS: Dict[str, Dict[str, Any]] = {}
DEMO_MEMBERSHIPS: List[Dict[str, Any]] = []


def _build_fixtures() -> None:
    tenant_data = [
        ("riskcanvas-demo", "RiskCanvas Demo"),
        ("acme-corp", "ACME Corp"),
        ("beta-finance", "Beta Finance"),
    ]
    for name, display in tenant_data:
        tid = _tid(name)
        DEMO_TENANTS[tid] = {
            "tenant_id": tid,
            "name": display,
            "slug": name,
            "created_at": ASOF,
            "seed": _sha({"tenant": name, "seed": True})[:16],
            "member_count": 0,
        }

    user_data = [
        ("alice@demo.riskcanvas.io", "Alice (Owner)"),
        ("bob@demo.riskcanvas.io", "Bob (Admin)"),
        ("carol@demo.riskcanvas.io", "Carol (Analyst)"),
        ("dave@demo.riskcanvas.io", "Dave (Viewer)"),
    ]
    for email, display in user_data:
        uid = _uid(email)
        DEMO_USERS[uid] = {
            "user_id": uid,
            "email": email,
            "display_name": display,
            "created_at": ASOF,
        }

    # memberships: all users in tenant 0, some in tenant 1,2
    tenant_ids = list(DEMO_TENANTS.keys())
    user_ids = list(DEMO_USERS.keys())
    memberships_raw = [
        (tenant_ids[0], user_ids[0], "OWNER"),
        (tenant_ids[0], user_ids[1], "ADMIN"),
        (tenant_ids[0], user_ids[2], "ANALYST"),
        (tenant_ids[0], user_ids[3], "VIEWER"),
        (tenant_ids[1], user_ids[0], "OWNER"),
        (tenant_ids[1], user_ids[1], "ANALYST"),
        (tenant_ids[2], user_ids[0], "OWNER"),
    ]
    for tid, uid, role in memberships_raw:
        DEMO_MEMBERSHIPS.append({
            "membership_id": _mid(tid, uid),
            "tenant_id": tid,
            "user_id": uid,
            "role": role,
            "joined_at": ASOF,
        })

    # update member counts
    for m in DEMO_MEMBERSHIPS:
        DEMO_TENANTS[m["tenant_id"]]["member_count"] += 1


_build_fixtures()

# Expose first tenant as "default"
DEFAULT_TENANT_ID: str = list(DEMO_TENANTS.keys())[0]
DEFAULT_USER_ID: str = list(DEMO_USERS.keys())[0]  # alice = OWNER


def get_demo_context(
    x_demo_tenant: Optional[str] = None,
    x_demo_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Resolve the demo user context from headers.
    x-demo-tenant: slug or tenant_id
    x-demo-role: OWNER|ADMIN|ANALYST|VIEWER (overrides stored role)
    """
    # Find tenant
    tid = DEFAULT_TENANT_ID
    if x_demo_tenant:
        # try slug match first, then id
        for t in DEMO_TENANTS.values():
            if t["slug"] == x_demo_tenant or t["tenant_id"] == x_demo_tenant:
                tid = t["tenant_id"]
                break

    # Find membership (alice is always first)
    uid = DEFAULT_USER_ID
    role = "OWNER"
    for m in DEMO_MEMBERSHIPS:
        if m["tenant_id"] == tid and m["user_id"] == uid:
            role = m["role"]
            break
    if x_demo_role and x_demo_role.upper() in ROLES:
        role = x_demo_role.upper()

    return {
        "tenant_id": tid,
        "user_id": uid,
        "role": role,
        "permissions": ROLE_PERMISSIONS[role],
        "demo_mode": True,
    }


# ── Public API functions ─────────────────────────────────────────────────────

def list_tenants() -> List[Dict[str, Any]]:
    return sorted(DEMO_TENANTS.values(), key=lambda t: t["name"])


def get_tenant(tenant_id: str) -> Dict[str, Any]:
    t = DEMO_TENANTS.get(tenant_id)
    if not t:
        raise ValueError(f"Tenant not found: {tenant_id}")
    return t


def list_members(tenant_id: str) -> List[Dict[str, Any]]:
    if tenant_id not in DEMO_TENANTS:
        raise ValueError(f"Tenant not found: {tenant_id}")
    mems = [m for m in DEMO_MEMBERSHIPS if m["tenant_id"] == tenant_id]
    result = []
    for m in mems:
        u = DEMO_USERS.get(m["user_id"], {})
        result.append({**m, **u})
    return sorted(result, key=lambda x: x["role"])


def add_member(tenant_id: str, email: str, role: str) -> Dict[str, Any]:
    if tenant_id not in DEMO_TENANTS:
        raise ValueError(f"Tenant not found: {tenant_id}")
    role = role.upper()
    if role not in ROLES:
        raise ValueError(f"Invalid role: {role}")
    # Idempotent: create user if needed
    uid = _uid(email)
    if uid not in DEMO_USERS:
        DEMO_USERS[uid] = {
            "user_id": uid,
            "email": email,
            "display_name": email.split("@")[0].capitalize(),
            "created_at": ASOF,
        }
    # Create membership if needed (idempotent)
    existing = next(
        (m for m in DEMO_MEMBERSHIPS if m["tenant_id"] == tenant_id and m["user_id"] == uid),
        None
    )
    if not existing:
        new_m = {
            "membership_id": _mid(tenant_id, uid),
            "tenant_id": tenant_id,
            "user_id": uid,
            "role": role,
            "joined_at": ASOF,
        }
        DEMO_MEMBERSHIPS.append(new_m)
        DEMO_TENANTS[tenant_id]["member_count"] += 1
        return {**new_m, **DEMO_USERS[uid]}
    return {**existing, **DEMO_USERS[uid]}


def require_perm(ctx: Dict[str, Any], permission: str) -> None:
    if permission not in ctx.get("permissions", []):
        raise ValueError(
            f"Permission denied: requires '{permission}', role is '{ctx.get('role')}'"
        )


# ── FastAPI router ───────────────────────────────────────────────────────────

router = APIRouter(prefix="/tenants", tags=["tenancy-v2"])


class AddMemberRequest(BaseModel):
    email: str
    role: str = "ANALYST"


@router.get("")
def api_list_tenants(
    x_demo_tenant: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
):
    ctx = get_demo_context(x_demo_tenant, x_demo_role)
    require_perm(ctx, "tenant.read")
    return {
        "tenants": list_tenants(),
        "current_tenant_id": ctx["tenant_id"],
        "current_role": ctx["role"],
    }


@router.get("/{tenant_id}/members")
def api_list_members(
    tenant_id: str,
    x_demo_tenant: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
):
    ctx = get_demo_context(x_demo_tenant, x_demo_role)
    require_perm(ctx, "tenant.read")
    try:
        return {"members": list_members(tenant_id), "tenant_id": tenant_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{tenant_id}/members")
def api_add_member(
    tenant_id: str,
    body: AddMemberRequest,
    x_demo_tenant: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
):
    ctx = get_demo_context(x_demo_tenant, x_demo_role)
    require_perm(ctx, "tenant.write")
    try:
        return add_member(tenant_id, body.email, body.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Utility endpoint: resolve current context from headers
@router.get("/~context")
def api_context(
    x_demo_tenant: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
):
    return get_demo_context(x_demo_tenant, x_demo_role)
