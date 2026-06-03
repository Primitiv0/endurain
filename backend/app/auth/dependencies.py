"""Public authentication dependencies for non-auth modules.

This module is the supported boundary for routers outside ``auth`` that
need identity, scope checks, or mixed JWT/API-key authentication. The
implementations delegate credential resolution to ``IdentityService`` so
callers do not import ``auth.security`` directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import auth.constants as auth_constants
import auth.identity_service as auth_identity_service
import core.logger as core_logger
from fastapi import Depends, HTTPException, Query, Request, WebSocket, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, SecurityScopes

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes=auth_constants.SCOPE_DICT,
    auto_error=False,
)
header_client_type_scheme = APIKeyHeader(name="X-Client-Type")
header_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class AuthContext:
    """Resolved auth context for JWT or API-key credentials.

    Attributes:
        user_id: Authenticated user's ID.
        scopes: Granted scope strings.
        auth_type: Credential source, either ``jwt`` or ``api_key``.
    """

    user_id: int
    scopes: list[str]
    auth_type: str


def get_access_token(
    access_token: Annotated[str | None, Depends(oauth2_scheme)],
    client_type: str = Depends(header_client_type_scheme),
) -> str:
    """Retrieve an access token from the Authorization header.

    Args:
        access_token: Bearer token parsed by OAuth2PasswordBearer.
        client_type: Client type header required by existing clients.

    Returns:
        The raw access token.

    Raises:
        HTTPException: 401 if the token is missing.
    """
    del client_type
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing from Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token


def _resolve_and_cache_principal(
    access_token: str,
    request: Request,
    identity_service: auth_identity_service.IdentityService,
) -> auth_identity_service.Principal:
    """Resolve a Principal once for the current request.

    Args:
        access_token: Raw JWT access token.
        request: Current HTTP request.
        identity_service: Per-request IdentityService.

    Returns:
        Cached or freshly resolved Principal.
    """
    cached = getattr(request.state, "principal", None)
    if cached is not None:
        return cached

    principal = identity_service.resolve_from_access_token(access_token)
    request.state.principal = principal
    return principal


def validate_access_token(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
) -> None:
    """Validate an access token through IdentityService.

    Args:
        request: Current HTTP request.
        access_token: Raw JWT access token.
        identity_service: Per-request IdentityService.

    Raises:
        HTTPException: 401 if the token is invalid.
    """
    _resolve_and_cache_principal(access_token, request, identity_service)


def get_sub_from_access_token(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
) -> int:
    """Return the authenticated user ID from an access token.

    Args:
        request: Current HTTP request.
        access_token: Raw JWT access token.
        identity_service: Per-request IdentityService.

    Returns:
        Authenticated user's ID.
    """
    principal = _resolve_and_cache_principal(access_token, request, identity_service)
    return principal.user_id


def check_scopes(
    request: Request,
    access_token: Annotated[str, Depends(get_access_token)],
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
    security_scopes: SecurityScopes,
) -> None:
    """Validate required scopes through IdentityService.

    Args:
        request: Current HTTP request.
        access_token: Raw JWT access token.
        identity_service: Per-request IdentityService.
        security_scopes: Required scopes for the endpoint.

    Raises:
        HTTPException: 403 if required scopes are missing.
    """
    principal = _resolve_and_cache_principal(access_token, request, identity_service)
    identity_service.check_scope(principal, frozenset(security_scopes.scopes))


async def validate_access_token_or_api_key(
    request: Request,
    identity_service: Annotated[
        auth_identity_service.IdentityService,
        Depends(auth_identity_service.get_identity_service),
    ],
    access_token: str | None = Depends(oauth2_scheme),
    api_key_header: str | None = Depends(header_api_key_scheme),
    api_key_query: str | None = Query(None, alias="api_key"),
) -> AuthContext:
    """Accept either a JWT bearer token or an API key.

    Args:
        request: Current HTTP request.
        identity_service: Per-request IdentityService.
        access_token: Optional Bearer token.
        api_key_header: Optional ``X-API-Key`` value.
        api_key_query: Optional ``api_key`` query parameter.

    Returns:
        Resolved authentication context.

    Raises:
        HTTPException: 401 if no valid credential is supplied.
    """
    cached = getattr(request.state, "principal", None)
    if cached is not None:
        auth_type = "api_key" if cached.is_api_key() else "jwt"
        return AuthContext(cached.user_id, list(cached.scopes), auth_type)

    if access_token is not None:
        principal = identity_service.resolve_from_access_token(access_token)
        request.state.principal = principal
        return AuthContext(principal.user_id, list(principal.scopes), "jwt")

    raw_key = api_key_header or api_key_query
    if raw_key is not None:
        principal = identity_service.resolve_from_api_key(raw_key, request)
        request.state.principal = principal
        return AuthContext(principal.user_id, list(principal.scopes), "api_key")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide a Bearer token or an API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_id_from_auth(
    auth: Annotated[AuthContext, Depends(validate_access_token_or_api_key)],
) -> int:
    """Extract the user ID from a unified AuthContext.

    Args:
        auth: Resolved authentication context.

    Returns:
        Authenticated user's ID.
    """
    return auth.user_id


def check_auth_scopes(
    auth: Annotated[AuthContext, Depends(validate_access_token_or_api_key)],
    security_scopes: SecurityScopes,
) -> None:
    """Validate scopes from a unified AuthContext.

    Args:
        auth: Resolved authentication context.
        security_scopes: Required endpoint scopes.

    Raises:
        HTTPException: 403 if required scopes are missing.
    """
    missing = set(security_scopes.scopes) - set(auth.scopes)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized Access - Missing permissions: {missing}",
            headers={"WWW-Authenticate": (f'Bearer scope="{security_scopes.scopes}"')},
        )


async def validate_websocket_access_token(
    websocket: WebSocket,
    access_token: str = Query(..., alias="access_token"),
    identity_service: auth_identity_service.IdentityService = Depends(auth_identity_service.get_identity_service),
) -> int:
    """Validate a WebSocket access token through IdentityService.

    Args:
        websocket: WebSocket connection instance.
        access_token: Access token from query parameter.
        identity_service: Per-connection IdentityService.

    Returns:
        Authenticated user's ID.

    Raises:
        WebSocketException: If the token is invalid or expired.
    """
    del websocket
    try:
        principal = identity_service.resolve_from_access_token(access_token)
        return principal.user_id
    except HTTPException as err:
        core_logger.print_to_log(
            f"WebSocket token validation failed: {err.detail}",
            "warning",
            exc=err,
        )
        from fastapi import WebSocketException

        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        ) from err


__all__ = [
    "AuthContext",
    "check_auth_scopes",
    "check_scopes",
    "get_sub_from_access_token",
    "get_user_id_from_auth",
    "validate_access_token",
    "validate_access_token_or_api_key",
    "validate_websocket_access_token",
]
