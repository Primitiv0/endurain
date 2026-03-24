"""CRUD operations for gear components."""

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

import gears.gear_components.schema as gear_components_schema
import gears.gear_components.models as gear_components_models
import activities.activity.models as activity_models

import core.decorators as core_decorators

# Fields that must never be overwritten via
# user-supplied data during updates.
_IMMUTABLE_FIELDS: set[str] = {
    "id",
    "user_id",
    "gear_id",
}


@core_decorators.handle_db_errors
def get_gear_component_by_id(
    gear_component_id: int,
    db: Session,
) -> gear_components_models.GearComponents | None:
    """
    Retrieve a gear component by its ID.

    Args:
        gear_component_id: Primary key.
        db: Database session.

    Returns:
        ORM gear component or None.

    Raises:
        HTTPException: On database error (500).
    """
    stmt = select(
        gear_components_models.GearComponents,
    ).where(
        gear_components_models.GearComponents.id
        == gear_component_id,
    )
    return (
        db.execute(stmt).scalar_one_or_none()
    )


@core_decorators.handle_db_errors
def get_gear_components_user(
    user_id: int,
    db: Session,
) -> list[gear_components_models.GearComponents]:
    """
    Retrieve all gear components for a user.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        List of ORM gear components.

    Raises:
        HTTPException: On database error (500).
    """
    stmt = select(
        gear_components_models.GearComponents,
    ).where(
        gear_components_models.GearComponents
        .user_id
        == user_id,
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_gear_components_user_by_gear_id(
    user_id: int,
    gear_id: int,
    db: Session,
    active: bool | None = None,
) -> list[gear_components_models.GearComponents]:
    """
    Retrieve gear components by user and gear.

    Args:
        user_id: Owner user ID.
        gear_id: Gear ID to filter by.
        db: Database session.
        active: Optional active-status filter.

    Returns:
        List of ORM gear components.

    Raises:
        HTTPException: On database error (500).
    """
    stmt = select(
        gear_components_models.GearComponents,
    ).where(
        gear_components_models.GearComponents
        .user_id
        == user_id,
        gear_components_models.GearComponents
        .gear_id
        == gear_id,
    )
    if active is not None:
        stmt = stmt.where(
            gear_components_models
            .GearComponents.active
            == active,
        )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def create_gear_component(
    gear_component: (
        gear_components_schema.GearComponentCreate
    ),
    user_id: int,
    db: Session,
) -> gear_components_models.GearComponents:
    """
    Create a new gear component.

    Args:
        gear_component: Create schema data.
        user_id: Authenticated user ID (token).
        db: Database session.

    Returns:
        Created ORM gear component.

    Raises:
        HTTPException: On database error (500).
    """
    new_gear_component = (
        gear_components_models.GearComponents(
            user_id=user_id,
            gear_id=gear_component.gear_id,
            type=gear_component.type,
            brand=gear_component.brand,
            model=gear_component.model,
            purchase_date=(
                gear_component.purchase_date
            ),
            active=True,
            expected_kms=(
                gear_component.expected_kms
            ),
            purchase_value=(
                gear_component.purchase_value
            ),
        )
    )

    db.add(new_gear_component)
    db.commit()
    db.refresh(new_gear_component)

    return new_gear_component


@core_decorators.handle_db_errors
def edit_gear_component(
    gear_component: (
        gear_components_schema.GearComponentUpdate
    ),
    db: Session,
) -> gear_components_models.GearComponents:
    """
    Edit an existing gear component by ID.

    Args:
        gear_component: Update schema data.
        db: Database session.

    Returns:
        Updated ORM gear component.

    Raises:
        HTTPException: If not found (404) or
            database error (500).
    """
    stmt = select(
        gear_components_models.GearComponents,
    ).where(
        gear_components_models.GearComponents.id
        == gear_component.id,
    )
    db_gear_component = (
        db.execute(stmt).scalar_one_or_none()
    )

    if db_gear_component is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Gear component not found",
        )

    gear_component_data = (
        gear_component.model_dump(
            exclude_unset=True,
        )
    )
    for key, value in gear_component_data.items():
        if key not in _IMMUTABLE_FIELDS:
            setattr(db_gear_component, key, value)

    # Enforce retired_date / active invariant.
    if db_gear_component.retired_date is not None:
        db_gear_component.active = False
    elif "retired_date" in gear_component_data:
        # retired_date explicitly cleared.
        db_gear_component.active = True

    db.commit()
    db.refresh(db_gear_component)

    return db_gear_component


@core_decorators.handle_db_errors
def delete_gear_component(
    user_id: int,
    gear_component_id: int,
    db: Session,
) -> None:
    """
    Delete a gear component by user and ID.

    Args:
        user_id: Owner user ID.
        gear_component_id: Component ID to delete.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If not found (404) or
            database error (500).
    """
    stmt = delete(
        gear_components_models.GearComponents,
    ).where(
        gear_components_models.GearComponents
        .user_id
        == user_id,
        gear_components_models.GearComponents.id
        == gear_component_id,
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                f"Gear component with ID "
                f"{gear_component_id} not found"
            ),
        )

    db.commit()


@core_decorators.handle_db_errors
def get_components_activity_stats(
    gear_id: int,
    db: Session,
) -> dict[int, dict[str, float]]:
    """
    Get per-component activity stats for a gear.

    Computes distance and time accumulated
    between each component's purchase_date
    and retired_date from the gear's activities.

    Args:
        gear_id: Gear ID to query.
        db: Database session.

    Returns:
        Dict mapping component ID to
        {distance, time} in meters/seconds.

    Raises:
        HTTPException: On database error.
    """
    comp = (
        select(
            gear_components_models.GearComponents.id
            .label("comp_id"),
            gear_components_models
            .GearComponents.purchase_date,
            gear_components_models
            .GearComponents.retired_date,
        )
        .where(
            gear_components_models.GearComponents.gear_id
            == gear_id,
        )
        .subquery()
    )

    stmt = (
        select(
            comp.c.comp_id,
            func.coalesce(
                func.sum(
                    activity_models
                    .Activity.distance
                ),
                0,
            ).label("distance"),
            func.coalesce(
                func.sum(
                    activity_models
                    .Activity.total_timer_time
                ),
                0,
            ).label("time"),
        )
        .select_from(comp)
        .outerjoin(
            activity_models.Activity,
            (
                activity_models.Activity.gear_id
                == gear_id
            )
            & (
                activity_models
                .Activity.start_time
                >= comp.c.purchase_date
            )
            & (
                (comp.c.retired_date.is_(None))
                | (
                    activity_models
                    .Activity.start_time
                    <= comp.c.retired_date
                )
            ),
        )
        .group_by(comp.c.comp_id)
    )

    rows = db.execute(stmt).all()
    return {
        row.comp_id: {
            "distance": float(row.distance),
            "time": float(row.time),
        }
        for row in rows
    }
