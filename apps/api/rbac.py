"""
RBAC (Role-Based Access Control) module for v1.4
Provides role validation and permission checking.
"""

from typing import Optional
from fastapi import Header, HTTPException


# Role hierarchy
ROLES = ["viewer", "analyst", "admin"]
ROLE_PERMISSIONS = {
    "viewer": ["read"],
    "analyst": ["read", "write", "execute"],
    "admin": ["read", "write", "execute", "delete", "admin"]
}


def get_demo_user_context(
    x_demo_user: Optional[str] = Header(default="demo-user"),
    x_demo_role: Optional[str] = Header(default="analyst")
) -> dict:
    """
    Extract user context from demo headers.
    In DEMO mode, we use deterministic headers.
    In PROD, this would validate JWT and extract claims.
    """
    role = x_demo_role.lower()
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}. Must be one of {ROLES}")
    
    return {
        "user": x_demo_user,
        "role": role,
        "permissions": ROLE_PERMISSIONS[role]
    }


def require_permission(user_context: dict, permission: str):
    """Check if user has required permission"""
    if permission not in user_context["permissions"]:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied. Required: {permission}, User role: {user_context['role']}"
        )


def require_role(user_context: dict, min_role: str):
    """Check if user has at least the specified role"""
    user_role = user_context["role"]
    try:
        user_idx = ROLES.index(user_role)
        min_idx = ROLES.index(min_role)
        if user_idx < min_idx:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role. Required: {min_role}, User role: {user_role}"
            )
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {min_role}")
