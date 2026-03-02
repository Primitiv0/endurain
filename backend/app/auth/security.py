import hmac
from dataclasses import dataclass
from typing import Annotated, Union
from datetime import datetime, timezone
from fastapi import (
    Depends,
    HTTPException,
    Query,
    Request,
    Security,
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
from sqlalchemy.orm import Session

import auth.constants as auth_constants
import auth.token_manager as auth_token_manager

import users.users_api_keys.crud as users_api_keys_crud
import users.users_api_keys.utils as users_api_keys_utils

import core.database as core_database
import core.logger as core_logger

# Define the OAuth2 scheme for handling bearer tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
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


def get_token(
    non_cookie_token: Annotated[Union[str, None], Depends(oauth2_scheme)],
    cookie_token: Union[str, None],
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
    access_token: Annotated[Union[str, None], Depends(oauth2_scheme)],
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
    access_token: Annotated[Union[str, None], Depends(oauth2_scheme)],
    client_type: str | None = Depends(header_client_type_scheme_optional),
) -> str | None:
    """
    Retrieve the access token for browser redirect scenarios.

    Args:
        access_token (Union[str, None]): The access token from the Authorization header
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


def validate_access_token(
    # access_token: Annotated[str, Depends(get_access_token_from_cookies)]
    access_token: Annotated[str, Depends(get_access_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> None:
    """
    Validates the provided access token for expiration.

    This function checks whether the given access token is still valid by verifying its expiration.
    If the token is expired or invalid, an HTTPException is raised and the error is logged.
    Any unexpected errors during validation are also logged and result in a 500 Internal Server Error.

    Args:
        access_token (str): The access token to be validated.
        token_manager (auth_token_manager.TokenManager): The token manager instance used for validation.

    Raises:
        HTTPException: If the token is expired, invalid, or an unexpected error occurs during validation.
    """
    try:
        # Validate the token expiration
        token_manager.validate_token_expiration(access_token)
    except HTTPException as http_err:
        log_level = "debug" if "expired" in http_err.detail.lower() else "error"
        core_logger.print_to_log(
            f"Access token validation failed: {http_err.detail}",
            log_level,
            exc=http_err,
            context={"access_token": "[REDACTED]"},
        )
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during access token validation: {err}",
            "error",
            exc=err,
            context={"access_token": "[REDACTED]"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during access token validation.",
        ) from err


def validate_access_token_for_browser_redirect(
    # access_token: Annotated[str, Depends(get_access_token_from_cookies)]
    access_token: Annotated[str, Depends(get_access_token_for_browser_redirect)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> None:
    """
    Validates the provided access token for expiration for browser redirects.

    This function checks whether the given access token is still valid by verifying its expiration.
    If the token is expired or invalid, an HTTPException is raised and the error is logged.
    Any unexpected errors during validation are also logged and result in a 500 Internal Server Error.

    Args:
        access_token (str): The access token to be validated.
        token_manager (auth_token_manager.TokenManager): The token manager instance used for validation.

    Raises:
        HTTPException: If the token is expired, invalid, or an unexpected error occurs during validation.
    """
    try:
        # Validate the token expiration
        token_manager.validate_token_expiration(access_token)
    except HTTPException as http_err:
        log_level = "debug" if "expired" in http_err.detail.lower() else "error"
        core_logger.print_to_log(
            f"Access token validation failed: {http_err.detail}",
            log_level,
            exc=http_err,
            context={"access_token": "[REDACTED]"},
        )
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during access token validation: {err}",
            "error",
            exc=err,
            context={"access_token": "[REDACTED]"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during access token validation.",
        ) from err


def get_sub_from_access_token(
    access_token: Annotated[str, Depends(get_access_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> int:
    """
    Retrieves the user ID ('sub' claim) from the provided access token.

    Args:
        access_token (str): The access token from which to extract the claim.
        token_manager (auth_token_manager.TokenManager): The token manager instance used to decode and validate the token.

    Returns:
        int: The user ID associated with the access token.

    Raises:
        Exception: If the token is invalid or the 'sub' claim is missing.
    """
    # Return the user ID associated with the token
    sub = token_manager.get_token_claim(access_token, "sub")
    if not isinstance(sub, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sub' claim must be an integer",
        )
    return sub


def get_sub_from_access_token_for_browser_redirect(
    access_token: Annotated[str, Depends(get_access_token_for_browser_redirect)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> int:
    """
    Retrieves the user ID ('sub' claim) from the provided access token for browser redirects.

    Args:
        access_token (str): The access token from which to extract the claim.
        token_manager (auth_token_manager.TokenManager): The token manager instance used to decode and validate the token.

    Returns:
        int: The user ID associated with the access token.

    Raises:
        Exception: If the token is invalid or the 'sub' claim is missing.
    """
    sub = token_manager.get_token_claim(access_token, "sub")
    if not isinstance(sub, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sub' claim must be an integer",
        )
    return sub


def get_sid_from_access_token(
    access_token: Annotated[str, Depends(get_access_token)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
) -> str:
    """
    Retrieves the session ID ('sid') from the provided access token.

    Args:
        access_token (str): The access token from which to extract the session ID.
        token_manager (auth_token_manager.TokenManager): The token manager used to validate and extract claims from the token.

    Returns:
        int: The session ID ('sid') associated with the access token.

    Raises:
        Exception: If the token is invalid or the 'sid' claim is not present.
    """
    # Return the session ID associated with the token
    sid = token_manager.get_token_claim(access_token, "sid")
    if not isinstance(sid, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: 'sid' claim must be a string",
        )
    return sid


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
    non_cookie_refresh_token: Annotated[Union[str, None], Depends(oauth2_scheme)],
    cookie_refresh_token: Union[str, None] = Depends(cookie_refresh_token_scheme),
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
        # Validate the token expiration
        token_manager.validate_token_expiration(refresh_token)
    except HTTPException as http_err:
        log_level = "debug" if "expired" in http_err.detail.lower() else "error"
        core_logger.print_to_log(
            f"Refresh token validation failed: {http_err.detail}",
            log_level,
            exc=http_err,
            context={"refresh_token": "[REDACTED]"},
        )
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during refresh token validation: {err}",
            "error",
            exc=err,
            context={"refresh_token": "[REDACTED]"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during refresh token validation.",
        ) from err


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
        token_manager (auth_token_manager.TokenManager): Instance responsible for managing and validating tokens.
        security_scopes (SecurityScopes): Required scopes for the endpoint.

    Raises:
        HTTPException: If any required scope is missing, raises 403 Forbidden with details.
        HTTPException: If an unexpected error occurs during scope validation, raises 500 Internal Server Error.

    Logs:
        Errors and exceptions are logged using core_logger for debugging and auditing purposes.
    """
    # Get the scope from the token
    scope = token_manager.get_token_claim(access_token, "scope")

    # Ensure the scope is a list
    if not isinstance(scope, list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access - Invalid scope format",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'},
        )

    try:
        # Use set operations to find missing scope
        missing_scopes = set(security_scopes.scopes) - set(scope)
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized Access - Missing permissions: {missing_scopes}",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'
                },
            )
    except HTTPException as http_err:
        core_logger.print_to_log(
            f"Scope validation failed: {http_err}",
            "error",
            exc=http_err,
        )
        raise http_err
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during scope validation: {err}",
            "error",
            exc=err,
            context={"scope": scope, "required_scope": security_scopes.scopes},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during scope validation.",
        ) from err


def check_scopes_for_browser_redirect(
    access_token: Annotated[str, Depends(get_access_token_for_browser_redirect)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
    security_scopes: SecurityScopes,
) -> None:
    """
    Validates that the access token contains all required security scopes for browser redirection.

    Args:
        access_token (str): The access token extracted from the request.
        token_manager (auth_token_manager.TokenManager): Instance responsible for managing and validating tokens.
        security_scopes (SecurityScopes): Required scopes for the endpoint.

    Raises:
        HTTPException: If any required scope is missing, raises 403 Forbidden with details.
        HTTPException: If an unexpected error occurs during scope validation, raises 500 Internal Server Error.

    Logs:
        Errors and exceptions are logged using core_logger for debugging and auditing purposes.
    """
    # Get the scope from the token
    scope = token_manager.get_token_claim(access_token, "scope")

    # Ensure the scope is a list
    if not isinstance(scope, list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized Access - Invalid scope format",
            headers={"WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'},
        )

    try:
        # Use set operations to find missing scope
        missing_scopes = set(security_scopes.scopes) - set(scope)
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized Access - Missing permissions: {missing_scopes}",
                headers={
                    "WWW-Authenticate": f'Bearer scope="{security_scopes.scopes}"'
                },
            )
    except HTTPException as http_err:
        core_logger.print_to_log(
            f"Scope validation failed: {http_err}",
            "error",
            exc=http_err,
        )
        raise http_err
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during scope validation: {err}",
            "error",
            exc=err,
            context={"scope": scope, "required_scope": security_scopes.scopes},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during scope validation.",
        ) from err


## API KEY + UNIFIED AUTH
async def validate_api_key(
    raw_key: str,
    request: Request,
    db,
) -> "AuthContext":
    """
    Validate a raw API key and return an AuthContext.

    Hashes the incoming key with SHA-256, looks it up
    in the database, checks revocation and expiry, and
    updates ``last_used_at``. Uses constant-time
    comparison (``hmac.compare_digest``) to prevent
    timing attacks.

    Args:
        raw_key: The plain-text API key from the
            request header or query parameter.
        request: The current HTTP request (for audit
            logging).
        db: SQLAlchemy database session.

    Returns:
        AuthContext with user_id, scopes, and
        auth_type set to ``"api_key"``.

    Raises:
        HTTPException: 401 if the key is not found,
            revoked, or expired.
    """
    computed_hash = users_api_keys_utils.hash_api_key(raw_key)
    db_key = users_api_keys_crud.get_api_key_by_hash(computed_hash, db)

    # Constant-time comparison to prevent timing attacks
    # (protects even when key is not found)
    stored_hash = db_key.key_hash if db_key else ("0" * 64)
    if not hmac.compare_digest(stored_hash, computed_hash):
        db_key = None

    if db_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not db_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if db_key.expires_at is not None:
        expires = db_key.expires_at
        # Ensure timezone-aware comparison
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # Update last_used_at (best-effort; don't fail the
    # request if this errors)
    try:
        users_api_keys_crud.update_last_used(db_key.id, db)
    except Exception as err:
        core_logger.print_to_log(
            f"Failed to update last_used_at for API key " f"{db_key.id}: {err}",
            "warning",
            exc=err,
        )

    # Structured audit log
    core_logger.print_to_log(
        "API key authenticated",
        "info",
        context={
            "key_prefix": db_key.key_prefix,
            "user_id": db_key.user_id,
            "endpoint": request.url.path,
            "ip": (request.client.host if request.client else "unknown"),
        },
    )

    scopes = users_api_keys_utils.json_to_scopes(db_key.scopes)
    return AuthContext(
        user_id=db_key.user_id,
        scopes=scopes,
        auth_type="api_key",
    )


async def validate_access_token_or_api_key(
    request: Request,
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
    bearer_token: Union[str, None] = Depends(oauth2_scheme),
    api_key_header: Union[str, None] = Depends(header_api_key_scheme),
    api_key_query: Union[str, None] = Query(None, alias="api_key"),
) -> "AuthContext":
    """
    Accept either a JWT bearer token or an API key.

    Tries JWT first (Authorization: Bearer header). If
    none is present, falls back to the ``X-API-Key``
    header, then the ``?api_key=`` query parameter.
    Raises 401 if neither is supplied.

    Args:
        request: The current HTTP request.
        token_manager: JWT token manager dependency.
        db: Database session dependency.
        bearer_token: Optional Bearer token from the
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
    # --- JWT path ---
    if bearer_token is not None:
        try:
            token_manager.validate_token_expiration(bearer_token)
        except HTTPException as http_err:
            log_level = "debug" if "expired" in http_err.detail.lower() else "error"
            core_logger.print_to_log(
                f"Access token validation failed: " f"{http_err.detail}",
                log_level,
                exc=http_err,
                context={"access_token": "[REDACTED]"},
            )
            raise

        sub = token_manager.get_token_claim(bearer_token, "sub")
        if not isinstance(sub, int):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=("Invalid token: 'sub' claim must " "be an integer"),
            )
        scope = token_manager.get_token_claim(bearer_token, "scope")
        if not isinstance(scope, list):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=("Invalid token: 'scope' claim must " "be a list"),
            )
        return AuthContext(user_id=sub, scopes=scope, auth_type="jwt")

    # --- API key path ---
    raw_key = api_key_header or api_key_query
    if raw_key is not None:
        return await validate_api_key(raw_key, request, db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=("Not authenticated. Provide a Bearer token " "or an API key."),
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_id_from_auth(
    auth: Annotated[
        "AuthContext",
        Depends(validate_access_token_or_api_key),
    ],
) -> int:
    """
    Extract the user ID from a unified AuthContext.

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
    """
    Validate scopes from a unified AuthContext.

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
            detail=(f"Unauthorized Access - Missing " f"permissions: {missing}"),
            headers={
                "WWW-Authenticate": (f'Bearer scope="' f'{security_scopes.scopes}"')
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
        # Validate token expiration
        token_manager.validate_token_expiration(access_token)

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
    except WebSocketException as ws_err:
        raise ws_err
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
    except Exception as err:
        core_logger.print_to_log(
            f"Unexpected error during WebSocket token validation: {err}",
            "error",
            exc=err,
        )
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token validation failed",
        ) from err
