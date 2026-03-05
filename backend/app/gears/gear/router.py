from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from sqlalchemy.orm import Session

import auth.security as auth_security

import gears.gear.schema as gears_schema
import gears.gear.crud as gears_crud
import gears.gear.dependencies as gears_dependencies

import core.database as core_database
import core.dependencies as core_dependencies

# Define the API router
router = APIRouter()

@router.get(
    "",
    response_model=gears_schema.GearsListResponse,
)
async def read_gears_user_all_pagination(
    _validate_pagination_values_on_query: Annotated[
        Callable, Depends(core_dependencies.validate_pagination_values_on_query)
    ],
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:read"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
    page_number: Annotated[
        int | None,
        Query(description="Pagination page number"),
    ] = None,
    num_records: Annotated[
        int | None,
        Query(description="Number of records per page"),
    ] = None,
    show_inactive: Annotated[
        bool | None,
        Query(description="Filter by inactive status"),
    ] = None,
):
    total = gears_crud.get_gears_number(db)
    gears = gears_crud.get_gear_users_with_pagination(
        token_user_id, db, page_number, num_records, show_inactive
    )

    return gears_schema.GearsListResponse(
        total=total,
        num_records=num_records,
        page_number=page_number,
        records=gears,
    )


@router.get(
    "/nickname/contains/{nickname}",
    response_model=list[gears_schema.Gear] | None,
)
async def read_gear_user_contains_nickname(
    nickname: str,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:read"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Return the gears
    return gears_crud.get_gear_user_contains_nickname(token_user_id, nickname, db)


@router.get(
    "/nickname/{nickname}",
    response_model=gears_schema.Gear | None,
)
async def read_gear_user_by_nickname(
    nickname: str,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:read"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Return the gear
    return gears_crud.get_gear_user_by_nickname(token_user_id, nickname, db)


@router.get(
    "/type/{gear_type}",
    response_model=list[gears_schema.Gear] | None,
)
async def read_gear_user_by_type(
    gear_type: int,
    validate_type: Annotated[Callable, Depends(gears_dependencies.validate_gear_type)],
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:read"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Return the gear
    return gears_crud.get_gear_by_type_and_user(gear_type, token_user_id, db)


@router.post(
    "",
    response_model=gears_schema.Gear,
    status_code=201,
)
async def create_gear(
    gear: gears_schema.Gear,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:write"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Create the gear and return it
    return gears_crud.create_gear(gear, token_user_id, db)


@router.put("/{gear_id}")
async def edit_gear(
    gear_id: int,
    validate_id: Annotated[Callable, Depends(gears_dependencies.validate_gear_id)],
    gear: gears_schema.Gear,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:write"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Get the gear by id
    gear_db = gears_crud.get_gear_user_by_id(token_user_id, gear_id, db)

    # Check if gear is None and raise an HTTPException if it is
    if gear_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gear ID {gear_id} not found",
        )

    if gear_db.user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Gear ID {gear_id} does not belong to user {token_user_id}",
        )

    # Edit the gear
    gears_crud.edit_gear(gear_id, gear, db)

    # Return success message
    return {"detail": f"Gear ID {gear_id} edited successfully"}


@router.delete("/{gear_id}")
async def delete_gear(
    gear_id: int,
    validate_id: Annotated[Callable, Depends(gears_dependencies.validate_gear_id)],
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["gears:write"])
    ],
    token_user_id: Annotated[int, Depends(auth_security.get_sub_from_access_token)],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
):
    # Get the gear by id
    gear = gears_crud.get_gear_user_by_id(token_user_id, gear_id, db)

    # Check if gear is None and raise an HTTPException if it is
    if gear is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gear ID {gear_id} not found",
        )

    if gear.user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Gear ID {gear_id} does not belong to user {token_user_id}",
        )

    # Delete the gear
    gears_crud.delete_gear(gear_id, db)

    # Return success message
    return {"detail": f"Gear ID {gear_id} deleted successfully"}
