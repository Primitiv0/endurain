"""CRUD operations for IdP link tokens."""

from datetime import datetime, timezone

from sqlalchemy import delete as sa_delete, select, update as sa_update
from sqlalchemy.orm import Session

import auth.idp_link_tokens.models as idp_link_token_models
import auth.idp_link_tokens.schema as idp_link_token_schema

import core.decorators as core_decorators
import core.logger as core_logger


@core_decorators.handle_db_errors
def get_idp_link_token_by_id(
    token_id: str, db: Session
) -> idp_link_token_models.IdpLinkToken | None:
    """Retrieve an IdP link token by ID, validating it is not expired or used.

    Args:
        token_id: The token ID to lookup.
        db: SQLAlchemy database session.

    Returns:
        The matching IdpLinkToken if valid (not expired and unused),
        None otherwise.

    Raises:
        HTTPException: 500 error if database query fails.
    """
    stmt = select(idp_link_token_models.IdpLinkToken).where(
        idp_link_token_models.IdpLinkToken.id == token_id,
        idp_link_token_models.IdpLinkToken.used.is_(False),
        idp_link_token_models.IdpLinkToken.expires_at
        > datetime.now(timezone.utc),
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def create_idp_link_token(
    token_data: idp_link_token_schema.IdpLinkTokenCreate, db: Session
) -> idp_link_token_models.IdpLinkToken:
    """Create and persist an IdP link token in the database.

    Args:
        token_data: Schema object containing token data.
        db: SQLAlchemy database session.

    Returns:
        The persisted IdpLinkToken instance.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    db_token = idp_link_token_models.IdpLinkToken(**token_data.model_dump())
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


@core_decorators.handle_db_errors
def mark_token_as_used(token_id: str, db: Session) -> bool:
    """Atomically mark an unused, unexpired IdP link token as used.

    Performs a single conditional UPDATE so concurrent attempts to
    consume the same token cannot both succeed (replay protection).

    Args:
        token_id: The token ID to mark as used.
        db: SQLAlchemy database session.

    Returns:
        True if exactly one row was claimed, False if the token was
        missing, expired, or already consumed.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    stmt = (
        sa_update(idp_link_token_models.IdpLinkToken)
        .where(
            idp_link_token_models.IdpLinkToken.id == token_id,
            idp_link_token_models.IdpLinkToken.used.is_(False),
            idp_link_token_models.IdpLinkToken.expires_at
            > datetime.now(timezone.utc),
        )
        .values(used=True)
    )
    result = db.execute(stmt)
    db.commit()

    claimed = result.rowcount == 1
    if claimed:
        core_logger.print_to_log(
            f"IdP link token marked as used: {token_id[:8]}...", "debug"
        )
    return claimed


@core_decorators.handle_db_errors
def delete_expired_tokens(db: Session) -> int:
    """Delete all expired IdP link tokens from the database.

    Args:
        db: SQLAlchemy database session.

    Returns:
        Number of tokens deleted.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    stmt = sa_delete(idp_link_token_models.IdpLinkToken).where(
        idp_link_token_models.IdpLinkToken.expires_at
        < datetime.now(timezone.utc)
    )
    result = db.execute(stmt)
    db.commit()

    deleted_count = result.rowcount
    if deleted_count > 0:
        core_logger.print_to_log(
            f"Deleted {deleted_count} expired IdP link token(s)", "debug"
        )
    return deleted_count
