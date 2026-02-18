"""
Azure Entra ID (Azure AD) JWT validation for RiskCanvas v2.0+
Supports DEMO mode (no validation) and PROD mode (Entra ID JWT validation).
"""

import os
try:
    import jwt
    from jwt import PyJWKClient
except ImportError:
    # PyJWT not installed, will fail in real mode
    jwt = None
    PyJWKClient = None
from typing import Optional, Dict, Any
from fastapi import HTTPException, Header
from datetime import datetime


def get_auth_mode() -> str:
    """Get authentication mode: 'none', 'entra'"""
    return os.getenv("AUTH_MODE", "none").lower()


def get_demo_mode() -> bool:
    """Check if DEMO mode is enabled (takes precedence over auth)"""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


class EntraIDValidator:
    """Azure Entra ID JWT validator"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.audience = os.getenv("AUTH_AUDIENCE", self.client_id)
        self.issuer = os.getenv("AUTH_ISSUER")
        
        if not self.issuer and self.tenant_id:
            self.issuer = f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
        
        self.jwks_client = None
        if self.tenant_id:
            jwks_uri = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            self.jwks_client = PyJWKClient(jwks_uri)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.
        Raises HTTPException if validation fails.
        """
        if not self.jwks_client:
            raise HTTPException(
                status_code=500,
                detail="Entra ID not configured (missing AZURE_TENANT_ID)"
            )
        
        try:
            # Get signing key
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Verify and decode token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidAudienceError:
            raise HTTPException(status_code=401, detail="Invalid audience")
        except jwt.InvalidIssuerError:
            raise HTTPException(status_code=401, detail="Invalid issuer")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")
    
    def extract_role(self, claims: Dict[str, Any]) -> str:
        """
        Extract role from JWT claims.
        Maps Entra ID roles to RiskCanvas roles (viewer/analyst/admin).
        """
        # Check common claim locations
        roles = claims.get("roles", [])
        if not roles:
            roles = claims.get("groups", [])
        if not roles:
            # Check app-specific claims
            roles = claims.get("extension_RiskCanvasRole", [])
        
        # Map to RiskCanvas roles (first match wins)
        role_mapping = {
            "RiskCanvas.Admin": "admin",
            "RiskCanvas.Analyst": "analyst",
            "RiskCanvas.Viewer": "viewer",
            "Admin": "admin",
            "Analyst": "analyst",
            "Viewer": "viewer",
        }
        
        for role in roles if isinstance(roles, list) else [roles]:
            mapped = role_mapping.get(role)
            if mapped:
                return mapped
        
        # Default to viewer if no role found
        return "viewer"
    
    def extract_username(self, claims: Dict[str, Any]) -> str:
        """Extract username from JWT claims"""
        # Try common claim locations
        return (
            claims.get("preferred_username") or
            claims.get("upn") or
            claims.get("email") or
            claims.get("sub") or
            "unknown"
        )


# Global validator instance (lazy init)
_entra_validator: Optional[EntraIDValidator] = None


def get_entra_validator() -> EntraIDValidator:
    """Get or create Entra ID validator instance"""
    global _entra_validator
    if _entra_validator is None:
        _entra_validator = EntraIDValidator()
    return _entra_validator


def validate_auth(
    authorization: Optional[str] = Header(default=None),
    x_demo_user: Optional[str] = Header(default=None),
    x_demo_role: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """
    Validate authentication and return user context.
    
    Modes:
    1. DEMO mode (DEMO_MODE=true): Use demo headers, no validation
    2. AUTH_MODE=none: No authentication, use demo headers or anonymous
    3. AUTH_MODE=entra: Validate Entra ID JWT
    
    Returns:
        dict with keys: username, role, claims (if available)
    """
    demo_mode = get_demo_mode()
    auth_mode = get_auth_mode()
    
    # DEMO mode: always use demo headers
    if demo_mode:
        return {
            "username": x_demo_user or "demo-user",
            "role": (x_demo_role or "analyst").lower(),
            "auth_mode": "demo",
            "claims": {}
        }
    
    # AUTH_MODE=none: no authentication required
    if auth_mode == "none":
        # Allow demo headers for backward compat
        if x_demo_user or x_demo_role:
            return {
                "username": x_demo_user or "anonymous",
                "role": (x_demo_role or "viewer").lower(),
                "auth_mode": "none",
                "claims": {}
            }
        # Default to anonymous viewer
        return {
            "username": "anonymous",
            "role": "viewer",
            "auth_mode": "none",
            "claims": {}
        }
    
    # AUTH_MODE=entra: validate JWT
    if auth_mode == "entra":
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Authorization header required (Bearer token)"
            )
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format (expected 'Bearer <token>')"
            )
        
        token = authorization[7:]  # Remove "Bearer " prefix
        validator = get_entra_validator()
        claims = validator.validate_token(token)
        
        return {
            "username": validator.extract_username(claims),
            "role": validator.extract_role(claims),
            "auth_mode": "entra",
            "claims": claims
        }
    
    # Unknown auth mode
    raise HTTPException(
        status_code=500,
        detail=f"Unknown AUTH_MODE: {auth_mode}"
    )


def require_role(user_context: Dict[str, Any], required_role: str) -> None:
    """
    Check if user has required role.
    Raises HTTPException if not authorized.
    
    Role hierarchy: viewer < analyst < admin
    """
    role_hierarchy = ["viewer", "analyst", "admin"]
    user_role = user_context.get("role", "viewer")
    
    try:
        user_level = role_hierarchy.index(user_role)
        required_level = role_hierarchy.index(required_role)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid role")
    
    if user_level < required_level:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions (required: {required_role}, have: {user_role})"
        )


def require_permission(user_context: Dict[str, Any], permission: str) -> None:
    """
    Check if user has required permission.
    Maps permissions to role requirements.
    
    Permission -> Required Role:
    - read: viewer+
    - write: analyst+
    - execute: analyst+
    - delete: admin
    - admin: admin
    """
    permission_role_map = {
        "read": "viewer",
        "write": "analyst",
        "execute": "analyst",
        "delete": "admin",
        "admin": "admin"
    }
    
    required_role = permission_role_map.get(permission)
    if not required_role:
        raise HTTPException(status_code=400, detail=f"Unknown permission: {permission}")
    
    require_role(user_context, required_role)
