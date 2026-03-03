"""Utility functions for password reset token operations."""

from datetime import datetime, timedelta, timezone
from fastapi import (
    HTTPException,
    status,
)
from uuid import uuid4
import hashlib

from sqlalchemy.orm import Session

from password_reset_tokens import (
    email_messages as password_reset_tokens_email_messages,
)
import password_reset_tokens.schema as password_reset_tokens_schema
import password_reset_tokens.crud as password_reset_tokens_crud

import users.users.crud as users_crud

import auth.password_hasher as auth_password_hasher

import core.apprise as core_apprise
import core.logger as core_logger

from core.database import SessionLocal


def create_password_reset_token(user_id: int, db: Session) -> str:
    """
    Create and persist a password reset token for a user.

    Args:
        user_id: ID of the user requesting the reset.
        db: Active SQLAlchemy session.

    Returns:
        The plaintext token to deliver to the user.
        Only the token hash is stored in the database.
    """
    # Generate token and hash
    token, token_hash = core_apprise.generate_token_and_hash()

    # Create token object
    reset_token = password_reset_tokens_schema.PasswordResetToken(
        id=str(uuid4()),
        user_id=user_id,
        token_hash=token_hash,
        created_at=datetime.now(timezone.utc),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)),
        used=False,
    )

    # Save to database
    password_reset_tokens_crud.create_password_reset_token(reset_token, db)

    # Return the plain token (not the hash)
    return token


async def send_password_reset_email(
    email: str, email_service: core_apprise.AppriseService, db: Session
) -> bool:
    """
    Send a password reset email to the given address.

    Args:
        email: Recipient email address.
        email_service: Configured AppriseService instance.
        db: Active SQLAlchemy session.

    Returns:
        True if the operation is considered successful,
        False if the email service failed to send.

    Raises:
        HTTPException: 503 if the email service is not configured.
    """
    # Check if email service is configured
    if not email_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured",
        )

    # Find user by email
    user = users_crud.get_user_by_email(email, db)
    if not user:
        # Don't reveal if email exists or not for security
        return True

    # Check if user is active
    if not user.active:
        # Don't reveal if user is inactive for security
        return True

    # Generate password reset token
    token = create_password_reset_token(user.id, db)

    # Generate reset link
    reset_link = f"{email_service.frontend_host}/reset-password?token={token}"

    # use default email message in English
    subject, html_content, text_content = (
        password_reset_tokens_email_messages.get_password_reset_email_en(
            user.name, reset_link, email_service
        )
    )

    # Send email
    return await email_service.send_email(
        to_emails=[email],
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def use_password_reset_token(
    token: str,
    new_password: str,
    password_hasher: auth_password_hasher.PasswordHasher,
    db: Session,
) -> None:
    """
    Reset a user's password using a valid reset token.

    Args:
        token: Plaintext reset token from the email link.
        new_password: New plaintext password to set.
        password_hasher: PasswordHasher instance for hashing.
        db: Active SQLAlchemy session.

    Returns:
        None

    Raises:
        HTTPException: 400 if the token is invalid or expired.
        HTTPException: 500 if password update or token marking fails.
    """
    # Hash the provided token to find the database record
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Look up the token in the database
    db_token = password_reset_tokens_crud.get_password_reset_token_by_hash(
        token_hash, db
    )

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    # Update user password
    users_crud.edit_user_password(db_token.user_id, new_password, password_hasher, db)

    # Mark token as used
    password_reset_tokens_crud.mark_password_reset_token_used(db_token.id, db)


def delete_invalid_tokens_from_db() -> None:
    """
    Remove expired password reset tokens from the database.

    Opens a new session, deletes expired tokens, and logs the count if any were
        removed.

    Returns:
        None
    """
    # Create a new database session using context manager
    with SessionLocal() as db:
        # Get num tokens deleted
        num_deleted = password_reset_tokens_crud.delete_expired_password_reset_tokens(
            db
        )

        # Log the number of deleted tokens
        if num_deleted > 0:
            core_logger.print_to_log_and_console(
                f"Deleted {num_deleted} expired password reset tokens", "info"
            )
