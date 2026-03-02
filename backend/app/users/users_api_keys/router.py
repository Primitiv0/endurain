"""User API key management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import auth.security as auth_security

import users.users_api_keys.crud as users_api_keys_crud
import users.users_api_keys.schema as users_api_keys_schema
import users.users_api_keys.utils as users_api_keys_utils
import users.users.crud as users_crud

import core.database as core_database

# Define the API router
router = APIRouter()


@router.get(
    "",
    response_model=list[users_api_keys_schema.UsersApiKeyRead],
    status_code=status.HTTP_200_OK,
)
async def get_user_api_keys(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> list[users_api_keys_schema.UsersApiKeyRead]:
    """
    Retrieve all API keys for the authenticated user.

    Args:
        token_user_id: User ID from access token.
        db: Database session dependency.

    Returns:
        List of API key objects. Raw keys and hashes
        are never included.
    """
    return users_api_keys_crud.get_api_keys_by_user_id(
        token_user_id, db
    )  # type: ignore[return-value]


@router.post(
    "",
    response_model=users_api_keys_schema.UsersApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_api_key(
    data: users_api_keys_schema.UsersApiKeyCreate,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> users_api_keys_schema.UsersApiKeyCreated:
    """
    Create a new API key for the authenticated user.

    The raw key is returned once in this response and
    cannot be retrieved again. Requested scopes must be
    a subset of the user's own permissions.

    Args:
        data: Key creation data (name, scopes, expiry).
        token_user_id: User ID from access token.
        db: Database session dependency.

    Returns:
        Created API key including the raw key string.

    Raises:
        HTTPException: 400 if scopes exceed the user's
            own permissions.
        HTTPException: 404 if the user is not found.
    """
    db_user = users_crud.get_user_by_id(token_user_id, db)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        users_api_keys_utils.validate_api_key_scopes(data.scopes, db_user.access_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    db_api_key, raw_key = users_api_keys_crud.create_api_key(token_user_id, data, db)

    return users_api_keys_schema.UsersApiKeyCreated(
        id=db_api_key.id,
        user_id=db_api_key.user_id,
        name=db_api_key.name,
        key_prefix=db_api_key.key_prefix,
        scopes=db_api_key.scopes,
        expires_at=db_api_key.expires_at,
        last_used_at=db_api_key.last_used_at,
        created_at=db_api_key.created_at,
        is_active=db_api_key.is_active,
        key=raw_key,
    )


@router.patch(
    "/{api_key_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_user_api_key(
    api_key_id: str,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> None:
    """
    Revoke an API key (soft-disable).

    The key record is retained for audit purposes but
    will be rejected on any subsequent use.

    Args:
        api_key_id: UUID of the API key to revoke.
        token_user_id: User ID from access token.
        db: Database session dependency.

    Returns:
        None.

    Raises:
        HTTPException: 404 if the key is not found or
            does not belong to the authenticated user.
    """
    users_api_keys_crud.revoke_api_key(api_key_id, token_user_id, db)


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_api_key(
    api_key_id: str,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> None:
    """
    Permanently delete an API key.

    Hard-delete. The key is gone and cannot be used
    or recovered after this operation.

    Args:
        api_key_id: UUID of the API key to delete.
        token_user_id: User ID from access token.
        db: Database session dependency.

    Returns:
        None.

    Raises:
        HTTPException: 404 if the key is not found or
            does not belong to the authenticated user.
    """
    users_api_keys_crud.delete_api_key(api_key_id, token_user_id, db)
