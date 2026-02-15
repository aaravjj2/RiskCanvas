"""
Authentication middleware for RiskCanvas API
Supports optional JWT bearer token validation (Azure Entra ID-ready)
"""

import os
import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional


class AuthMiddleware:
    """
    JWT authentication middleware.
    In DEMO mode or when ENABLE_AUTH=false, authentication is disabled.
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        
        # Azure AD configuration
        self.tenant_id = os.getenv("AZURE_AD_TENANT_ID")
        self.client_id = os.getenv("AZURE_AD_CLIENT_ID")
        self.audience = os.getenv("AZURE_AD_AUDIENCE", f"api://{self.client_id}")
        
        # For demo/test: deterministic fake token validation
        self.allow_test_token = self.demo_mode
    
    def is_enabled(self) -> bool:
        """Check if authentication is enabled"""
        return self.enabled and not self.demo_mode
    
    def validate_token(self, token: str) -> dict:
        """
        Validate JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token claims
        
        Raises:
            HTTPException if token invalid
        """
        # In demo mode, accept test token
        if self.allow_test_token and token == "test-token-12345":
            return {
                "sub": "test-user",
                "name": "Test User",
                "roles": ["user"]
            }
        
        if not self.is_enabled():
            # Auth disabled, return empty claims
            return {}
        
        try:
            # Real JWT validation (would use Azure AD public keys in production)
            # For now, decode without verification (placeholder)
            # In production, would use:
            # decoded = jwt.decode(
            #     token,
            #     key=get_azure_ad_public_key(),
            #     algorithms=["RS256"],
            #     audience=self.audience,
            #     issuer=f"https://sts.windows.net/{self.tenant_id}/"
            # )
            
            # Placeholder: decode without verification
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def __call__(self, request: Request):
        """Middleware callable"""
        if not self.is_enabled():
            # Auth disabled, skip
            return
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        # Parse Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format"
            )
        
        token = parts[1]
        
        # Validate token
        claims = self.validate_token(token)
        
        # Attach claims to request state
        request.state.user = claims


# Global auth instance
auth = AuthMiddleware()


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from request state"""
    return getattr(request.state, "user", None)
