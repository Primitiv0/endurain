"""
CRUD operations for health fasting records.

This module provides database operations for creating, reading, updating,
and deleting fasting session records.
"""

from fastapi import HTTPException, status
from sqlalchemy import func, desc, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import health.health_fasting.schema as health_fasting_schema
import health.health_fasting.models as health_fasting_models

import core.decorators as core_decorators


@core_decorators.handle_db_errors
def get_health_fasting_number(user_id: int, db: Session) -> int:
    """
    Retrieve total count of fasting records for a user.

    Args:
        user_id: User ID to count records for.
        db: Database session.

    Returns:
        Total number of fasting records.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(func.count())
        .select_from(health_fasting_models.HealthFasting)
        .where(health_fasting_models.HealthFasting.user_id == user_id)
    )
    return db.execute(stmt).scalar_one()


@core_decorators.handle_db_errors
def get_all_health_fasting_by_user_id(
    user_id: int, db: Session
) -> list[health_fasting_models.HealthFasting]:
    """
    Retrieve all fasting records for a user.

    Args:
        user_id: User ID to fetch records for.
        db: Database session.

    Returns:
        List of HealthFasting models ordered by date descending.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(health_fasting_models.HealthFasting)
        .where(health_fasting_models.HealthFasting.user_id == user_id)
        .order_by(desc(health_fasting_models.HealthFasting.date))
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_health_fasting_by_id_and_user_id(
    health_fasting_id: int, user_id: int, db: Session
) -> health_fasting_models.HealthFasting | None:
    """
    Retrieve fasting record by ID and user ID.

    Args:
        health_fasting_id: Fasting record ID to fetch.
        user_id: User ID to fetch record for.
        db: Database session.

    Returns:
        HealthFasting model if found, None otherwise.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = select(health_fasting_models.HealthFasting).where(
        health_fasting_models.HealthFasting.id == health_fasting_id,
        health_fasting_models.HealthFasting.user_id == user_id,
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def get_health_fasting_with_pagination(
    user_id: int,
    db: Session,
    page_number: int = 1,
    num_records: int = 5,
) -> list[health_fasting_models.HealthFasting]:
    """
    Retrieve paginated fasting records for a user.

    Args:
        user_id: User ID to fetch records for.
        db: Database session.
        page_number: Page number to retrieve (1-indexed).
        num_records: Number of records per page.

    Returns:
        List of HealthFasting models for the requested page.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(health_fasting_models.HealthFasting)
        .where(health_fasting_models.HealthFasting.user_id == user_id)
        .order_by(desc(health_fasting_models.HealthFasting.date))
        .offset((page_number - 1) * num_records)
        .limit(num_records)
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_active_fasting_by_user_id(
    user_id: int, db: Session
) -> health_fasting_models.HealthFasting | None:
    """
    Retrieve the active (in_progress) fasting session for a user.

    Args:
        user_id: User ID to fetch active fast for.
        db: Database session.

    Returns:
        HealthFasting model if active fast exists, None otherwise.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(health_fasting_models.HealthFasting)
        .where(
            health_fasting_models.HealthFasting.user_id == user_id,
            health_fasting_models.HealthFasting.status == "in_progress",
        )
        .order_by(desc(health_fasting_models.HealthFasting.fast_start_time_utc))
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def get_completed_fasting_count(user_id: int, db: Session) -> int:
    """
    Get the count of completed fasting sessions for a user.

    Args:
        user_id: User ID to count completed fasts for.
        db: Database session.

    Returns:
        Number of completed fasting sessions.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(func.count())
        .select_from(health_fasting_models.HealthFasting)
        .where(
            health_fasting_models.HealthFasting.user_id == user_id,
            health_fasting_models.HealthFasting.status == "completed",
        )
    )
    return db.execute(stmt).scalar_one()


@core_decorators.handle_db_errors
def get_total_fasting_seconds(user_id: int, db: Session) -> int:
    """
    Get total fasting duration in seconds for a user.

    Args:
        user_id: User ID to calculate total for.
        db: Database session.

    Returns:
        Total fasting duration in seconds.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(
            func.coalesce(
                func.sum(health_fasting_models.HealthFasting.actual_duration_seconds), 0
            )
        )
        .select_from(health_fasting_models.HealthFasting)
        .where(
            health_fasting_models.HealthFasting.user_id == user_id,
            health_fasting_models.HealthFasting.status == "completed",
        )
    )
    return db.execute(stmt).scalar_one()


@core_decorators.handle_db_errors
def get_avg_fasting_duration(user_id: int, db: Session) -> int | None:
    """
    Get average fasting duration in seconds for a user.

    Args:
        user_id: User ID to calculate average for.
        db: Database session.

    Returns:
        Average fasting duration in seconds, None if no data.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(func.avg(health_fasting_models.HealthFasting.actual_duration_seconds))
        .select_from(health_fasting_models.HealthFasting)
        .where(
            health_fasting_models.HealthFasting.user_id == user_id,
            health_fasting_models.HealthFasting.status == "completed",
        )
    )
    result = db.execute(stmt).scalar_one()
    return int(result) if result else None


@core_decorators.handle_db_errors
def get_completed_fasting_ordered_by_date(
    user_id: int, db: Session
) -> list[health_fasting_models.HealthFasting]:
    """
    Get all completed fasting sessions ordered by date ascending.

    Args:
        user_id: User ID to fetch records for.
        db: Database session.

    Returns:
        List of completed HealthFasting models ordered by date.

    Raises:
        HTTPException: If database error occurs.
    """
    stmt = (
        select(health_fasting_models.HealthFasting)
        .where(
            health_fasting_models.HealthFasting.user_id == user_id,
            health_fasting_models.HealthFasting.status == "completed",
        )
        .order_by(health_fasting_models.HealthFasting.date)
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def create_health_fasting(
    user_id: int,
    health_fasting: health_fasting_schema.HealthFastingCreate,
    db: Session,
) -> health_fasting_models.HealthFasting:
    """
    Create a new fasting session for a user.

    Args:
        user_id: User ID to create the fasting session for.
        health_fasting: Fasting data to create.
        db: Database session.

    Returns:
        Created HealthFasting model.

    Raises:
        HTTPException: If database error or duplicate entry.
    """
    try:
        db_health_fasting = health_fasting_models.HealthFasting(
            **health_fasting.model_dump(exclude_none=False),
            user_id=user_id,
        )

        db.add(db_health_fasting)
        db.commit()
        db.refresh(db_health_fasting)

        return db_health_fasting
    except IntegrityError as integrity_error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Failed to create fasting record. Database integrity error.",
        ) from integrity_error


@core_decorators.handle_db_errors
def edit_health_fasting(
    user_id: int,
    health_fasting: health_fasting_schema.HealthFastingUpdate,
    db: Session,
) -> health_fasting_models.HealthFasting:
    """
    Edit an existing fasting record for a user.

    Args:
        user_id: User ID who owns the fasting record.
        health_fasting: Fasting data to update.
        db: Database session.

    Returns:
        Updated HealthFasting model.

    Raises:
        HTTPException: If record not found or permission denied.
    """
    if health_fasting.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit fasting record for another user.",
        )

    db_health_fasting = get_health_fasting_by_id_and_user_id(
        health_fasting.id, user_id, db
    )

    if db_health_fasting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fasting record not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    health_fasting_data = health_fasting.model_dump(exclude_unset=True)
    for key, value in health_fasting_data.items():
        setattr(db_health_fasting, key, value)

    db.commit()
    db.refresh(db_health_fasting)

    return db_health_fasting


@core_decorators.handle_db_errors
def complete_health_fasting(
    user_id: int,
    health_fasting_id: int,
    complete_data: health_fasting_schema.HealthFastingComplete,
    db: Session,
) -> health_fasting_models.HealthFasting:
    """
    Complete or end a fasting session.

    Args:
        user_id: User ID who owns the fasting record.
        health_fasting_id: ID of the fasting record to complete.
        complete_data: Completion data including end time and status.
        db: Database session.

    Returns:
        Updated HealthFasting model.

    Raises:
        HTTPException: If record not found or not in progress.
    """
    db_health_fasting = get_health_fasting_by_id_and_user_id(
        health_fasting_id, user_id, db
    )

    if db_health_fasting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fasting record not found",
        )

    if db_health_fasting.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fasting session is not in progress",
        )

    # Calculate actual duration
    start_time = db_health_fasting.fast_start_time_utc
    end_time = complete_data.fast_end_time_utc
    actual_duration = int((end_time - start_time).total_seconds())

    # Update the record
    db_health_fasting.fast_end_time_utc = complete_data.fast_end_time_utc
    db_health_fasting.fast_end_time_local = complete_data.fast_end_time_local
    db_health_fasting.status = complete_data.status
    db_health_fasting.actual_duration_seconds = actual_duration
    if complete_data.notes:
        db_health_fasting.notes = complete_data.notes

    db.commit()
    db.refresh(db_health_fasting)

    return db_health_fasting


@core_decorators.handle_db_errors
def delete_health_fasting(user_id: int, health_fasting_id: int, db: Session) -> None:
    """
    Delete a fasting record for a user.

    Args:
        user_id: User ID who owns the fasting record.
        health_fasting_id: Fasting record ID to delete.
        db: Database session.

    Returns:
        None

    Raises:
        HTTPException: If record not found.
    """
    db_health_fasting = get_health_fasting_by_id_and_user_id(
        health_fasting_id, user_id, db
    )

    if db_health_fasting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Fasting record with id {health_fasting_id} "
                f"for user {user_id} not found"
            ),
        )

    db.delete(db_health_fasting)
    db.commit()
