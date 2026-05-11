"""Authentication package.

Provides the FastAPI router, JWT token issuance and validation,
password hashing, scope enforcement, API-key validation, and the
progressive-lockout stores used during login and MFA verification.

Persistence-bearing concerns (identity providers, IdP link tokens,
MFA backup codes, OAuth state) live in dedicated sub-packages and
expose their own models, schemas, and CRUD modules.

Exports:
    - Password hashing: ``PasswordHasher``, ``PasswordPolicyError``,
      ``get_password_hasher``
    - JWT: ``TokenManager``, ``TokenType``, ``get_token_manager``
    - Security dependencies: ``AuthContext``, ``oauth2_scheme``,
      ``validate_access_token``, ``validate_refresh_token``,
      ``check_scopes``, ``check_auth_scopes``,
      ``get_sub_from_access_token``, ``get_sid_from_access_token``,
      ``get_sub_from_refresh_token``, ``get_sid_from_refresh_token``,
      ``validate_access_token_or_api_key``,
      ``validate_websocket_access_token``,
      ``header_client_type_scheme``, ``header_csrf_token_scheme``
    - Schemas: ``LoginRequest``, ``MFALoginRequest``,
      ``MFARequiredResponse``, ``MobileSessionResponse``,
      ``TokenResponseWeb``, ``TokenResponseMobile``,
      ``LogoutResponse``
    - Stores: ``PendingMFALogin``, ``RedisPendingMFALogin``,
      ``FailedLoginAttempts``, ``RedisFailedLoginAttempts``,
      ``get_pending_mfa_store``, ``get_failed_login_attempts``,
      ``cleanup_expired_pending_mfa_logins``,
      ``clear_pending_mfa_for_user``
    - Helpers: ``authenticate_user``, ``complete_login``,
      ``create_tokens``, ``create_mobile_pkce_session_response``
"""

from .password_hasher import (
    PasswordHasher,
    PasswordPolicyError,
    get_password_hasher,
)
from .schema import (
    LoginRequest,
    LogoutResponse,
    MFALoginRequest,
    MFARequiredResponse,
    MobileSessionResponse,
    TokenResponseMobile,
    TokenResponseWeb,
)
from .security_stores import (
    FailedLoginAttempts,
    PendingMFALogin,
    RedisFailedLoginAttempts,
    RedisPendingMFALogin,
    cleanup_expired_pending_mfa_logins,
    clear_pending_mfa_for_user,
    create_auth_security_stores,
    get_failed_login_attempts,
    get_pending_mfa_store,
)
from .security import (
    AuthContext,
    check_auth_scopes,
    check_scopes,
    get_sid_from_access_token,
    get_sid_from_refresh_token,
    get_sub_from_access_token,
    get_sub_from_refresh_token,
    header_client_type_scheme,
    header_csrf_token_scheme,
    oauth2_scheme,
    validate_access_token,
    validate_access_token_or_api_key,
    validate_refresh_token,
    validate_websocket_access_token,
)
from .token_manager import TokenManager, TokenType, get_token_manager
from .utils import (
    authenticate_user,
    complete_login,
    create_mobile_pkce_session_response,
    create_tokens,
)

__all__ = [
    # Password hashing
    "PasswordHasher",
    "PasswordPolicyError",
    "get_password_hasher",
    # JWT / token management
    "TokenManager",
    "TokenType",
    "get_token_manager",
    # Security dependencies
    "AuthContext",
    "oauth2_scheme",
    "header_client_type_scheme",
    "header_csrf_token_scheme",
    "validate_access_token",
    "validate_refresh_token",
    "validate_access_token_or_api_key",
    "validate_websocket_access_token",
    "check_scopes",
    "check_auth_scopes",
    "get_sub_from_access_token",
    "get_sid_from_access_token",
    "get_sub_from_refresh_token",
    "get_sid_from_refresh_token",
    # Schemas
    "LoginRequest",
    "MFALoginRequest",
    "MFARequiredResponse",
    "MobileSessionResponse",
    "TokenResponseWeb",
    "TokenResponseMobile",
    "LogoutResponse",
    # Auth security stores / lockout
    "PendingMFALogin",
    "RedisPendingMFALogin",
    "FailedLoginAttempts",
    "RedisFailedLoginAttempts",
    "create_auth_security_stores",
    "get_pending_mfa_store",
    "get_failed_login_attempts",
    "cleanup_expired_pending_mfa_logins",
    "clear_pending_mfa_for_user",
    # Helpers
    "authenticate_user",
    "complete_login",
    "create_tokens",
    "create_mobile_pkce_session_response",
]
