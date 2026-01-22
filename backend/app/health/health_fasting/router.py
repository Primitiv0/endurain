"""
FastAPI router for health fasting endpoints.

This module defines the API endpoints for managing fasting sessions,
including CRUD operations, active fast tracking, and statistics.
"""

from typing import Annotated, Callable
from datetime import timedelta

from fastapi import APIRouter, Depends, Security, HTTPException, status
from sqlalchemy.orm import Session

import health.health_fasting.schema as health_fasting_schema
import health.health_fasting.crud as health_fasting_crud

import auth.security as auth_security

import core.database as core_database
import core.dependencies as core_dependencies

# Define the API router
router = APIRouter()


@router.get(
    "",
    response_model=health_fasting_schema.HealthFastingListResponse,
    status_code=status.HTTP_200_OK,
)
async def read_health_fasting_all(
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingListResponse:
    """
    Retrieve all fasting records for the authenticated user.

    Args:
        _check_scopes: Security dependency for health:read scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        HealthFastingListResponse with total count and all records.
    """
    total = health_fasting_crud.get_health_fasting_number(token_user_id, db)
    records = health_fasting_crud.get_all_health_fasting_by_user_id(token_user_id, db)

    return health_fasting_schema.HealthFastingListResponse(
        total=total, records=records  # type: ignore[arg-type]
    )


@router.get(
    "/page_number/{page_number}/num_records/{num_records}",
    response_model=health_fasting_schema.HealthFastingListResponse,
    status_code=status.HTTP_200_OK,
)
async def read_health_fasting_all_pagination(
    page_number: int,
    num_records: int,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    _validate_pagination_values: Annotated[
        Callable, Depends(core_dependencies.validate_pagination_values)
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingListResponse:
    """
    Retrieve paginated fasting records for the authenticated user.

    Args:
        page_number: Page number to retrieve (1-indexed).
        num_records: Number of records per page.
        _check_scopes: Security dependency for health:read scope.
        _validate_pagination_values: Validates pagination parameters.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        HealthFastingListResponse with paginated records.
    """
    total = health_fasting_crud.get_health_fasting_number(token_user_id, db)
    records = health_fasting_crud.get_health_fasting_with_pagination(
        token_user_id, db, page_number, num_records
    )

    return health_fasting_schema.HealthFastingListResponse(
        total=total,
        num_records=num_records,
        page_number=page_number,
        records=records,  # type: ignore[arg-type]
    )


@router.get(
    "/active",
    response_model=health_fasting_schema.HealthFastingRead | None,
    status_code=status.HTTP_200_OK,
)
async def read_active_fasting(
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingRead | None:
    """
    Retrieve the active fasting session for the authenticated user.

    Args:
        _check_scopes: Security dependency for health:read scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        Active HealthFastingRead if exists, None otherwise.
    """
    return health_fasting_crud.get_active_fasting_by_user_id(token_user_id, db)


@router.get(
    "/stats",
    response_model=health_fasting_schema.HealthFastingStatsResponse,
    status_code=status.HTTP_200_OK,
)
async def read_fasting_stats(
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingStatsResponse:
    """
    Retrieve fasting statistics for the authenticated user.

    Args:
        _check_scopes: Security dependency for health:read scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        HealthFastingStatsResponse with statistics.
    """
    total_fasts = health_fasting_crud.get_completed_fasting_count(token_user_id, db)
    total_fasting_seconds = health_fasting_crud.get_total_fasting_seconds(
        token_user_id, db
    )
    avg_duration = health_fasting_crud.get_avg_fasting_duration(token_user_id, db)

    # Calculate streaks
    current_streak, longest_streak = _calculate_streaks(token_user_id, db)

    # Calculate completion rate
    total_started = health_fasting_crud.get_health_fasting_number(token_user_id, db)
    completion_rate = (total_fasts / total_started * 100) if total_started > 0 else 0.0

    return health_fasting_schema.HealthFastingStatsResponse(
        total_fasts=total_fasts,
        current_streak=current_streak,
        longest_streak=longest_streak,
        avg_duration_seconds=avg_duration,
        total_fasting_seconds=total_fasting_seconds,
        completion_rate=round(completion_rate, 1),
    )


def _calculate_streaks(user_id: int, db: Session) -> tuple[int, int]:
    """
    Calculate current and longest fasting streaks.

    Args:
        user_id: User ID to calculate streaks for.
        db: Database session.

    Returns:
        Tuple of (current_streak, longest_streak).
    """
    completed_fasts = health_fasting_crud.get_completed_fasting_ordered_by_date(
        user_id, db
    )

    if not completed_fasts:
        return 0, 0

    # Get unique dates
    dates = sorted(set(fast.date for fast in completed_fasts))

    if not dates:
        return 0, 0

    longest_streak = 1
    current_streak = 1
    temp_streak = 1

    for i in range(1, len(dates)):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 1

    # Check if current streak is still active (last fast was today or yesterday)
    from datetime import date

    today = date.today()
    last_fast_date = dates[-1]

    if last_fast_date == today or last_fast_date == today - timedelta(days=1):
        # Count backwards from the end
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if dates[i] - dates[i - 1] == timedelta(days=1):
                current_streak += 1
            else:
                break
    else:
        current_streak = 0

    return current_streak, longest_streak


@router.get(
    "/{health_fasting_id}",
    response_model=health_fasting_schema.HealthFastingRead,
    status_code=status.HTTP_200_OK,
)
async def read_health_fasting_by_id(
    health_fasting_id: int,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:read"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingRead:
    """
    Retrieve a specific fasting record by ID.

    Args:
        health_fasting_id: ID of the fasting record.
        _check_scopes: Security dependency for health:read scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        HealthFastingRead for the specified record.

    Raises:
        HTTPException: If record not found.
    """
    record = health_fasting_crud.get_health_fasting_by_id_and_user_id(
        health_fasting_id, token_user_id, db
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fasting record not found",
        )

    return record  # type: ignore[return-value]


@router.post(
    "",
    response_model=health_fasting_schema.HealthFastingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_health_fasting(
    health_fasting: health_fasting_schema.HealthFastingCreate,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:write"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingRead:
    """
    Create a new fasting session.

    Args:
        health_fasting: Fasting data to create.
        _check_scopes: Security dependency for health:write scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        Created HealthFastingRead record.

    Raises:
        HTTPException: If user already has an active fast.
    """
    # Check if user already has an active fast
    active_fast = health_fasting_crud.get_active_fasting_by_user_id(token_user_id, db)

    if active_fast is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active fasting session. "
            "Complete or cancel it before starting a new one.",
        )

    return health_fasting_crud.create_health_fasting(token_user_id, health_fasting, db)


@router.put(
    "",
    response_model=health_fasting_schema.HealthFastingRead,
    status_code=status.HTTP_200_OK,
)
async def edit_health_fasting(
    health_fasting: health_fasting_schema.HealthFastingUpdate,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:write"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingRead:
    """
    Edit an existing fasting record.

    Args:
        health_fasting: Fasting data to update.
        _check_scopes: Security dependency for health:write scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        Updated HealthFastingRead record.
    """
    return health_fasting_crud.edit_health_fasting(token_user_id, health_fasting, db)


@router.post(
    "/{health_fasting_id}/complete",
    response_model=health_fasting_schema.HealthFastingRead,
    status_code=status.HTTP_200_OK,
)
async def complete_health_fasting(
    health_fasting_id: int,
    complete_data: health_fasting_schema.HealthFastingComplete,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:write"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> health_fasting_schema.HealthFastingRead:
    """
    Complete or end a fasting session.

    Args:
        health_fasting_id: ID of the fasting record to complete.
        complete_data: Completion data with end time and status.
        _check_scopes: Security dependency for health:write scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.

    Returns:
        Updated HealthFastingRead record.
    """
    return health_fasting_crud.complete_health_fasting(
        token_user_id, health_fasting_id, complete_data, db
    )


@router.delete(
    "/{health_fasting_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_health_fasting(
    health_fasting_id: int,
    _check_scopes: Annotated[
        Callable, Security(auth_security.check_scopes, scopes=["health:write"])
    ],
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete a fasting record.

    Args:
        health_fasting_id: ID of the fasting record to delete.
        _check_scopes: Security dependency for health:write scope.
        token_user_id: User ID from the access token.
        db: Database session dependency.
    """
    health_fasting_crud.delete_health_fasting(token_user_id, health_fasting_id, db)
