"""
Password reset tokens module for user password recovery.

This module provides CRUD operations, email messaging,
and utilities for password reset token management.

Exports:
    - CRUD: create_password_reset_token,
      get_password_reset_token_by_hash,
      mark_password_reset_token_used,
      delete_expired_password_reset_tokens
    - Schemas: PasswordResetToken, PasswordResetRequest,
      PasswordResetConfirm, PasswordResetResponse
    - Models: PasswordResetToken (ORM model)
"""

from .crud import (
    create_password_reset_token,
    get_password_reset_token_by_hash,
    mark_password_reset_token_used,
    delete_expired_password_reset_tokens,
)
from .models import PasswordResetToken as PasswordResetTokenModel
from .schema import (
    PasswordResetToken,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse,
)

__all__ = [
    # CRUD operations
    "create_password_reset_token",
    "get_password_reset_token_by_hash",
    "mark_password_reset_token_used",
    "delete_expired_password_reset_tokens",
    # Database model
    "PasswordResetTokenModel",
    # Pydantic schemas
    "PasswordResetToken",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "PasswordResetResponse",
]
