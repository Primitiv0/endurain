"""Tests for app/auth/dependencies.py.

Covers all public functions and async dependencies defined in the module.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import auth.dependencies as auth_dependencies
import pytest
from auth.dependencies import (
    AuthContext,
    check_auth_scopes,
    check_scopes,
    get_access_token,
    get_sub_from_access_token,
    get_user_id_from_auth,
    validate_access_token,
    validate_access_token_or_api_key,
    validate_websocket_access_token,
)
from auth.principal import ApiKeyCred, PasswordCred, Principal
from fastapi import HTTPException, WebSocket, status


class TestGetAccessToken:
    """Tests for get_access_token."""

    def test_valid_token_returns_token_string(self):
        result = get_access_token("my-token", "web")
        assert result == "my-token"

    def test_none_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            get_access_token(None, "web")
        assert exc_info.value.status_code == 401
        assert "Access token missing" in exc_info.value.detail


class TestValidateAccessToken:
    """Tests for validate_access_token."""

    @patch("auth.dependencies._resolve_and_cache_principal")
    def test_calls_resolve_and_cache_principal(self, mock_resolve):
        request = MagicMock()
        validate_access_token(request, "token", MagicMock())
        mock_resolve.assert_called_once()


class TestGetSubFromAccessToken:
    """Tests for get_sub_from_access_token."""

    @patch("auth.dependencies._resolve_and_cache_principal")
    def test_returns_user_id(self, mock_resolve):
        principal = Principal(
            user_id=5,
            username="u",
            email="u@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset(),
            credential=PasswordCred(username="u"),
        )
        mock_resolve.return_value = principal
        result = get_sub_from_access_token(MagicMock(), "token", MagicMock())
        assert result == 5


class TestCheckScopes:
    """Tests for check_scopes."""

    @patch("auth.dependencies._resolve_and_cache_principal")
    def test_delegates_to_identity_service_check_scope(self, mock_resolve):
        principal = MagicMock()
        mock_resolve.return_value = principal
        identity_service = MagicMock()
        security_scopes = MagicMock()
        security_scopes.scopes = ["profile"]

        check_scopes(MagicMock(), "token", identity_service, security_scopes)

        identity_service.check_scope.assert_called_once_with(principal, frozenset({"profile"}))


class TestValidateAccessTokenOrApiKey:
    """Tests for validate_access_token_or_api_key."""

    async def test_cached_principal_api_key_returns_auth_context(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        request.state.principal = Principal(
            user_id=3,
            username="apiuser",
            email="api@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset({"read"}),
            credential=ApiKeyCred(api_key_id=1, key_prefix="test"),
        )
        result = await validate_access_token_or_api_key(request, MagicMock())
        assert isinstance(result, AuthContext)
        assert result.user_id == 3
        assert result.auth_type == "api_key"

    async def test_cached_principal_jwt_returns_auth_context(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        request.state.principal = Principal(
            user_id=4,
            username="jwtuser",
            email="jwt@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset({"profile"}),
            credential=PasswordCred(username="jwtuser"),
        )
        result = await validate_access_token_or_api_key(request, MagicMock())
        assert result.auth_type == "jwt"

    async def test_access_token_provided_resolves_via_service(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        identity_service = MagicMock()
        identity_service.resolve_from_access_token.return_value = Principal(
            user_id=7,
            username="tokenuser",
            email="t@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset({"admin"}),
            credential=PasswordCred(username="tokenuser"),
        )
        result = await validate_access_token_or_api_key(
            request,
            identity_service,
            access_token="bearer-token",
        )
        assert result.user_id == 7
        assert result.auth_type == "jwt"
        identity_service.resolve_from_access_token.assert_called_once_with("bearer-token")

    async def test_api_key_header_provided_resolves_via_service(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        identity_service = MagicMock()
        identity_service.resolve_from_api_key.return_value = Principal(
            user_id=8,
            username="keyuser",
            email="k@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset({"read"}),
            credential=ApiKeyCred(api_key_id=2, key_prefix="sk"),
        )
        result = await validate_access_token_or_api_key(
            request,
            identity_service,
            access_token=None,
            api_key_header="sk-123",
            api_key_query=None,
        )
        assert result.user_id == 8
        assert result.auth_type == "api_key"

    async def test_api_key_query_provided_resolves_via_service(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        identity_service = MagicMock()
        identity_service.resolve_from_api_key.return_value = Principal(
            user_id=9,
            username="quser",
            email="q@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset({"read"}),
            credential=ApiKeyCred(api_key_id=3, key_prefix="qk"),
        )
        result = await validate_access_token_or_api_key(
            request,
            identity_service,
            access_token=None,
            api_key_header=None,
            api_key_query="qk-456",
        )
        assert result.user_id == 9
        assert result.auth_type == "api_key"

    async def test_no_credentials_raises_401(self):
        request = MagicMock()
        request.state = SimpleNamespace()
        with pytest.raises(HTTPException) as exc_info:
            await validate_access_token_or_api_key(
                request,
                MagicMock(),
                access_token=None,
                api_key_header=None,
                api_key_query=None,
            )
        assert exc_info.value.status_code == 401


class TestGetUserIdFromAuth:
    """Tests for get_user_id_from_auth."""

    def test_returns_user_id(self):
        auth = AuthContext(user_id=10, scopes=[], auth_type="jwt")
        result = get_user_id_from_auth(auth)
        assert result == 10


class TestCheckAuthScopes:
    """Tests for check_auth_scopes."""

    def test_all_scopes_present_no_exception(self):
        auth = AuthContext(user_id=1, scopes=["profile", "read"], auth_type="jwt")
        security_scopes = MagicMock()
        security_scopes.scopes = ["profile"]
        check_auth_scopes(auth, security_scopes)

    def test_missing_scopes_raises_403(self):
        auth = AuthContext(user_id=1, scopes=["profile"], auth_type="jwt")
        security_scopes = MagicMock()
        security_scopes.scopes = ["profile", "admin"]
        with pytest.raises(HTTPException) as exc_info:
            check_auth_scopes(auth, security_scopes)
        assert exc_info.value.status_code == 403


class TestValidateWebsocketAccessToken:
    """Tests for validate_websocket_access_token."""

    async def test_valid_token_returns_user_id(self):
        identity_service = MagicMock()
        identity_service.resolve_from_access_token.return_value = Principal(
            user_id=42,
            username="wsuser",
            email="ws@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset(),
            credential=PasswordCred(username="wsuser"),
        )
        websocket = MagicMock(spec=WebSocket)
        result = await validate_websocket_access_token(websocket, "valid-token", identity_service)
        assert result == 42

    @patch("auth.dependencies.core_logger.print_to_log")
    async def test_http_exception_logs_warning_and_raises_websocket_exception(self, mock_log):
        identity_service = MagicMock()
        identity_service.resolve_from_access_token.side_effect = HTTPException(
            status_code=401,
            detail="Token expired",
        )
        websocket = MagicMock(spec=WebSocket)
        with pytest.raises(Exception) as exc_info:
            await validate_websocket_access_token(websocket, "bad-token", identity_service)

        from fastapi import WebSocketException

        assert isinstance(exc_info.value, WebSocketException)
        assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION
        mock_log.assert_called_once()


class TestResolveAndCachePrincipal:
    """Tests for _resolve_and_cache_principal."""

    def test_returns_cached_principal(self):
        principal = Principal(
            user_id=1,
            username="u",
            email="u@e.com",
            is_active=True,
            is_superuser=False,
            scopes=frozenset(),
            credential=PasswordCred(username="u"),
        )
        request = MagicMock()
        request.state = SimpleNamespace()
        request.state.principal = principal

        result = auth_dependencies._resolve_and_cache_principal("token", request, MagicMock())
        assert result == principal
