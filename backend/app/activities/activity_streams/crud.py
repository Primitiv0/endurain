"""CRUD operations for activity stream data."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import activities.activity.crud as activity_crud
import activities.activity.models as activity_models
import activities.activity_streams.constants as activity_streams_constants
import activities.activity_streams.models as activity_streams_models
import activities.activity_streams.schema as activity_streams_schema
import activities.activity_streams.utils as activity_streams_utils
import core.logger as core_logger
import server_settings.utils as server_settings_utils
import users.users.crud as users_crud


def get_activity_streams(
    activity_id: int,
    token_user_id: int,
    db: Session,
) -> list[activity_streams_schema.ActivityStreams] | None:
    """
    Get all streams for an activity.

    Args:
        activity_id: The activity identifier.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        List of activity streams or None.

    Raises:
        HTTPException: On database errors.
    """
    try:
        activity = activity_crud.get_activity_by_id(activity_id, db)

        if not activity:
            return None

        stmt = select(activity_streams_models.ActivityStreams).where(
            activity_streams_models.ActivityStreams.activity_id == activity_id,
        )
        activity_streams = db.scalars(stmt).all()

        if not activity_streams:
            return None

        if token_user_id != activity.user_id:
            activity_streams = activity_streams_utils.filter_visible_streams(activity_streams, activity)

        return [activity_streams_utils.transform_activity_streams(stream) for stream in activity_streams]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            f"Error in get_activity_streams: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


def get_activities_streams(
    activity_ids: list[int],
    token_user_id: int,
    db: Session,
    activities: list[activity_models.Activity] | None = None,
) -> list[activity_streams_schema.ActivityStreams]:
    """
    Get streams for multiple activities.

    Args:
        activity_ids: List of activity IDs.
        token_user_id: Authenticated user ID.
        db: Database session.
        activities: Pre-fetched activity list.

    Returns:
        List of activity streams.

    Raises:
        HTTPException: On database errors.
    """
    try:
        if not activity_ids:
            return []

        if not activities:
            stmt = select(activity_models.Activity).where(activity_models.Activity.id.in_(activity_ids))
            activities = db.scalars(stmt).all()

        if not activities:
            return []

        allowed_ids = [a.id for a in activities if a.user_id == token_user_id]

        if not allowed_ids:
            return []

        stmt = select(activity_streams_models.ActivityStreams).where(
            activity_streams_models.ActivityStreams.activity_id.in_(allowed_ids)
        )
        all_streams = db.scalars(stmt).all()

        if not all_streams:
            return []

        return [activity_streams_utils.transform_activity_streams(stream) for stream in all_streams]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            f"Error in get_activities_streams: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


def get_public_activity_streams(
    activity_id: int,
    db: Session,
) -> list[activity_streams_schema.ActivityStreams] | None:
    """
    Get public streams for an activity.

    Args:
        activity_id: The activity identifier.
        db: Database session.

    Returns:
        List of activity streams or None.

    Raises:
        HTTPException: On database errors.
    """
    try:
        server_settings = server_settings_utils.get_server_settings_or_404(db)

        if not server_settings.public_shareable_links:
            return None

        activity = activity_crud.get_activity_by_id_if_is_public(activity_id, db)

        if not activity:
            return None

        stmt = (
            select(activity_streams_models.ActivityStreams)
            .join(
                activity_models.Activity,
                activity_models.Activity.id == (activity_streams_models.ActivityStreams.activity_id),
            )
            .where(
                activity_streams_models.ActivityStreams.activity_id == activity_id,
                activity_models.Activity.visibility == 0,
                activity_models.Activity.id == activity_id,
            )
        )
        activity_streams = db.scalars(stmt).all()

        if not activity_streams:
            return None

        activity_streams = activity_streams_utils.filter_visible_streams(activity_streams, activity)

        return [activity_streams_utils.transform_activity_streams(stream) for stream in activity_streams]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            f"Error in get_public_activity_streams: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


def get_activity_stream_by_type(
    activity_id: int,
    stream_type: int,
    token_user_id: int,
    db: Session,
) -> activity_streams_schema.ActivityStreams | None:
    """
    Get a specific stream type for an activity.

    Args:
        activity_id: The activity identifier.
        stream_type: The stream type constant.
        token_user_id: Authenticated user ID.
        db: Database session.

    Returns:
        The activity stream or None.

    Raises:
        HTTPException: On database errors.
    """
    try:
        activity = activity_crud.get_activity_by_id(activity_id, db)

        if not activity:
            return None

        stmt = select(activity_streams_models.ActivityStreams).where(
            activity_streams_models.ActivityStreams.activity_id == activity_id,
            activity_streams_models.ActivityStreams.stream_type == stream_type,
        )
        activity_stream = db.scalars(stmt).first()

        if not activity_stream:
            return None

        if token_user_id != activity.user_id and activity_streams_utils.is_stream_hidden(
            activity,
            activity_stream.stream_type,
        ):
            return None

        return activity_streams_utils.transform_activity_streams(activity_stream)
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            f"Error in get_activity_stream_by_type: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


def get_public_activity_stream_by_type(
    activity_id: int,
    stream_type: int,
    db: Session,
) -> activity_streams_schema.ActivityStreams | None:
    """
    Get a public stream by type for an activity.

    Args:
        activity_id: The activity identifier.
        stream_type: The stream type constant.
        db: Database session.

    Returns:
        The activity stream or None.

    Raises:
        HTTPException: On database errors.
    """
    try:
        server_settings = server_settings_utils.get_server_settings_or_404(db)

        if not server_settings.public_shareable_links:
            return None

        activity = activity_crud.get_activity_by_id_if_is_public(activity_id, db)

        if not activity:
            return None

        stmt = (
            select(activity_streams_models.ActivityStreams)
            .join(
                activity_models.Activity,
                activity_models.Activity.id == (activity_streams_models.ActivityStreams.activity_id),
            )
            .where(
                activity_streams_models.ActivityStreams.activity_id == activity_id,
                activity_streams_models.ActivityStreams.stream_type == stream_type,
                activity_models.Activity.visibility == 0,
                activity_models.Activity.id == activity_id,
            )
        )
        activity_stream = db.scalars(stmt).first()

        if not activity_stream:
            return None

        if activity_streams_utils.is_stream_hidden(
            activity,
            activity_stream.stream_type,
        ):
            return None

        return activity_streams_utils.transform_activity_streams(activity_stream)
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            f"Error in get_public_activity_stream_by_type: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


def get_hr_streams_without_zone_percentages(
    db: Session,
    batch_size: int = 500,
    after_id: int = 0,
) -> list[activity_streams_models.ActivityStreams]:
    """Return HR streams lacking pre-computed zone_percentages in batches."""
    stmt = (
        select(activity_streams_models.ActivityStreams)
        .where(
            activity_streams_models.ActivityStreams.stream_type == activity_streams_constants.STREAM_TYPE_HR,
            activity_streams_models.ActivityStreams.zone_percentages.is_(None),
            activity_streams_models.ActivityStreams.id > after_id,
        )
        .order_by(activity_streams_models.ActivityStreams.id)
        .limit(batch_size)
    )
    return db.scalars(stmt).all()


def backfill_zone_percentages_for_missing_hr_streams(
    db: Session,
    batch_size: int = 500,
) -> bool:
    """Backfill zone_percentages for existing HR streams in batches."""
    streams_processed_with_no_errors = True
    last_id = 0

    while True:
        batch_streams = get_hr_streams_without_zone_percentages(db, batch_size=batch_size, after_id=last_id)
        if not batch_streams:
            break

        activity_cache: dict[int, activity_models.Activity] = {}
        user_cache: dict[int, object] = {}

        for stream in batch_streams:
            try:
                activity = activity_cache.get(stream.activity_id)
                if activity is None:
                    activity = activity_crud.get_activity_by_id(stream.activity_id, db)
                    if activity is None:
                        continue
                    activity_cache[stream.activity_id] = activity

                user = user_cache.get(activity.user_id)
                if user is None:
                    user = users_crud.get_user_by_id(activity.user_id, db)
                    if user is None:
                        continue
                    user_cache[activity.user_id] = user

                payload = activity_streams_utils.build_zone_percentages(
                    user,
                    activity,
                    stream.stream_waypoints,
                )

                if payload is not None:
                    stream.zone_percentages = payload
                    db.add(stream)
            except Exception as err:
                streams_processed_with_no_errors = False
                core_logger.print_to_log_and_console(
                    f"Backfill - Error processing stream {getattr(stream, 'id', 'unknown')}: {err}",
                    "error",
                    exc=err,
                )

        db.commit()
        last_id = batch_streams[-1].id

    return streams_processed_with_no_errors


def create_activity_streams(
    activity_streams: list[activity_streams_schema.ActivityStreams],
    db: Session,
) -> None:
    """
    Bulk create activity streams.

    Args:
        activity_streams: List of stream schemas.
        db: Database session.

    Raises:
        HTTPException: On database errors.
    """
    try:
        activity_by_id = {}
        user_by_activity_id = {}

        hr_activity_ids = {
            stream.activity_id
            for stream in activity_streams
            if stream.stream_type == activity_streams_constants.STREAM_TYPE_HR
        }

        for activity_id in hr_activity_ids:
            activity = activity_crud.get_activity_by_id(activity_id, db)
            if not activity:
                continue

            user = users_crud.get_user_by_id(activity.user_id, db)
            if not user:
                continue

            activity_by_id[activity_id] = activity
            user_by_activity_id[activity_id] = user

        streams = []
        for stream in activity_streams:
            zone_percentages = None
            if stream.stream_type == activity_streams_constants.STREAM_TYPE_HR:
                activity = activity_by_id.get(stream.activity_id)
                user = user_by_activity_id.get(stream.activity_id)
                if activity and user:
                    zone_percentages = activity_streams_utils.build_zone_percentages(
                        user,
                        activity,
                        stream.stream_waypoints,
                    )

            streams.append(
                activity_streams_models.ActivityStreams(
                    activity_id=(stream.activity_id),
                    stream_type=stream.stream_type,
                    stream_waypoints=(stream.stream_waypoints),
                    strava_activity_stream_id=(stream.strava_activity_stream_id),
                    zone_percentages=zone_percentages,
                )
            )

        db.add_all(streams)
        db.commit()
    except SQLAlchemyError as err:
        db.rollback()
        core_logger.print_to_log_and_console(
            f"Error in create_activity_streams: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err
