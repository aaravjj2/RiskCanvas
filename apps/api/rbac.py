"""
RBAC (Role-Based Access Control) module for v1.4
Provides role validation and permission checking.
Supports both DEMO mode (deterministic headers) and PROD mode (optional auth).
"""

import os
from typing import Optional
from fastapi import Header, HTTPException


# Role hierarchy
ROLES = ["viewer", "analyst", "admin"]
ROLE_PERMISSIONS = {
    "viewer": ["read"],
    "analyst": ["read", "write", "execute"],
    "admin": ["read", "write", "execute", "delete", "admin"]
}

def get_demo_mode() -> bool:
    """Check if DEMO mode is enabled"""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def get_user_context(
    x_demo_user: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None)
) -> dict:
    """
    Extract user context from headers.
    
    DEMO mode (DEMO_MODE=true):
    - Uses X-Demo-User and X-Demo-Role headers
    - Defaults to demo-user/analyst if not provided
    - Deterministic behavior for testing
    
    PROD mode (DEMO_MODE=false):
    - Optionally accepts X-Demo-* headers (for backward compat)
    - Otherwise uses Authorization bearer token (not yet implemented)
    - Falls back to anonymous/viewer for unauthenticated requests
    """
    demo_mode = get_demo_mode()
    
    if demo_mode:
        # DEMO mode: use demo headers with defaults
        user = x_demo_user or "demo-user"
        role = (x_demo_role or "analyst").lower()
    else:
        # PROD mode: accept demo headers if provided, else use auth
        if x_demo_user and x_demo_role:
            user = x_demo_user
            role = x_demo_role.lower()
        elif authorization:
            # TODO: Parse JWT token and extract user/role
            # For now, treat as admin
            user = "authenticated-user"
            role = "admin"
        else:
            # Unauthenticated: minimal permissions
            user = "anonymous"
            role = "viewer"
    
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}. Must be one of {ROLES}")
    
    return {
        "user": user,
        "role": role,
        "permissions": ROLE_PERMISSIONS[role],
        "demo_mode": demo_mode
    }


# Alias for backward compatibility
get_demo_user_context = get_user_context


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
