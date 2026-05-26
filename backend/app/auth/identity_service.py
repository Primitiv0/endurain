"""IdentityService Protocol and DefaultIdentityService implementation.

Defines the ``IdentityService`` boundary type that non-auth modules must use
to consume identity.  The boundary hides the concrete helpers
(:mod:`auth.security`, :mod:`auth.password_hasher`, :mod:`auth.token_manager`)
from external callers and makes them mockable in isolation.

Transaction contract
--------------------
``IdentityService`` methods do **not** commit the database session.
The caller (FastAPI dependency / outer handler) owns the transaction
lifecycle; rollback on failure is the caller's responsibility.

Request-state caching
---------------------
The resolved :class:`~auth.principal.Principal` should be stored on
``request.state.principal`` after the first resolution so that
multiple FastAPI dependencies in the same request do not trigger
duplicate database lookups.

Usage
-----
Inject via the ``get_identity_service`` FastAPI dependency.  A new
:class:`DefaultIdentityService` instance is returned per request;
never use a module-level singleton.
"""

from __future__ import annotations

import hmac
from datetime import datetime, timezone
from typing import Annotated, Protocol, runtime_checkable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import auth.password_hasher as auth_password_hasher
import auth.token_manager as auth_token_manager
import auth.utils as auth_utils

import users.users.schema as users_schema
import users.users.utils as users_utils
import users.users_api_keys.crud as users_api_keys_crud
import users.users_api_keys.utils as users_api_keys_utils
import auth.sessions.crud as users_sessions_crud

import core.database as core_database
import core.logger as core_logger

from auth.principal import (
    AccessTokenCred,
    ApiKeyCred,
    OAuthCred,
    PasswordCred,
    Principal,
    SessionCookieCred,
)

__all__ = [
    "IdentityService",
    "DefaultIdentityService",
    "get_identity_service",
]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class IdentityService(Protocol):
    """Typed contract for the auth boundary.

    All methods except :meth:`check_scope` may raise
    :class:`~fastapi.HTTPException` on invalid or expired
    credentials.  None of the methods commit the database
    session — that is the caller's responsibility.
    """

    def authenticate_password(
        self,
        username: str,
        password: str,
    ) -> Principal:
        """Verify username/password and return a Principal.

        Args:
            username: The username supplied by the caller.
            password: The plaintext password to verify.

        Returns:
            Principal: Resolved principal with a
                :class:`~auth.principal.PasswordCred`.

        Raises:
            HTTPException: 401 if the credentials are
                invalid or the account does not exist.
        """
        ...

    def resolve_from_access_token(
        self,
        access_token: str,
    ) -> Principal:
        """Validate a JWT access token and return a Principal.

        Args:
            access_token: The raw JWT string from the
                Authorization header.

        Returns:
            Principal: Resolved principal with an
                :class:`~auth.principal.AccessTokenCred`.

        Raises:
            HTTPException: 401 if the token is expired,
                invalid, or the user is not found.
        """
        ...

    def resolve_from_api_key(
        self,
        raw_key: str,
        request: Request,
    ) -> Principal:
        """Validate a raw API key and return a Principal.

        Args:
            raw_key: The plain-text API key from the
                ``X-API-Key`` header or ``?api_key=``
                query parameter.
            request: The current HTTP request (used for
                audit logging).

        Returns:
            Principal: Resolved principal with an
                :class:`~auth.principal.ApiKeyCred`.

        Raises:
            HTTPException: 401 if the key is not found,
                revoked, or expired.
        """
        ...

    def resolve_from_session_cookie(
        self,
        session_id: str,
    ) -> Principal:
        """Validate a session ID and return a Principal.

        Args:
            session_id: The session identifier from the
                cookie or token ``sid`` claim.

        Returns:
            Principal: Resolved principal with a
                :class:`~auth.principal.SessionCookieCred`.

        Raises:
            HTTPException: 401 if the session is not
                found or has expired.
        """
        ...

    def issue_token_pair(
        self,
        user: users_schema.UsersRead,
        session_id: str | None = None,
    ) -> tuple[str, datetime, str, datetime, str, str]:
        """Issue an access/refresh token pair for a user.

        Args:
            user: The validated user object.
            session_id: Optional existing session
                identifier; a new UUID is generated
                when ``None``.

        Returns:
            tuple: ``(session_id, access_token_exp,
                access_token, refresh_token_exp,
                refresh_token, csrf_token)``.
        """
        ...

    def revoke_session(
        self,
        session_id: str,
        user_id: int,
    ) -> None:
        """Revoke and delete a session.

        Args:
            session_id: The session to revoke.
            user_id: Owner of the session (used to
                prevent cross-user revocations).

        Raises:
            HTTPException: 404 if the session is not
                found for this user.
        """
        ...

    def revoke_api_key(
        self,
        api_key_id: str,
        user_id: int,
    ) -> None:
        """Soft-revoke an API key (sets ``is_active=False``).

        Args:
            api_key_id: UUID of the API key.
            user_id: Owner of the API key (prevents
                cross-user revocations).

        Raises:
            HTTPException: 404 if the key is not found
                for this user.
        """
        ...

    def check_scope(
        self,
        principal: Principal,
        required_scopes: frozenset[str],
    ) -> None:
        """Assert that the principal holds all required scopes.

        Args:
            principal: The authenticated principal.
            required_scopes: Scope strings that must all
                be present in ``principal.scopes``.

        Raises:
            HTTPException: 403 if any required scope is
                missing.
        """
        ...


# ---------------------------------------------------------------------------
# Default implementation
# ---------------------------------------------------------------------------


class DefaultIdentityService:
    """Concrete ``IdentityService`` that delegates to existing helpers.

    Constructor injects all per-request dependencies explicitly so that
    each method is testable in isolation.

    Transaction contract: none of the methods call ``db.commit()``.
    The caller (FastAPI dependency or outer handler) is responsible for
    committing or rolling back the session.

    Attributes:
        _db: SQLAlchemy database session for this request.
        _token_manager: JWT token manager.
        _password_hasher: Password hasher/verifier.
    """

    def __init__(
        self,
        db: Session,
        token_manager: auth_token_manager.TokenManager,
        password_hasher: auth_password_hasher.PasswordHasher,
    ) -> None:
        """
        Initialise the service with per-request dependencies.

        Args:
            db: SQLAlchemy database session.
            token_manager: Configured JWT token manager.
            password_hasher: Argon2/bcrypt password hasher.
        """
        self._db = db
        self._token_manager = token_manager
        self._password_hasher = password_hasher

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_principal(
        self,
        user: object,
        scopes: list[str],
        credential: (
            PasswordCred
            | AccessTokenCred
            | ApiKeyCred
            | SessionCookieCred
            | OAuthCred
        ),
    ) -> Principal:
        """Build a ``Principal`` from an ORM user row.

        Args:
            user: SQLAlchemy ``Users`` model instance.
            scopes: List of granted OAuth2 scope strings.
            credential: Typed credential variant.

        Returns:
            Principal: Frozen principal ready to cache on
                ``request.state``.
        """
        return Principal(
            user_id=user.id,  # type: ignore[attr-defined]
            username=user.username,  # type: ignore[attr-defined]
            email=user.email,  # type: ignore[attr-defined]
            is_active=bool(user.active),  # type: ignore[attr-defined]
            is_superuser=(
                user.access_type == "admin"  # type: ignore[attr-defined]
            ),
            scopes=frozenset(scopes),
            credential=credential,
        )

    # ------------------------------------------------------------------
    # Protocol methods
    # ------------------------------------------------------------------

    def authenticate_password(
        self,
        username: str,
        password: str,
    ) -> Principal:
        """Verify username/password and return a Principal.

        Args:
            username: The username supplied by the caller.
            password: The plaintext password to verify.

        Returns:
            Principal: Resolved principal with a
                :class:`~auth.principal.PasswordCred`.

        Raises:
            HTTPException: 401 if the credentials are
                invalid or the account does not exist.
        """
        user = auth_utils.authenticate_user(
            username,
            password,
            self._password_hasher,
            self._db,
        )
        # Scopes are determined by the token-issuing step;
        # at password-auth time we return an empty set so
        # callers know authentication succeeded but must
        # call issue_token_pair to get scoped tokens.
        return self._build_principal(user, [], PasswordCred(username=username))

    def resolve_from_access_token(
        self,
        access_token: str,
    ) -> Principal:
        """Validate a JWT access token and return a Principal.

        Args:
            access_token: The raw JWT string from the
                Authorization header.

        Returns:
            Principal: Resolved principal with an
                :class:`~auth.principal.AccessTokenCred`.

        Raises:
            HTTPException: 401 if the token is expired,
                invalid, or the user is not found.
        """
        try:
            self._token_manager.validate_token_expiration(
                access_token,
                auth_token_manager.TokenType.ACCESS,
            )
        except HTTPException as http_err:
            log_level = (
                "debug"
                if "expired" in http_err.detail.lower()
                else "error"
            )
            core_logger.print_to_log(
                f"Access token validation failed: "
                f"{http_err.detail}",
                log_level,
                exc=http_err,
                context={"access_token": "[REDACTED]"},
            )
            raise

        sub = self._token_manager.get_token_claim(access_token, "sub")
        if not isinstance(sub, int):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: 'sub' claim must be an integer",
            )

        scope = self._token_manager.get_token_claim(access_token, "scope")
        if not isinstance(scope, list):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: 'scope' claim must be a list",
            )

        sid = self._token_manager.get_token_claim(access_token, "sid")
        if not isinstance(sid, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Invalid token: 'sid' claim must be a string"
                ),
            )

        user = users_utils.get_user_by_id_or_404(sub, self._db)
        users_utils.check_user_is_active(user)

        return self._build_principal(
            user,
            scope,
            AccessTokenCred(session_id=sid),
        )

    def resolve_from_api_key(
        self,
        raw_key: str,
        request: Request,
    ) -> Principal:
        """Validate a raw API key and return a Principal.

        Args:
            raw_key: The plain-text API key from the
                ``X-API-Key`` header or ``?api_key=``
                query parameter.
            request: The current HTTP request (used for
                audit logging).

        Returns:
            Principal: Resolved principal with an
                :class:`~auth.principal.ApiKeyCred`.

        Raises:
            HTTPException: 401 if the key is not found,
                revoked, or expired.
        """
        computed_hash = users_api_keys_utils.hash_api_key(raw_key)
        db_key = users_api_keys_crud.get_api_key_by_hash(
            computed_hash, self._db
        )

        # Constant-time comparison prevents timing attacks
        # even when the key is not found.
        stored_hash = db_key.key_hash if db_key else ("0" * 64)
        if not hmac.compare_digest(stored_hash, computed_hash):
            db_key = None

        if db_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        user = users_utils.get_user_by_id_or_404(db_key.user_id, self._db)
        users_utils.check_user_is_active(user)

        if not db_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        if db_key.expires_at is not None:
            if datetime.now(timezone.utc) > db_key.expires_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        # Best-effort last_used_at update; never fails the request.
        try:
            users_api_keys_crud.update_last_used(db_key.id, self._db)
        except SQLAlchemyError as err:
            core_logger.print_to_log(
                f"Failed to update last_used_at for "
                f"API key {db_key.id}: {err}",
                "warning",
                exc=err,
            )

        core_logger.print_to_log(
            "API key authenticated",
            "info",
            context={
                "key_prefix": db_key.key_prefix,
                "user_id": db_key.user_id,
                "endpoint": request.url.path,
                "ip": (
                    request.client.host
                    if request.client
                    else "unknown"
                ),
            },
        )

        scopes = users_api_keys_utils.json_to_scopes(db_key.scopes)
        return self._build_principal(
            user,
            scopes,
            ApiKeyCred(
                api_key_id=db_key.id,
                key_prefix=db_key.key_prefix,
            ),
        )

    def resolve_from_session_cookie(
        self,
        session_id: str,
    ) -> Principal:
        """Validate a session ID and return a Principal.

        Args:
            session_id: The session identifier from the
                cookie or token ``sid`` claim.

        Returns:
            Principal: Resolved principal with a
                :class:`~auth.principal.SessionCookieCred`.

        Raises:
            HTTPException: 401 if the session is not
                found or has expired.
        """
        db_session = users_sessions_crud.get_session_by_id_not_expired(
            session_id, self._db
        )
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = users_utils.get_user_by_id_or_404(
            db_session.user_id, self._db
        )
        users_utils.check_user_is_active(user)

        return self._build_principal(
            user,
            [],
            SessionCookieCred(session_id=session_id),
        )

    def issue_token_pair(
        self,
        user: users_schema.UsersRead,
        session_id: str | None = None,
    ) -> tuple[str, datetime, str, datetime, str, str]:
        """Issue an access/refresh token pair for a user.

        Args:
            user: The validated user object.
            session_id: Optional existing session
                identifier; a new UUID is generated
                when ``None``.

        Returns:
            tuple: ``(session_id, access_token_exp,
                access_token, refresh_token_exp,
                refresh_token, csrf_token)``.
        """
        return auth_utils.create_tokens(
            user, self._token_manager, session_id
        )

    def revoke_session(
        self,
        session_id: str,
        user_id: int,
    ) -> None:
        """Revoke and delete a session.

        Args:
            session_id: The session to revoke.
            user_id: Owner of the session (used to
                prevent cross-user revocations).

        Raises:
            HTTPException: 404 if the session is not
                found for this user.
        """
        users_sessions_crud.delete_session(
            session_id, user_id, self._db
        )

    def revoke_api_key(
        self,
        api_key_id: str,
        user_id: int,
    ) -> None:
        """Soft-revoke an API key (sets ``is_active=False``).

        Args:
            api_key_id: UUID of the API key.
            user_id: Owner of the API key (prevents
                cross-user revocations).

        Raises:
            HTTPException: 404 if the key is not found
                for this user.
        """
        users_api_keys_crud.revoke_api_key(
            api_key_id, user_id, self._db
        )

    def check_scope(
        self,
        principal: Principal,
        required_scopes: frozenset[str],
    ) -> None:
        """Assert that the principal holds all required scopes.

        Args:
            principal: The authenticated principal.
            required_scopes: Scope strings that must all
                be present in ``principal.scopes``.

        Raises:
            HTTPException: 403 if any required scope is
                missing.
        """
        missing = required_scopes - principal.scopes
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Unauthorized Access - "
                    f"Missing permissions: {missing}"
                ),
            )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


def get_identity_service(
    db: Annotated[Session, Depends(core_database.get_db)],
    token_manager: Annotated[
        auth_token_manager.TokenManager,
        Depends(auth_token_manager.get_token_manager),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
) -> IdentityService:
    """FastAPI dependency that yields a per-request IdentityService.

    A new :class:`DefaultIdentityService` is constructed for every
    request.  Never use a module-level singleton.

    The resolved :class:`~auth.principal.Principal` should be cached
    on ``request.state.principal`` by the caller so that downstream
    dependencies within the same request do not trigger extra database
    lookups.

    Args:
        db: SQLAlchemy database session (from ``get_db``).
        token_manager: JWT token manager.
        password_hasher: Argon2/bcrypt password hasher.

    Returns:
        IdentityService: A fresh ``DefaultIdentityService`` instance
            bound to this request's dependencies.
    """
    return DefaultIdentityService(db, token_manager, password_hasher)
