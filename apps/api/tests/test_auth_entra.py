"""
Tests for Azure Entra ID authentication (v2.0+)
Tests DEMO mode, AUTH_MODE=none, and AUTH_MODE=entra (mocked).
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from auth_entra import (
    get_auth_mode,
    get_demo_mode,
    EntraIDValidator,
    validate_auth,
    require_role,
)


class TestAuthMode:
    """Test auth mode detection"""
    
    def test_default_auth_mode_is_none(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_auth_mode() == "none"
    
    def test_auth_mode_entra(self):
        with patch.dict(os.environ, {"AUTH_MODE": "entra"}):
            assert get_auth_mode() == "entra"
    
    def test_demo_mode_false_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_demo_mode() is False
    
    def test_demo_mode_true(self):
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            assert get_demo_mode() is True


class TestValidateAuthDemoMode:
    """Test validate_auth in DEMO mode"""
    
    def test_demo_mode_with_headers(self):
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            result = validate_auth(
                authorization=None,
                x_demo_user="test-user",
                x_demo_role="analyst"
            )
            assert result["username"] == "test-user"
            assert result["role"] == "analyst"
            assert result["auth_mode"] == "demo"
    
    def test_demo_mode_defaults(self):
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            result = validate_auth(
                authorization=None,
                x_demo_user=None,
                x_demo_role=None
            )
            assert result["username"] == "demo-user"
            assert result["role"] == "analyst"
            assert result["auth_mode"] == "demo"


class TestValidateAuthNoneMode:
    """Test validate_auth with AUTH_MODE=none"""
    
    def test_none_mode_with_demo_headers(self):
        with patch.dict(os.environ, {"AUTH_MODE": "none", "DEMO_MODE": "false"}):
            result = validate_auth(
                authorization=None,
                x_demo_user="test-user",
                x_demo_role="viewer"
            )
            assert result["username"] == "test-user"
            assert result["role"] == "viewer"
            assert result["auth_mode"] == "none"
    
    def test_none_mode_anonymous_default(self):
        with patch.dict(os.environ, {"AUTH_MODE": "none", "DEMO_MODE": "false"}):
            result = validate_auth(
                authorization=None,
                x_demo_user=None,
                x_demo_role=None
            )
            assert result["username"] == "anonymous"
            assert result["role"] == "viewer"
            assert result["auth_mode"] == "none"


class TestValidateAuthEntraMode:
    """Test validate_auth with AUTH_MODE=entra (mocked)"""
    
    def test_entra_missing_authorization_header(self):
        with patch.dict(os.environ, {"AUTH_MODE": "entra", "DEMO_MODE": "false"}):
            with pytest.raises(HTTPException) as exc_info:
                validate_auth(
                    authorization=None,
                    x_demo_user=None,
                    x_demo_role=None
                )
            assert exc_info.value.status_code == 401
            assert "Authorization header required" in exc_info.value.detail
    
    def test_entra_invalid_header_format(self):
        with patch.dict(os.environ, {"AUTH_MODE": "entra", "DEMO_MODE": "false"}):
            with pytest.raises(HTTPException) as exc_info:
                validate_auth(
                    authorization="InvalidFormat",
                    x_demo_user=None,
                    x_demo_role=None
                )
            assert exc_info.value.status_code == 401
            assert "Invalid authorization header format" in exc_info.value.detail
    
    @patch('auth_entra.get_entra_validator')
    def test_entra_valid_token(self, mock_get_validator):
        """Test Entra validation with mocked validator"""
        mock_validator = MagicMock()
        mock_validator.validate_token.return_value = {
            "sub": "user123",
            "preferred_username": "test@example.com",
            "roles": ["RiskCanvas.Analyst"]
        }
        mock_validator.extract_username.return_value = "test@example.com"
        mock_validator.extract_role.return_value = "analyst"
        mock_get_validator.return_value = mock_validator
        
        with patch.dict(os.environ, {"AUTH_MODE": "entra", "DEMO_MODE": "false"}):
            result = validate_auth(
                authorization="Bearer fake_token_123",
                x_demo_user=None,
                x_demo_role=None
            )
            
            assert result["username"] == "test@example.com"
            assert result["role"] == "analyst"
            assert result["auth_mode"] == "entra"
            assert "claims" in result
            
            # Verify validator was called
            mock_validator.validate_token.assert_called_once_with("fake_token_123")


class TestEntraIDValidator:
    """Test EntraIDValidator class"""
    
    def test_init_with_tenant_id(self):
        with patch.dict(os.environ, {
            "AZURE_TENANT_ID": "test-tenant",
            "AZURE_CLIENT_ID": "test-client"
        }):
            validator = EntraIDValidator()
            assert validator.tenant_id == "test-tenant"
            assert validator.client_id == "test-client"
            assert validator.issuer == "https://login.microsoftonline.com/test-tenant/v2.0"
    
    def test_init_no_config(self):
        with patch.dict(os.environ, {}, clear=True):
            validator = EntraIDValidator()
            assert validator.tenant_id is None
            assert validator.jwks_client is None
    
    def test_extract_role_from_roles_claim(self):
        validator = EntraIDValidator()
        claims = {"roles": ["RiskCanvas.Admin"]}
        assert validator.extract_role(claims) == "admin"
    
    def test_extract_role_from_groups_claim(self):
        validator = EntraIDValidator()
        claims = {"groups": ["RiskCanvas.Viewer"]}
        assert validator.extract_role(claims) == "viewer"
    
    def test_extract_role_default_to_viewer(self):
        validator = EntraIDValidator()
        claims = {}
        assert validator.extract_role(claims) == "viewer"
    
    def test_extract_role_mapping(self):
        validator = EntraIDValidator()
        assert validator.extract_role({"roles": ["Admin"]}) == "admin"
        assert validator.extract_role({"roles": ["Analyst"]}) == "analyst"
        assert validator.extract_role({"roles": ["Viewer"]}) == "viewer"
    
    def test_extract_username_preferred_username(self):
        validator = EntraIDValidator()
        claims = {"preferred_username": "user@example.com"}
        assert validator.extract_username(claims) == "user@example.com"
    
    def test_extract_username_fallback(self):
        validator = EntraIDValidator()
        claims = {"email": "user@example.com"}
        assert validator.extract_username(claims) == "user@example.com"
    
    def test_extract_username_default(self):
        validator = EntraIDValidator()
        claims = {}
        assert validator.extract_username(claims) == "unknown"


class TestRequireRole:
    """Test role-based authorization"""
    
    def test_viewer_has_viewer_permission(self):
        user_context = {"role": "viewer"}
        require_role(user_context, "viewer")  # Should not raise
    
    def test_analyst_has_viewer_permission(self):
        user_context = {"role": "analyst"}
        require_role(user_context, "viewer")  # Should not raise
    
    def test_analyst_has_analyst_permission(self):
        user_context = {"role": "analyst"}
        require_role(user_context, "analyst")  # Should not raise
    
    def test_admin_has_all_permissions(self):
        user_context = {"role": "admin"}
        require_role(user_context, "viewer")  # Should not raise
        require_role(user_context, "analyst")  # Should not raise
        require_role(user_context, "admin")  # Should not raise
    
    def test_viewer_lacks_analyst_permission(self):
        user_context = {"role": "viewer"}
        with pytest.raises(HTTPException) as exc_info:
            require_role(user_context, "analyst")
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
    
    def test_viewer_lacks_admin_permission(self):
        user_context = {"role": "viewer"}
        with pytest.raises(HTTPException) as exc_info:
            require_role(user_context, "admin")
        assert exc_info.value.status_code == 403
    
    def test_analyst_lacks_admin_permission(self):
        user_context = {"role": "analyst"}
        with pytest.raises(HTTPException) as exc_info:
            require_role(user_context, "admin")
        assert exc_info.value.status_code == 403


class TestIntegration:
    """Integration tests for auth flow"""
    
    def test_demo_mode_takes_precedence_over_auth_mode(self):
        """DEMO mode should override AUTH_MODE"""
        with patch.dict(os.environ, {"DEMO_MODE": "true", "AUTH_MODE": "entra"}):
            result = validate_auth(
                authorization="Bearer fake_token",
                x_demo_user="demo-user",
                x_demo_role="analyst"
            )
            # Should use demo mode, not attempt entra validation
            assert result["auth_mode"] == "demo"
            assert result["username"] == "demo-user"
    
    def test_complete_auth_flow_demo(self):
        """Test complete auth flow in DEMO mode"""
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            # Validate
            user_context = validate_auth(
                authorization=None,
                x_demo_user="analyst-user",
                x_demo_role="analyst"
            )
            
            # Check permissions
            require_role(user_context, "viewer")  # Should pass
            require_role(user_context, "analyst")  # Should pass
            
            # Should fail for admin
            with pytest.raises(HTTPException):
                require_role(user_context, "admin")
