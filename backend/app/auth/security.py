"""Authentication dependencies and helpers for the auth module.

Provides FastAPI dependencies that resolve and validate JWT access/refresh
tokens (cookie or Authorization header), enforce OAuth2 scopes, accept API
keys as an alternative credential, and validate WebSocket access tokens.
Defines :class:`AuthContext`, the unified credential representation passed
to endpoints that accept either auth method.
"""

from dataclasses import dataclass
from typing import Annotated
from fastapi import (
    Depends,
    HTTPException,
    Query,
    Request,
    status,
    WebSocket,
    WebSocketException,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
    APIKeyHeader,
    APIKeyCookie,
)

import auth.constants as auth_constants
import auth.identity_service as auth_identity_service
import auth.token_manager as auth_token_manager
import auth.utils as auth_utils

from auth.principal import AccessTokenCred, Principal
from joserfc.errors import MissingClaimError

import core.logger as core_logger

# Define the OAuth2 scheme for handling bearer tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes=auth_constants.SCOPE_DICT,
    auto_error=False,
)

# Define the API key header for the client type
header_client_type_scheme = APIKeyHeader(name="X-Client-Type")

# Define the API key header for third-party API key auth
header_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class AuthContext:
    """
    Unified authentication context.

    Carries the resolved user identity and scopes
    regardless of whether authentication was via JWT
    or API key.

    Attributes:
        user_id: Authenticated user's ID.
        scopes: List of granted scope strings.
        auth_type: Source of authentication
            (``"jwt"`` or ``"api_key"``).
    """

    user_id: int
    scopes: list[str]
    auth_type: str


# Define the API key header for the client type for OAuth redirects
header_client_type_scheme_optional = APIKeyHeader(
    name="X-Client-Type", auto_error=False
)

# Define the API key header for CSRF token
header_csrf_token_scheme = APIKeyHeader(name="X-CSRF-Token", auto_error=False)

# Define the API key cookie for the refresh token
cookie_refresh_token_scheme = APIKeyCookie(
    name="endurain_refresh_token",
    auto_error=False,
)


def _resolve_and_cache_principal(
    access_token: str,
    request: Request,
    identity_service: auth_identity_service.IdentityService,
) -> Principal:
    """Resolve and cache a Principal from a JWT access token.

    Checks ``request.state.principal`` first so that multiple
    dependencies in the same request share a single DB lookup.
    On cache miss, delegates to
    :meth:`~auth.identity_service.IdentityService.resolve_from_access_token`
    and stores the result on ``request.state``.

    Args:
        access_token: Raw JWT access token string.
        request: Current HTTP request used for caching.
        identity_service: Per-request IdentityService.

    Returns:
        Principal: Cached or freshly-resolved principal.

    Raises:
        HTTPException: 401 if the token is invalid or
            the user is not found.
    """
    cached: Principal | None = getattr(
        request.state, "principal", None
    )
    if cached is not None:
        return cached
    principal = identity_service.resolve_from_access_token(
        access_token
    )
    request.state.principal = principal
    return principal


def get_token(
    non_cookie_token: Annotated[str | None, Depends(oauth2_scheme)],
    cookie_token: str | None,
    client_type: str,
    token_type: str,
) -> str | None:
    """
    Retrieves the authentication token based on client type and token type.

    Args:
        non_cookie_token (str | None): Token provided via Authorization header.
        cookie_token (str | None): Token provided via cookie.
        client_type (str): Type of client requesting the token ("web" or "mobile").
        token_type (str): Type of token being requested ("access" or "refresh").

    Returns:
        str: The authentication token appropriate for the client type and token type.

    Raises:
        HTTPException: If the required token is missing, or if the client type is invalid.
    """
    # OAuth 2.1: Access tokens always come from Authorization header (all clients)
    if token_type == "access":
        if non_cookie_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token missing from Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return non_cookie_token

    # Refresh tokens: cookie (web) or Authorization header (mobile)
    if token_type == "refresh":
        if client_type == "web":
            if cookie_token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token missing from cookie",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return cookie_token
        if client_type == "mobile":
            if non_cookie_token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token missing from Authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return non_cookie_token

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid client type or token type",
        headers={"WWW-Authenticate": "Bearer"},
    )


## ACCESS TOKEN VALIDATION
def get_access_token(
    access_token: Annotated[str | None, Depends(oauth2_scheme)],
    client_type: str = Depends(header_client_type_scheme),
) -> str | None:
    """
    Retrieves the access token from the Authorization header.

    Args:
        access_token (str | None): Access token provided via the Authorization header (OAuth2 scheme).
        client_type (str): The type of client making the request, extracted from a custom header.

    Returns:
        str: The access token from the Authorization header.

    Raises:
        HTTPException: If the access token is missing from the Authorization header.
    """
    return get_token(access_token, None, client_type, "access")


def get_access_token_for_browser_redirect(
    access_token: Annotated[str | None, Depends(oauth2_scheme)],
    client_type: str | None = Depends(header_client_type_scheme_optional),
) -> str | None:
    """
    Retrieve the access token for browser redirect scenarios.

    Args:
        access_token (str | None): The access token from the Authorization header
            or query parameter, extracted via OAuth2 scheme dependency.
        client_type (str | None, optional): The type of client making the request
            (e.g., "web", "mobile"). Defaults to "web" if not provided, as browser
            redirects typically originate from web clients.

    Returns:
        str | None: The access token if found and valid, None otherwise.

    Note:
        This function defaults client_type to "web" when None is provided,
        specifically to handle OAuth redirect scenarios where the client type
        may not be explicitly specified.
    """
    if client_type is None:
        client_type = "web"

    return get_token(
        access_token,
        None,
        client_type,
        "access",
    )


def _validate_access_token_impl(
    access_token: str,
    token_manager: auth_token_manager.TokenManager,
) -> None:
    """Shared implementation for access-token validation.

    Args:
        access_token: The access token to validate.
        token_manager: The configured token manager.

    Raises:
        HTTPException: If the token is missing claims, expired, or otherwise
            invalid. Unexpected exceptions are not caught here so the global
            error handler can record them.
    """
    try:
        token_manager.validate_token_expiration(
            access_token,
            auth_token_manager.TokenType.ACCESS,
        )
    except HTTPException as http_err:
        log_level = "debug" if "expired" in http_err.detail.lower() else "error"
        core_logger.print_to_log(
            f"Access token validation failed: {http_err.detail}",
            log_level,
            exc=http_err,
            context={"access_token": "[REDACTED]"},
        )
        raise


def validate_access_token(
    access_token: Annotated[str, Depends(get_access_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> None:
    """FastAPI dependency that validates the access token from the
    Authorization header.

    Args:
        access_token (str): The access token to be validated.
        token_manager (auth_token_manager.TokenManager): The token manager instance used for validation.

    Raises:
        HTTPException: If the token is expired or invalid.
    """
    _validate_access_token_impl(access_token, token_manager)


def validate_access_token_for_browser_redirect(
    access_token: Annotated[str, Depends(get_access_token_for_browser_redirect)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> None:
    """FastAPI dependency that validates the access token for browser-redirect
    flows where ``X-Client-Type`` may be absent.

    Args:
        access_token (str): The access token to be validated.
        token_manager (auth_token_manager.TokenManager): The token manager instance used for validation.

    Raises:
        HTTPException: If the token is expired or invalid.
    """
    _validate_access_token_impl(access_token, token_manager)


def get_sub_from_access_token(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
) -> int:
    """Retrieve the user ID from the access token.

    Resolves and caches the :class:`~auth.principal.Principal`
    on ``request.state`` then returns ``principal.user_id``.
    Subsequent calls within the same request hit the cache
    instead of issuing another DB lookup.

    Args:
        request: Current HTTP request for state caching.
        access_token: JWT from the Authorization header.
        identity_service: Per-request IdentityService.

    Returns:
        int: Authenticated user's primary key.

    Raises:
        HTTPException: 401 if the token is invalid,
            expired, or the user is not found.
    """
    principal = _resolve_and_cache_principal(
        access_token, request, identity_service
    )
    return principal.user_id


def get_sub_from_access_token_for_browser_redirect(
    request: Request,
    access_token: Annotated[
        str, Depends(get_access_token_for_browser_redirect)
    ],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
) -> int:
    """Retrieve the user ID from an access token for browser-redirect flows.

    Resolves and caches the :class:`~auth.principal.Principal`
    on ``request.state``; uses the browser-redirect token
    extractor that tolerates a missing ``X-Client-Type`` header.

    Args:
        request: Current HTTP request for state caching.
        access_token: JWT from the Authorization header or
            browser-redirect flow.
        identity_service: Per-request IdentityService.

    Returns:
        int: Authenticated user's primary key.

    Raises:
        HTTPException: 401 if the token is invalid,
            expired, or the user is not found.
    """
    principal = _resolve_and_cache_principal(
        access_token, request, identity_service
    )
    return principal.user_id


def get_sid_from_access_token(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
) -> str:
    """Retrieve the session ID from the access token.

    Resolves and caches the :class:`~auth.principal.Principal`
    on ``request.state`` then extracts the session ID from the
    :class:`~auth.principal.AccessTokenCred`.

    Args:
        request: Current HTTP request for state caching.
        access_token: JWT from the Authorization header.
        identity_service: Per-request IdentityService.

    Returns:
        str: Session ID (``sid`` claim) from the token.

    Raises:
        HTTPException: 401 if the token is invalid,
            expired, or the credential type is unexpected.
    """
    principal = _resolve_and_cache_principal(
        access_token, request, identity_service
    )
    cred = principal.credential
    if not isinstance(cred, AccessTokenCred):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credential type for session ID",
        )
    return cred.session_id


def get_and_return_access_token(
    access_token: Annotated[str, Depends(get_access_token)],
) -> str:
    """
    Retrieves and returns the access token from the request dependencies.

    Args:
        access_token (str): The access token extracted via dependency injection.

    Returns:
        str: The access token.
    """
    # Return token
    return access_token


## REFRESH TOKEN VALIDATION
def get_refresh_token(
    non_cookie_refresh_token: Annotated[str | None, Depends(oauth2_scheme)],
    cookie_refresh_token: str | None = Depends(cookie_refresh_token_scheme),
    client_type: str = Depends(header_client_type_scheme),
) -> str | None:
    """
    Retrieves the refresh token from either the Authorization header or a cookie, depending on the client type.

    Args:
        non_cookie_refresh_token (str | None): The refresh token provided via the Authorization header (if present).
        cookie_refresh_token (str | None): The refresh token provided via a cookie (if present).
        client_type (str): The type of client making the request, extracted from the request headers.

    Returns:
        str: The resolved refresh token based on the provided sources and client type.

    Raises:
        HTTPException: If no valid refresh token is found or the client type is invalid.
    """
    return get_token(
        non_cookie_refresh_token, cookie_refresh_token, client_type, "refresh"
    )


def validate_refresh_token(
    refresh_token: Annotated[str, Depends(get_refresh_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> None:
    """
    Validates the expiration of a refresh token using the provided token manager.

    Args:
        refresh_token (str): The refresh token to be validated, extracted via dependency injection.
        token_manager (auth_token_manager.TokenManager): The token manager instance used to validate the token, injected via dependency.

    Raises:
        HTTPException: If the refresh token is expired or invalid, or if an unexpected error occurs during validation.

    Logs:
        Errors and unexpected exceptions are logged with context, including a redacted refresh token.
    """
    try:
        # Validate the token expiration and type
        token_manager.validate_token_expiration(
            refresh_token,
            auth_token_manager.TokenType.REFRESH,
        )
    except HTTPException as http_err:
        log_level = "debug" if "expired" in http_err.detail.lower() else "error"
        core_logger.print_to_log(
            f"Refresh token validation failed: {http_err.detail}",
            log_level,
            exc=http_err,
            context={"refresh_token": "[REDACTED]"},
        )
        # If a pre-upgrade token (e.g. missing the ``typ`` claim) reaches
        # this point the SPA would otherwise loop forever: every page load
        # would resend the same stale cookie, refresh would 401, and the
        # client would never recover. A custom exception handler clears
        # both the legacy root-scoped cookie and the current auth-scoped
        # cookie using separate Set-Cookie headers. We only do this for
        # ``MissingClaimError``-style failures to avoid logging users out
        # on transient issues.
        if isinstance(http_err.__cause__, MissingClaimError):
            raise auth_utils.ClearRefreshTokenCookieHTTPException(
                status_code=http_err.status_code,
                detail=http_err.detail,
                headers=http_err.headers,
            ) from http_err
        raise


def get_sub_from_refresh_token(
    refresh_token: Annotated[str, Depends(get_refresh_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> int:
    """
    Retrieves the user ID ('sub' claim) from a given refresh token.

    Args:
        refresh_token (str): The refresh token from which to extract the user ID.
        token_manager (auth_token_manager.TokenManager): The token manager instance used to validate and parse the token.

    Returns:
        int: The user ID associated with the provided refresh token.

    Raises:
        Exception: If the token is invalid or the 'sub' claim is not found.
    """
    # Return the user ID associated with the token
    sub = token_manager.get_token_claim(refresh_token, "sub")
    if not isinstance(sub, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sub' claim must be an integer",
        )
    return sub


def get_sid_from_refresh_token(
    refresh_token: Annotated[str, Depends(get_refresh_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> str:
    """
    Retrieves the session ID ('sid') from a given refresh token.

    Args:
        refresh_token (str): The refresh token from which to extract the session ID.
        token_manager (auth_token_manager.TokenManager): The token manager used to validate and extract claims from the token.

    Returns:
        str: The session ID associated with the provided refresh token.

    Raises:
        Exception: If the token is invalid or the 'sid' claim is not present.
    """
    # Return the session ID associated with the token
    sid = token_manager.get_token_claim(refresh_token, "sid")
    if not isinstance(sid, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sid' claim must be a string",
        )
    return sid


def get_and_return_refresh_token(
    refresh_token: Annotated[str, Depends(get_refresh_token)],
) -> str:
    """
    Retrieves and returns the refresh token from the request dependencies.

    Args:
        refresh_token (str): The refresh token extracted via dependency injection.

    Returns:
        str: The provided refresh token.
    """
    # Return token
    return refresh_token


def _check_scopes_impl(
    access_token: str,
    token_manager: auth_token_manager.TokenManager,
    security_scopes: SecurityScopes,
) -> None:
    """Shared implementation for scope enforcement.

    Defence-in-depth: validates token type and expiration before
    inspecting scopes. Without this, refresh tokens (which carry
    the same ``scope`` claim) would satisfy scope-gated routes,
    and expired access tokens would still authorise requests on
    routers that omit an explicit ``validate_access_token``
    dependency.

    Args:
        access_token: The access token to inspect.
        token_manager: The configured token manager.
        security_scopes: Required scopes for the protected endpoint.

    Raises:
        HTTPException: 401 if the token is expired or of the wrong
            type. 403 if the ``scope`` claim is malformed or any
            required scope is missing.
    """
    _validate_access_token_impl(access_token, token_manager)
    scope = token_manager.get_token_claim(access_token, "scope")

    if not isinstance(scope, list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access - Invalid scope format",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'},
        )

    missing_scopes = set(security_scopes.scopes) - set(scope)
    if missing_scopes:
        core_logger.print_to_log(
            f"Scope validation failed: missing {missing_scopes}",
            "error",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized Access - Missing permissions: {missing_scopes}",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'},
        )


def check_scopes(
    access_token: Annotated[str, Depends(get_access_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
    security_scopes: SecurityScopes,
) -> None:
    """
    Validates that the access token contains all required security scopes.

    Args:
        access_token (str): The access token extracted from the request.
        token_manager (auth_token_manager.TokenManager): Instance responsible
            for managing and validating tokens.
        security_scopes (SecurityScopes): Required scopes for the endpoint.

    Raises:
        HTTPException: 403 if any required scope is missing or scope is
            malformed.
    """
    _check_scopes_impl(access_token, token_manager, security_scopes)


def check_scopes_for_browser_redirect(
    access_token: Annotated[str, Depends(get_access_token_for_browser_redirect)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
    security_scopes: SecurityScopes,
) -> None:
    """
    Validates that the access token contains all required security scopes for
    browser redirection.

    Args:
        access_token (str): The access token extracted from the request.
        token_manager (auth_token_manager.TokenManager): Instance responsible
            for managing and validating tokens.
        security_scopes (SecurityScopes): Required scopes for the endpoint.

    Raises:
        HTTPException: 403 if any required scope is missing or scope is
            malformed.
    """
    _check_scopes_impl(access_token, token_manager, security_scopes)


## API KEY + UNIFIED AUTH
async def validate_api_key(
    raw_key: str,
    request: Request,
    identity_service: auth_identity_service.IdentityService,
) -> "AuthContext":
    """Validate a raw API key and return an AuthContext.

    Delegates to
    :meth:`~auth.identity_service.IdentityService.resolve_from_api_key`
    and wraps the returned
    :class:`~auth.principal.Principal` in an
    :class:`AuthContext` for backward compatibility.

    Args:
        raw_key: The plain-text API key from the
            request header or query parameter.
        request: The current HTTP request (for audit
            logging and state caching).
        identity_service: Per-request IdentityService.

    Returns:
        AuthContext with user_id, scopes, and
        auth_type set to ``"api_key"``.

    Raises:
        HTTPException: 401 if the key is not found,
            revoked, or expired.
    """
    principal = identity_service.resolve_from_api_key(raw_key, request)
    return AuthContext(
        user_id=principal.user_id,
        scopes=list(principal.scopes),
        auth_type="api_key",
    )


async def validate_access_token_or_api_key(
    request: Request,
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
    access_token: str | None = Depends(oauth2_scheme),
    api_key_header: str | None = Depends(header_api_key_scheme),
    api_key_query: str | None = Query(None, alias="api_key"),
) -> "AuthContext":
    """Accept either a JWT bearer token or an API key.

    Tries JWT first (Authorization: Bearer header). If none
    is present, falls back to the ``X-API-Key`` header, then
    the ``?api_key=`` query parameter. Raises 401 if neither
    is supplied.

    Delegates to :class:`~auth.identity_service.IdentityService`
    for credential resolution and caches the resolved
    :class:`~auth.principal.Principal` on
    ``request.state.principal`` so that other dependencies in
    the same request can share the result without a second DB
    lookup.

    Args:
        request: The current HTTP request.
        identity_service: Per-request IdentityService.
        access_token: Optional Bearer token from the
            Authorization header.
        api_key_header: Optional API key from the
            ``X-API-Key`` header.
        api_key_query: Optional API key from the
            ``?api_key=`` query parameter.

    Returns:
        AuthContext with resolved user_id, scopes, and
        auth_type (``"jwt"`` or ``"api_key"``).

    Raises:
        HTTPException: 401 if no valid credential is
            provided.
    """
    # --- Cache check: return early if Principal already resolved ---
    cached: Principal | None = getattr(
        request.state, "principal", None
    )
    if cached is not None:
        auth_type = "api_key" if cached.is_api_key() else "jwt"
        return AuthContext(
            user_id=cached.user_id,
            scopes=list(cached.scopes),
            auth_type=auth_type,
        )

    # --- JWT path ---
    if access_token is not None:
        principal = identity_service.resolve_from_access_token(
            access_token
        )
        request.state.principal = principal
        return AuthContext(
            user_id=principal.user_id,
            scopes=list(principal.scopes),
            auth_type="jwt",
        )

    # --- API key path ---
    raw_key = api_key_header or api_key_query
    if raw_key is not None:
        principal = identity_service.resolve_from_api_key(
            raw_key, request
        )
        request.state.principal = principal
        return AuthContext(
            user_id=principal.user_id,
            scopes=list(principal.scopes),
            auth_type="api_key",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Not authenticated. "
            "Provide a Bearer token or an API key."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_id_from_auth(
    auth: Annotated[
        "AuthContext",
        Depends(validate_access_token_or_api_key),
    ],
) -> int:
    """Extract the user ID from a unified AuthContext.

    Use this in place of ``get_sub_from_access_token``
    on endpoints that accept both JWT and API key auth.

    Args:
        auth: Resolved AuthContext from
            validate_access_token_or_api_key.

    Returns:
        The authenticated user's ID.
    """
    return auth.user_id


def check_auth_scopes(
    auth: Annotated[
        "AuthContext",
        Depends(validate_access_token_or_api_key),
    ],
    security_scopes: SecurityScopes,
) -> None:
    """Validate scopes from a unified AuthContext.

    Use this in place of ``check_scopes`` on endpoints
    that accept both JWT and API key auth.

    Args:
        auth: Resolved AuthContext from
            validate_access_token_or_api_key.
        security_scopes: Required scopes for the
            endpoint.

    Raises:
        HTTPException: 403 if any required scope is
            missing from the AuthContext.
    """
    missing = set(security_scopes.scopes) - set(auth.scopes)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Unauthorized Access - "
                f"Missing permissions: {missing}"
            ),
            headers={
                "WWW-Authenticate": (
                    f'Bearer scope="{security_scopes.scopes}"'
                )
            },
        )


## WEBSOCKET TOKEN VALIDATION
async def validate_websocket_access_token(
    websocket: WebSocket,
    access_token: str = Query(..., alias="access_token"),
    token_manager: auth_token_manager.TokenManager = Depends(
        auth_token_manager.get_token_manager
    ),
) -> int:
    """
    Validate access token for WebSocket connections.

    WebSocket connections cannot use Authorization headers during
    the handshake, so tokens are passed via query parameters.

    Args:
        websocket: The WebSocket connection instance.
        access_token: Access token from query parameter.
        token_manager: Token manager for validation.

    Returns:
        The authenticated user ID from the token.

    Raises:
        WebSocketException: If token is missing, invalid, or expired.
    """
    try:
        # Validate token expiration and type
        token_manager.validate_token_expiration(
            access_token,
            auth_token_manager.TokenType.ACCESS,
        )

        # Get user ID from token
        token_user_id = token_manager.get_token_claim(access_token, "sub")

        if token_user_id is None or isinstance(token_user_id, list):
            core_logger.print_to_log(
                "WebSocket token validation failed: invalid sub claim",
                "warning",
            )
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid token: missing user ID",
            )

        return int(token_user_id)
    except WebSocketException:
        raise
    except HTTPException as http_err:
        core_logger.print_to_log(
            f"WebSocket token validation failed: {http_err.detail}",
            "warning",
            exc=http_err,
        )
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        ) from http_err
