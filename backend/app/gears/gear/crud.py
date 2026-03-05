from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from urllib.parse import unquote

import gears.gear.schema as gears_schema
import gears.gear.utils as gears_utils
import gears.gear.models as gears_models

import core.decorators as core_decorators
import core.logger as core_logger


@core_decorators.handle_db_errors
def get_gear_user_by_id(
    user_id: int, gear_id: int, db: Session
) -> gears_models.Gear | None:
    """
    Retrieve a gear by ID for a specific user.

    Args:
        user_id: Owner user ID.
        gear_id: Gear ID to fetch.
        db: Database session.

    Returns:
        Gear model if found, None otherwise.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
        gears_models.Gear.id == gear_id,
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def get_gears_number(db: Session) -> int:
    """
    Get total count of gears in the database.

    Args:
        db: Database session.

    Returns:
        Total number of gears.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(func.count(gears_models.Gear.id))
    return db.execute(stmt).scalar_one()


@core_decorators.handle_db_errors
def get_gear_users_with_pagination(
    user_id: int,
    db: Session,
    page_number: int | None = None,
    num_records: int | None = None,
    show_inactive: bool | None = True,
) -> list[gears_models.Gear]:
    """
    Retrieve paginated gears for a user.

    Args:
        user_id: Owner user ID.
        db: Database session.
        page_number: Page number (1-indexed). Defaults to None.
        num_records: Records per page. Defaults to None.
        show_inactive: Include inactive gears. Defaults to True.

    Returns:
        List of Gear models ordered by nickname.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
    )

    if show_inactive is False:
        stmt = stmt.where(
            gears_models.Gear.active.is_(True),
        )

    stmt = stmt.order_by(gears_models.Gear.nickname)

    if (
        page_number is not None
        and num_records is not None
    ):
        stmt = stmt.offset(
            (page_number - 1) * num_records,
        ).limit(num_records)

    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_gear_user(
    user_id: int, db: Session
) -> list[gears_models.Gear]:
    """
    Retrieve all gears for a specific user.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        List of Gear models for the user.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_gear_user_contains_nickname(
    user_id: int, nickname: str, db: Session
) -> list[gears_models.Gear]:
    """
    Retrieve gears matching a nickname substring.

    Args:
        user_id: Owner user ID.
        nickname: Substring to search for.
        db: Database session.

    Returns:
        List of Gear models matching criteria.

    Raises:
        HTTPException: If a database error occurs.
    """
    parsed_nickname = (
        unquote(nickname)
        .replace("+", " ")
        .lower()
        .strip()
    )

    stmt = select(gears_models.Gear).where(
        func.lower(
            gears_models.Gear.nickname,
        ).like(f"%{parsed_nickname}%"),
        gears_models.Gear.user_id == user_id,
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_gear_user_by_nickname(
    user_id: int, nickname: str, db: Session
) -> gears_models.Gear | None:
    """
    Retrieve a gear by exact nickname for a user.

    Args:
        user_id: Owner user ID.
        nickname: Gear nickname to match.
        db: Database session.

    Returns:
        Gear model if found, None otherwise.

    Raises:
        HTTPException: If a database error occurs.
    """
    parsed_nickname = (
        unquote(nickname)
        .replace("+", " ")
        .lower()
        .strip()
    )

    stmt = select(gears_models.Gear).where(
        func.lower(
            gears_models.Gear.nickname,
        ) == parsed_nickname,
        gears_models.Gear.user_id == user_id,
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def get_gear_by_type_and_user(
    gear_type: int, user_id: int, db: Session
) -> list[gears_models.Gear]:
    """
    Retrieve gears by type for a specific user.

    Args:
        gear_type: Gear type identifier.
        user_id: Owner user ID.
        db: Database session.

    Returns:
        List of Gear models ordered by nickname.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = (
        select(gears_models.Gear)
        .where(
            gears_models.Gear.gear_type == gear_type,
            gears_models.Gear.user_id == user_id,
        )
        .order_by(gears_models.Gear.nickname)
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_gear_by_strava_id_from_user_id(
    gear_strava_id: str,
    user_id: int,
    db: Session,
) -> gears_models.Gear | None:
    """
    Retrieve a gear by Strava ID for a user.

    Args:
        gear_strava_id: Strava gear identifier.
        user_id: Owner user ID.
        db: Database session.

    Returns:
        Gear model if found, None otherwise.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
        gears_models.Gear.strava_gear_id
        == gear_strava_id,
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def get_gear_by_garminconnect_id_from_user_id(
    gear_garminconnect_id: str,
    user_id: int,
    db: Session,
) -> gears_models.Gear | None:
    """
    Retrieve a gear by Garmin Connect ID for a user.

    Args:
        gear_garminconnect_id: Garmin Connect gear ID.
        user_id: Owner user ID.
        db: Database session.

    Returns:
        Gear model if found, None otherwise.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
        gears_models.Gear.garminconnect_gear_id
        == gear_garminconnect_id,
    )
    return db.execute(stmt).scalar_one_or_none()


@core_decorators.handle_db_errors
def create_multiple_gears(
    gears: list[gears_schema.GearCreate],
    user_id: int,
    db: Session,
) -> None:
    """
    Create multiple gears for a user.

    Filters invalid entries, deduplicates by
    nickname, skips existing gears, and persists
    the rest.

    Args:
        gears: List of gear schemas to create.
        user_id: Owner user ID.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If a database or
            integrity error occurs.
    """
    # Filter out None and gears without a nickname
    valid_gears = [
        gear
        for gear in (gears or [])
        if gear is not None
        and getattr(gear, "nickname", None)
        and str(gear.nickname)
        .replace("+", " ")
        .strip()
    ]

    # De-dupe by nickname (case-insensitive)
    seen: set[str] = set()
    deduped: list[gears_schema.GearCreate] = []
    for gear in valid_gears:
        nickname_normalized = (
            str(gear.nickname)
            .replace("+", " ")
            .lower()
            .strip()
        )
        if nickname_normalized not in seen:
            seen.add(nickname_normalized)
            deduped.append(gear)
        else:
            core_logger.print_to_log_and_console(
                f"Duplicate nickname "
                f"'{gear.nickname}' in request "
                f"for user {user_id}, skipping",
                "warning",
            )

    # Skip any that already exist for this user
    gears_to_create: list[gears_schema.GearCreate] = []
    for gear in deduped:
        gear_check = get_gear_user_by_nickname(
            user_id, gear.nickname, db,
        )
        if gear_check is not None:
            core_logger.print_to_log_and_console(
                f"Gear with nickname "
                f"'{gear.nickname}' already exists "
                f"for user {user_id}, skipping",
                "warning",
            )
        else:
            gears_to_create.append(gear)

    # Persist any remaining
    if gears_to_create:
        new_gears = [
            gears_utils
            .transform_schema_gear_to_model_gear(
                gear, user_id,
            )
            for gear in gears_to_create
        ]
        try:
            db.add_all(new_gears)
            db.commit()
            for new_gear in new_gears:
                db.refresh(new_gear)
        except IntegrityError as integrity_err:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Duplicate entry error. Check "
                    "if strava_gear_id or "
                    "garminconnect_gear_id "
                    "are unique"
                ),
            ) from integrity_err


@core_decorators.handle_db_errors
def create_gear(
    gear: gears_schema.GearCreate,
    user_id: int,
    db: Session,
) -> gears_models.Gear:
    """
    Create a single gear for a user.

    Args:
        gear: Gear schema with data to create.
        user_id: Owner user ID.
        db: Database session.

    Returns:
        Created Gear model.

    Raises:
        HTTPException: If gear already exists or
            a database error occurs.
    """
    gear_check = get_gear_user_by_nickname(
        user_id, gear.nickname, db,
    )

    if gear_check is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Gear with nickname "
                f"{gear.nickname} already exists "
                f"for user {user_id}"
            ),
        )

    new_gear = (
        gears_utils
        .transform_schema_gear_to_model_gear(
            gear, user_id,
        )
    )

    try:
        db.add(new_gear)
        db.commit()
        db.refresh(new_gear)
    except IntegrityError as integrity_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Duplicate entry error. Check "
                "if strava_gear_id or "
                "garminconnect_gear_id "
                "are unique"
            ),
        ) from integrity_err

    return new_gear


@core_decorators.handle_db_errors
def edit_gear(
    gear_id: int,
    gear: gears_schema.GearBase,
    db: Session,
) -> gears_models.Gear:
    """
    Edit an existing gear by ID.

    Args:
        gear_id: Gear ID to edit.
        gear: Gear schema with updated fields.
        db: Database session.

    Returns:
        Updated Gear model.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(gears_models.Gear).where(
        gears_models.Gear.id == gear_id,
    )
    db_gear = db.execute(stmt).scalar_one_or_none()

    if gear.brand is not None:
        db_gear.brand = (
            unquote(gear.brand).replace("+", " ")
        )
    if gear.model is not None:
        db_gear.model = (
            unquote(gear.model).replace("+", " ")
        )
    if gear.nickname is not None:
        db_gear.nickname = (
            unquote(gear.nickname)
            .replace("+", " ")
        )
    if gear.gear_type is not None:
        db_gear.gear_type = gear.gear_type
    if gear.created_at is not None:
        db_gear.created_at = gear.created_at
    if gear.active is not None:
        db_gear.active = gear.active
    if gear.initial_kms is not None:
        db_gear.initial_kms = gear.initial_kms
    if gear.purchase_value is not None:
        db_gear.purchase_value = gear.purchase_value
    if gear.strava_gear_id is not None:
        db_gear.strava_gear_id = gear.strava_gear_id
    if gear.garminconnect_gear_id is not None:
        db_gear.garminconnect_gear_id = (
            gear.garminconnect_gear_id
        )

    db.commit()
    db.refresh(db_gear)

    return db_gear


@core_decorators.handle_db_errors
def delete_gear(
    gear_id: int, db: Session
) -> None:
    """
    Delete a gear by ID.

    Args:
        gear_id: Gear ID to delete.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If gear not found or
            a database error occurs.
    """
    stmt = delete(gears_models.Gear).where(
        gears_models.Gear.id == gear_id,
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Gear with id {gear_id} not found"
            ),
        )

    db.commit()


@core_decorators.handle_db_errors
def delete_all_strava_gear_for_user(
    user_id: int, db: Session
) -> None:
    """
    Delete all Strava-linked gears for a user.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = delete(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
        gears_models.Gear.strava_gear_id.isnot(
            None,
        ),
    )
    result = db.execute(stmt)

    if result.rowcount != 0:
        db.commit()


@core_decorators.handle_db_errors
def delete_all_garminconnect_gear_for_user(
    user_id: int, db: Session
) -> None:
    """
    Delete all Garmin Connect-linked gears for a
    user.

    Args:
        user_id: Owner user ID.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = delete(gears_models.Gear).where(
        gears_models.Gear.user_id == user_id,
        gears_models.Gear.garminconnect_gear_id
        .isnot(None),
    )
    result = db.execute(stmt)

    if result.rowcount != 0:
        db.commit()
