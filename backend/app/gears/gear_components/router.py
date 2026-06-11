"""Gear components API router endpoints."""

from collections.abc import Callable
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
)
from sqlalchemy.orm import Session

import auth.dependencies as auth_dependencies
import core.database as core_database
import gears.gear.dependencies as gear_deps
import gears.gear_components.crud as gc_crud
import gears.gear_components.dependencies as gc_deps
import gears.gear_components.schema as gc_schema

# Define the API router
router = APIRouter()


@router.get(
    "/types",
    response_model=gc_schema.GearComponentTypesRead,
    status_code=status.HTTP_200_OK,
)
async def read_gear_component_types(
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:read"],
        ),
    ],
) -> gc_schema.GearComponentTypesRead:
    """
    Retrieve valid component type lists.

    Args:
        _check_scopes: Validates gears:read scope.

    Returns:
        Component types grouped by gear type.

    Raises:
        HTTPException: If unauthorized.
    """
    return gc_schema.GearComponentTypesRead(
        bike=gc_schema.BIKE_COMPONENT_TYPES,
        shoes=gc_schema.SHOES_COMPONENT_TYPES,
        racquet=(gc_schema.RACQUET_COMPONENT_TYPES),
        windsurf=(gc_schema.WINDSURF_COMPONENT_TYPES),
    )


@router.get(
    "",
    response_model=(list[gc_schema.GearComponentRead] | None),
    status_code=status.HTTP_200_OK,
)
async def read_gear_components(
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_dependencies.get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> list[gc_schema.GearComponentRead] | None:
    """
    Retrieve all gear components for a user.

    Args:
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        List of gear component records or None.

    Raises:
        HTTPException: If unauthorized.
    """
    return gc_crud.get_gear_components_user(
        token_user_id,
        db,
    )


@router.get(
    "/gear_id/{gear_id}",
    response_model=(list[gc_schema.GearComponentRead] | None),
    status_code=status.HTTP_200_OK,
)
async def read_gear_components_gear_id(
    gear_id: int,
    validate_gear_id: Annotated[
        Callable,
        Depends(
            gear_deps.validate_gear_id,
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:read"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_dependencies.get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
    active: bool | None = None,
) -> list[gc_schema.GearComponentRead] | None:
    """
    Retrieve gear components by gear ID.

    Args:
        gear_id: Gear ID to filter by.
        validate_gear_id: Validates gear ID.
        _check_scopes: Validates gears:read scope.
        token_user_id: Authenticated user ID.
        db: Database session.
        active: Optional active-status filter.

    Returns:
        List of gear component records or None.

    Raises:
        HTTPException: If unauthorized.
    """
    components = gc_crud.get_gear_components_user_by_gear_id(
        token_user_id,
        gear_id,
        db,
        active=active,
    )
    if not components:
        return components

    stats = gc_crud.get_components_activity_stats(
        gear_id,
        db,
    )

    result: list[gc_schema.GearComponentRead] = []
    for comp in components:
        comp_read = gc_schema.GearComponentRead.model_validate(comp)
        comp_stats = stats.get(comp.id, {})
        comp_read.current_distance = comp_stats.get("distance", 0)
        comp_read.current_time = comp_stats.get("time", 0)
        result.append(comp_read)

    return result


@router.post(
    "",
    response_model=gc_schema.GearComponentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_gear_component(
    gear_component: gc_schema.GearComponentCreate,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    verify_gear_type: Annotated[
        Callable,
        Security(
            gc_deps.validate_gear_component_type,
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_dependencies.get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gc_schema.GearComponentRead:
    """
    Create a new gear component.

    Args:
        gear_component: Gear component data.
        _check_scopes: Validates gears:write scope.
        verify_gear_type: Validates component type.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        Created gear component record.

    Raises:
        HTTPException: If unauthorized or invalid
            component type.
    """
    return gc_crud.create_gear_component(
        gear_component,
        token_user_id,
        db,
    )


@router.put(
    "",
    response_model=gc_schema.GearComponentRead,
    status_code=status.HTTP_200_OK,
)
async def edit_gear_component(
    gear_component: gc_schema.GearComponentUpdate,
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_dependencies.get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> gc_schema.GearComponentRead:
    """
    Update an existing gear component.

    Args:
        gear_component: Updated component data.
        _check_scopes: Validates gears:write scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        Updated gear component record.

    Raises:
        HTTPException: If not found, forbidden,
            or invalid dates.
    """
    if (
        gear_component.retired_date is not None
        and gear_component.purchase_date is not None
        and gear_component.retired_date <= gear_component.purchase_date
    ):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=("Retired date must be after purchase date"),
        )

    gear_component_db = gc_crud.get_gear_component_by_id(
        gear_component.id,
        db,
    )

    if gear_component_db is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=(f"Gear component ID {gear_component.id} not found"),
        )

    if gear_component_db.user_id != token_user_id:
        raise HTTPException(
            status_code=(status.HTTP_403_FORBIDDEN),
            detail=(f"Gear component ID {gear_component.id} does not belong to user {token_user_id}"),
        )

    return gc_crud.edit_gear_component(
        gear_component,
        db,
    )


@router.delete(
    "/{gear_component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_component_gear(
    gear_component_id: int,
    validate_id: Annotated[
        Callable,
        Depends(
            gc_deps.validate_gear_component_id,
        ),
    ],
    _check_scopes: Annotated[
        Callable,
        Security(
            auth_dependencies.check_scopes,
            scopes=["gears:write"],
        ),
    ],
    token_user_id: Annotated[
        int,
        Depends(
            auth_dependencies.get_sub_from_access_token,
        ),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete a gear component by ID.

    Args:
        gear_component_id: Component ID to delete.
        validate_id: Validates component ID.
        _check_scopes: Validates gears:write scope.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If not found, forbidden,
            or unauthorized.
    """
    gear_component = gc_crud.get_gear_component_by_id(
        gear_component_id,
        db,
    )

    if gear_component is None:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=(f"Gear component ID {gear_component_id} not found"),
        )

    if gear_component.user_id != token_user_id:
        raise HTTPException(
            status_code=(status.HTTP_403_FORBIDDEN),
            detail=(f"Gear component ID {gear_component_id} does not belong to user {token_user_id}"),
        )

    gc_crud.delete_gear_component(
        token_user_id,
        gear_component_id,
        db,
    )
