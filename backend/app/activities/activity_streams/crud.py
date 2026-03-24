"""CRUD operations for activity stream data."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import activities.activity_streams.schema \
    as activity_streams_schema
import activities.activity_streams.models \
    as activity_streams_models
import activities.activity_streams.utils \
    as activity_streams_utils

import activities.activity.crud as activity_crud
import activities.activity.models \
    as activity_models

import server_settings.utils \
    as server_settings_utils

import core.logger as core_logger


def get_activity_streams(
    activity_id: int,
    token_user_id: int,
    db: Session,
) -> list[
    activity_streams_schema.ActivityStreams
] | None:
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
        activity = (
            activity_crud.get_activity_by_id(
                activity_id, db
            )
        )

        if not activity:
            return None

        stmt = select(
            activity_streams_models.ActivityStreams
        ).where(
            activity_streams_models.ActivityStreams
            .activity_id == activity_id,
        )
        activity_streams = (
            db.scalars(stmt).all()
        )

        if not activity_streams:
            return None

        if token_user_id != activity.user_id:
            activity_streams = (
                activity_streams_utils
                .filter_visible_streams(
                    activity_streams, activity
                )
            )

        return [
            activity_streams_utils
            .transform_activity_streams(
                stream, activity, db
            )
            for stream in activity_streams
        ]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            "Error in get_activity_streams:"
            f" {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def get_activities_streams(
    activity_ids: list[int],
    token_user_id: int,
    db: Session,
    activities: list[
        activity_models.Activity
    ] | None = None,
) -> list[
    activity_streams_schema.ActivityStreams
]:
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
            stmt = select(
                activity_models.Activity
            ).where(
                activity_models.Activity.id.in_(
                    activity_ids
                )
            )
            activities = (
                db.scalars(stmt).all()
            )

        if not activities:
            return []

        activity_map = {
            a.id: a for a in activities
        }

        allowed_ids = [
            a.id
            for a in activities
            if a.user_id == token_user_id
        ]

        if not allowed_ids:
            return []

        stmt = select(
            activity_streams_models.ActivityStreams
        ).where(
            activity_streams_models.ActivityStreams
            .activity_id.in_(allowed_ids)
        )
        all_streams = db.scalars(stmt).all()

        if not all_streams:
            return []

        return [
            activity_streams_utils
            .transform_activity_streams(
                stream,
                activity_map[
                    stream.activity_id
                ],
                db,
            )
            for stream in all_streams
        ]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            "Error in get_activities_streams:"
            f" {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def get_public_activity_streams(
    activity_id: int,
    db: Session,
) -> list[
    activity_streams_schema.ActivityStreams
] | None:
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
        server_settings = (
            server_settings_utils
            .get_server_settings_or_404(db)
        )

        if not server_settings.public_shareable_links:
            return None

        activity = (
            activity_crud
            .get_activity_by_id_if_is_public(
                activity_id, db
            )
        )

        if not activity:
            return None

        stmt = (
            select(
                activity_streams_models
                .ActivityStreams
            )
            .join(
                activity_models.Activity,
                activity_models.Activity.id
                == (
                    activity_streams_models
                    .ActivityStreams.activity_id
                ),
            )
            .where(
                activity_streams_models
                .ActivityStreams.activity_id
                == activity_id,
                activity_models
                .Activity.visibility == 0,
                activity_models.Activity.id
                == activity_id,
            )
        )
        activity_streams = (
            db.scalars(stmt).all()
        )

        if not activity_streams:
            return None

        activity_streams = (
            activity_streams_utils
            .filter_visible_streams(
                activity_streams, activity
            )
        )

        return [
            activity_streams_utils
            .transform_activity_streams(
                stream, activity, db
            )
            for stream in activity_streams
        ]
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            "Error in"
            " get_public_activity_streams:"
            f" {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def get_activity_stream_by_type(
    activity_id: int,
    stream_type: int,
    token_user_id: int,
    db: Session,
) -> (
    activity_streams_schema.ActivityStreams
    | None
):
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
        activity = (
            activity_crud.get_activity_by_id(
                activity_id, db
            )
        )

        if not activity:
            return None

        stmt = select(
            activity_streams_models.ActivityStreams
        ).where(
            activity_streams_models.ActivityStreams
            .activity_id == activity_id,
            activity_streams_models.ActivityStreams
            .stream_type == stream_type,
        )
        activity_stream = (
            db.scalars(stmt).first()
        )

        if not activity_stream:
            return None

        if token_user_id != activity.user_id:
            if activity_streams_utils\
                    .is_stream_hidden(
                activity,
                activity_stream.stream_type,
            ):
                return None

        return (
            activity_streams_utils
            .transform_activity_streams(
                activity_stream, activity, db
            )
        )
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            "Error in"
            " get_activity_stream_by_type:"
            f" {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def get_public_activity_stream_by_type(
    activity_id: int,
    stream_type: int,
    db: Session,
) -> (
    activity_streams_schema.ActivityStreams
    | None
):
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
        server_settings = (
            server_settings_utils
            .get_server_settings_or_404(db)
        )

        if not server_settings.public_shareable_links:
            return None

        activity = (
            activity_crud
            .get_activity_by_id_if_is_public(
                activity_id, db
            )
        )

        if not activity:
            return None

        stmt = (
            select(
                activity_streams_models
                .ActivityStreams
            )
            .join(
                activity_models.Activity,
                activity_models.Activity.id
                == (
                    activity_streams_models
                    .ActivityStreams.activity_id
                ),
            )
            .where(
                activity_streams_models
                .ActivityStreams.activity_id
                == activity_id,
                activity_streams_models
                .ActivityStreams.stream_type
                == stream_type,
                activity_models
                .Activity.visibility == 0,
                activity_models.Activity.id
                == activity_id,
            )
        )
        activity_stream = (
            db.scalars(stmt).first()
        )

        if not activity_stream:
            return None

        if activity_streams_utils\
                .is_stream_hidden(
            activity,
            activity_stream.stream_type,
        ):
            return None

        return (
            activity_streams_utils
            .transform_activity_streams(
                activity_stream, activity, db
            )
        )
    except SQLAlchemyError as err:
        core_logger.print_to_log(
            "Error in"
            " get_public_activity_stream"
            f"_by_type: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err


def create_activity_streams(
    activity_streams: list[
        activity_streams_schema.ActivityStreams
    ],
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
        streams = [
            activity_streams_models.ActivityStreams(
                activity_id=(
                    stream.activity_id
                ),
                stream_type=stream.stream_type,
                stream_waypoints=(
                    stream.stream_waypoints
                ),
                strava_activity_stream_id=(
                    stream
                    .strava_activity_stream_id
                ),
            )
            for stream in activity_streams
        ]

        db.add_all(streams)
        db.commit()
    except SQLAlchemyError as err:
        db.rollback()
        core_logger.print_to_log_and_console(
            "Error in"
            " create_activity_streams:"
            f" {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Internal Server Error",
        ) from err
