"""Gear API router endpoints."""

from typing import Annotated, Callable

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Security,
    status,
)
from sqlalchemy.orm import Session

import auth.security as auth_security

import gears.gear.crud as gears_crud
import gears.gear.dependencies as gears_dependencies
import gears.gear.models as gear_models
import gears.gear.schema as gears_schema

import core.database as core_database
import core.dependencies as core_dependencies

# Define the API router
router = APIRouter()

@router.get(
    "",
    response_model=gears_schema.GearsListResponse,
    status_code=status.HTTP_200_OK,
)
async def read_gears_user_all_pagination(
    _validate_pagination_values_on_query: Annotated[
        Callable,
        Depends(
            core_dependencies
            .validate_pagination_values_on_query
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
    page_number: Annotated[
        int | None,
        Query(
            description="Pagination page number",
        ),
    ] = None,
    num_records: Annotated[
        int | None,
        Query(
            description="Records per page",
        ),
    ] = None,
    show_inactive: Annotated[
        bool | None,
        Query(
            description="Filter by inactive status",
        ),
    ] = None,
) -> gears_schema.GearsListResponse:
    """
    Retrieve paginated gear records for a user.

    Args:
        _validate_pagination_values_on_query:
            Validates pagination query params.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.
        page_number: Optional page number.
        num_records: Optional records per page.
        show_inactive: Optional inactive filter.

    Returns:
        GearsListResponse with paginated records.

    Raises:
        HTTPException: If unauthorized or invalid
            parameters.
    """
    total = gears_crud.get_gears_number(db)
    gears = (
        gears_crud.get_gear_users_with_pagination(
            token_user_id,
            db,
            page_number,
            num_records,
            show_inactive,
        )
    )

    return gears_schema.GearsListResponse(
        total=total,
        num_records=num_records,
        page_number=page_number,
        records=gears,
    )


@router.get(
    "/id/{gear_id}",
    response_model=gears_schema.GearRead | None,
    status_code=status.HTTP_200_OK,
)
async def read_gear_id(
    gear_id: int,
    validate_id: Annotated[
        Callable,
        Depends(
            gears_dependencies.validate_gear_id,
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gears_schema.GearRead | None:
    """
    Retrieve a gear by ID for the authenticated user.
    Args:
        gear_id: Gear ID to retrieve.
        validate_id: Validates gear ID exists.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        GearRead if found, None otherwise.

    Raises:
        HTTPException: If unauthorized.
    """
    return gears_crud.get_gear_user_by_id(
        token_user_id, gear_id, db,
    )


@router.get(
    "/nickname/contains/{nickname}",
    response_model=list[gears_schema.GearRead],
    status_code=status.HTTP_200_OK,
)
async def read_gear_user_contains_nickname(
    nickname: str,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> list[gear_models.Gear]:
    """
    Retrieve gears matching a nickname substring.

    Args:
        nickname: Substring to search for.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        List of GearRead matching the nickname.

    Raises:
        HTTPException: If unauthorized.
    """
    return (
        gears_crud
        .get_gear_user_contains_nickname(
            token_user_id, nickname, db,
        )
    )


@router.get(
    "/nickname/{nickname}",
    response_model=gears_schema.GearRead | None,
    status_code=status.HTTP_200_OK,
)
async def read_gear_user_by_nickname(
    nickname: str,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gears_schema.GearRead | None:
    """
    Retrieve a gear by exact nickname for a user.

    Args:
        nickname: Gear nickname to match.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        GearRead if found, None otherwise.

    Raises:
        HTTPException: If unauthorized.
    """
    return gears_crud.get_gear_user_by_nickname(
        token_user_id, nickname, db,
    )


@router.get(
    "/type/{gear_type}",
    response_model=list[gears_schema.GearRead],
    status_code=status.HTTP_200_OK,
)
async def read_gear_user_by_type(
    gear_type: int,
    validate_type: Annotated[
        Callable,
        Depends(
            gears_dependencies.validate_gear_type,
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> list[gear_models.Gear]:
    """
    Retrieve gears by type for a user.

    Args:
        gear_type: Gear type identifier.
        validate_type: Validates gear type value.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        List of GearRead matching the type.

    Raises:
        HTTPException: If unauthorized or invalid
            type.
    """
    return gears_crud.get_gear_by_type_and_user(
        gear_type, token_user_id, db,
    )


@router.post(
    "",
    response_model=gears_schema.GearRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_gear(
    gear: gears_schema.GearCreate,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gears_schema.GearRead:
    """
    Create a new gear for the authenticated user.

    Args:
        gear: Gear data to create.
        _check_scopes: Validates gears:write scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        Created GearRead record.

    Raises:
        HTTPException: If unauthorized or gear
            already exists.
    """
    return gears_crud.create_gear(
        gear, token_user_id, db,
    )


@router.put(
    "/{gear_id}",
    response_model=gears_schema.GearRead,
    status_code=status.HTTP_200_OK,
)
async def edit_gear(
    gear_id: int,
    validate_id: Annotated[
        Callable,
        Depends(
            gears_dependencies.validate_gear_id,
        ),
    ],
    gear: gears_schema.GearUpdate,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gears_schema.GearRead:
    """
    Update an existing gear by ID.

    Args:
        gear_id: Gear ID to update.
        validate_id: Validates gear ID exists.
        gear: Updated gear data.
        _check_scopes: Validates gears:write scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        Updated GearRead record.

    Raises:
        HTTPException: If gear not found, forbidden,
            or unauthorized.
    """
    gear_db = gears_crud.get_gear_user_by_id(
        token_user_id, gear_id, db,
    )

    if gear_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Gear ID {gear_id} not found"
            ),
        )

    if gear_db.user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Gear ID {gear_id} does not "
                f"belong to user {token_user_id}"
            ),
        )

    return gears_crud.edit_gear(
        gear_id, gear, db,
    )


@router.delete(
    "/{gear_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_gear(
    gear_id: int,
    validate_id: Annotated[
        Callable,
        Depends(
            gears_dependencies.validate_gear_id,
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_security.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_security
            .get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete a gear by ID.

    Args:
        gear_id: Gear ID to delete.
        validate_id: Validates gear ID exists.
        _check_scopes: Validates gears:write scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If gear not found, forbidden,
            or unauthorized.
    """
    gear = gears_crud.get_gear_user_by_id(
        token_user_id, gear_id, db,
    )

    if gear is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Gear ID {gear_id} not found"
            ),
        )

    if gear.user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Gear ID {gear_id} does not "
                f"belong to user {token_user_id}"
            ),
        )

    gears_crud.delete_gear(gear_id, db)
