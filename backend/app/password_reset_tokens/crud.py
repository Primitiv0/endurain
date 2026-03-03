"""CRUD operations for password reset tokens."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.orm import Session

import password_reset_tokens.schema as password_reset_tokens_schema
import password_reset_tokens.models as password_reset_tokens_models

import core.decorators as core_decorators


@core_decorators.handle_db_errors
def create_password_reset_token(
    token: password_reset_tokens_schema.PasswordResetToken,
    db: Session,
) -> password_reset_tokens_models.PasswordResetToken:
    """Create and persist a new password reset token.

    Args:
        token: Schema object with token data to persist.
        db: SQLAlchemy database session.

    Returns:
        The persisted PasswordResetToken ORM instance.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    # Create a new password reset token
    db_token = password_reset_tokens_models.PasswordResetToken(
        id=token.id,
        user_id=token.user_id,
        token_hash=token.token_hash,
        created_at=token.created_at,
        expires_at=token.expires_at,
        used=token.used,
    )

    # Add the token to the database
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return db_token


@core_decorators.handle_db_errors
def get_password_reset_token_by_hash(
    token_hash: str, db: Session
) -> password_reset_tokens_models.PasswordResetToken | None:
    """Retrieve an unused, unexpired token matching the given hash.

    Args:
        token_hash: The hashed token value to look up.
        db: SQLAlchemy database session.

    Returns:
        The matching PasswordResetToken if found and valid,
        None otherwise.

    Raises:
        HTTPException: 500 error if database query fails.
    """
    stmt = select(password_reset_tokens_models.PasswordResetToken).where(
        password_reset_tokens_models.PasswordResetToken.token_hash == token_hash,
        password_reset_tokens_models.PasswordResetToken.used == False,  # noqa: E712
        password_reset_tokens_models.PasswordResetToken.expires_at
        > datetime.now(timezone.utc),
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def mark_password_reset_token_used(
    token_id: str, db: Session
) -> password_reset_tokens_models.PasswordResetToken | None:
    """Mark a password reset token as used.

    Args:
        token_id: The unique identifier of the token to mark.
        db: SQLAlchemy database session.

    Returns:
        Updated PasswordResetToken instance if found,
        None otherwise.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    stmt = select(password_reset_tokens_models.PasswordResetToken).where(
        password_reset_tokens_models.PasswordResetToken.id == token_id,
    )
    db_token = db.execute(stmt).scalar_one_or_none()

    if db_token:
        # Mark the token as used
        db_token.used = True
        db.commit()
        db.refresh(db_token)

    return db_token


@core_decorators.handle_db_errors
def delete_expired_password_reset_tokens(db: Session) -> int:
    """Delete all expired password reset tokens.

    Args:
        db: SQLAlchemy database session.

    Returns:
        Number of deleted rows.

    Raises:
        HTTPException: 500 error if database operation fails.
    """
    stmt = sa_delete(password_reset_tokens_models.PasswordResetToken).where(
        password_reset_tokens_models.PasswordResetToken.expires_at
        < datetime.now(timezone.utc)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount
