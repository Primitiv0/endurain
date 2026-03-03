"""
Sign-up tokens module for user registration.

This module provides CRUD operations, email messaging, and utilities for
sign-up token management.

Exports:
    - CRUD: create_sign_up_token,
      get_sign_up_token_by_hash,
      mark_sign_up_token_used,
      delete_expired_sign_up_tokens
    - Schemas: SignUpToken, SignUpConfirm,
      SignUpResponse
    - Models: SignUpToken (ORM model)
"""

from .crud import (
    create_sign_up_token,
    get_sign_up_token_by_hash,
    mark_sign_up_token_used,
    delete_expired_sign_up_tokens,
)
from .models import SignUpToken as SignUpTokenModel
from .schema import (
    SignUpToken,
    SignUpConfirm,
    SignUpResponse,
)

__all__ = [
    # CRUD operations
    "create_sign_up_token",
    "get_sign_up_token_by_hash",
    "mark_sign_up_token_used",
    "delete_expired_sign_up_tokens",
    # Database model
    "SignUpTokenModel",
    # Pydantic schemas
    "SignUpToken",
    "SignUpConfirm",
    "SignUpResponse",
]
