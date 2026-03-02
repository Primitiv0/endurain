"""
User API key management module.

This module provides API key lifecycle management including
creation, validation, revocation, and deletion.

Exports:
    - CRUD: get_api_keys_by_user_id, get_api_key_by_id,
      get_api_key_by_hash, create_api_key, update_last_used,
      revoke_api_key, delete_api_key
    - Schemas: UsersApiKeyCreate, UsersApiKeyRead,
      UsersApiKeyCreated
    - Models: UsersApiKeys (ORM model)
    - Utils: generate_api_key, hash_api_key,
      validate_api_key_scopes
"""

from .crud import (
    get_api_keys_by_user_id,
    get_api_key_by_id,
    get_api_key_by_hash,
    create_api_key,
    update_last_used,
    revoke_api_key,
    delete_api_key,
)
from .models import UsersApiKeys as UsersApiKeysModel
from .schema import (
    UsersApiKeyCreate,
    UsersApiKeyRead,
    UsersApiKeyCreated,
)
from .utils import (
    generate_api_key,
    hash_api_key,
    validate_api_key_scopes,
)

__all__ = [
    # CRUD operations
    "get_api_keys_by_user_id",
    "get_api_key_by_id",
    "get_api_key_by_hash",
    "create_api_key",
    "update_last_used",
    "revoke_api_key",
    "delete_api_key",
    # Database model
    "UsersApiKeysModel",
    # Pydantic schemas
    "UsersApiKeyCreate",
    "UsersApiKeyRead",
    "UsersApiKeyCreated",
    # Utility functions
    "generate_api_key",
    "hash_api_key",
    "validate_api_key_scopes",
]
