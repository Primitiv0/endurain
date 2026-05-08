"""
Identity Provider Link Tokens Module

Provides one-time, short-lived tokens for securely linking identity
providers to existing user accounts.

Exports:
    - CRUD: create_idp_link_token,
      get_idp_link_token_by_id,
      mark_token_as_used,
      delete_expired_tokens
    - Schemas: IdpLinkTokenCreate, IdpLinkTokenResponse
    - Models: IdpLinkToken (ORM model)
    - Utils: generate_idp_link_token,
      delete_idp_link_expired_tokens_from_db,
      TOKEN_EXPIRY_SECONDS
"""

from .crud import (
    create_idp_link_token,
    delete_expired_tokens,
    get_idp_link_token_by_id,
    mark_token_as_used,
)
from .models import IdpLinkToken as IdpLinkTokenModel
from .schema import IdpLinkTokenCreate, IdpLinkTokenResponse
from .utils import (
    TOKEN_EXPIRY_SECONDS,
    delete_idp_link_expired_tokens_from_db,
    generate_idp_link_token,
)

__all__ = [
    # CRUD operations
    "create_idp_link_token",
    "delete_expired_tokens",
    "get_idp_link_token_by_id",
    "mark_token_as_used",
    # Database model
    "IdpLinkTokenModel",
    # Pydantic schemas
    "IdpLinkTokenCreate",
    "IdpLinkTokenResponse",
    # Utilities
    "TOKEN_EXPIRY_SECONDS",
    "delete_idp_link_expired_tokens_from_db",
    "generate_idp_link_token",
]
