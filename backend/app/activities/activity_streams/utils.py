"""Utility functions for activity stream data."""

import datetime

import numpy as np
from sqlalchemy.orm import Session

import activities.activity.models as activity_models
import activities.activity_streams.constants as activity_streams_constants
import activities.activity_streams.models as activity_streams_models
import activities.activity_streams.schema as activity_streams_schema
import users.users.crud as users_crud

# Map stream type to activity hide attribute
_STREAM_HIDE_MAP: dict[int, str] = {
    activity_streams_constants.STREAM_TYPE_HR: "hide_hr",
    activity_streams_constants.STREAM_TYPE_POWER: "hide_power",
    activity_streams_constants.STREAM_TYPE_CADENCE: "hide_cadence",
    activity_streams_constants.STREAM_TYPE_ELEVATION: "hide_elevation",
    activity_streams_constants.STREAM_TYPE_SPEED: "hide_speed",
    activity_streams_constants.STREAM_TYPE_PACE: "hide_pace",
    activity_streams_constants.STREAM_TYPE_MAP: "hide_map",
}


def is_stream_hidden(
    activity: activity_models.Activity,
    stream_type: int,
) -> bool:
    """
    Check if a stream type is hidden.

    Args:
        activity: The activity ORM instance.
        stream_type: The stream type constant.

    Returns:
        True if the stream should be hidden.
    """
    attr = _STREAM_HIDE_MAP.get(stream_type)
    return bool(attr and getattr(activity, attr, False))


def filter_visible_streams(
    streams: list[activity_streams_models.ActivityStreams],
    activity: activity_models.Activity,
) -> list[activity_streams_models.ActivityStreams]:
    """
    Filter out streams hidden by the activity.

    Args:
        streams: List of stream ORM instances.
        activity: The activity ORM instance.

    Returns:
        Streams that are not hidden.
    """
    return [s for s in streams if not is_stream_hidden(activity, s.stream_type)]


def transform_activity_streams(
    activity_stream: (activity_streams_models.ActivityStreams),
    activity: activity_models.Activity,
    db: Session,
) -> activity_streams_schema.ActivityStreams:
    """
    Transform a stream to a Pydantic schema.

    Args:
        activity_stream: The stream ORM instance.
        activity: The activity ORM instance.
        db: Database session.

    Returns:
        The activity stream as a schema.
    """
    if activity_stream.stream_type == activity_streams_constants.STREAM_TYPE_HR:
        return transform_activity_streams_hr(activity_stream, activity, db)

    return activity_streams_schema.ActivityStreams.model_validate(activity_stream)


def transform_activity_streams_hr(
    activity_stream: (activity_streams_models.ActivityStreams),
    activity: activity_models.Activity,
    db: Session,
) -> activity_streams_schema.ActivityStreams:
    """
    Calculate HR zone percentages for a stream.

    Args:
        activity_stream: The HR stream instance.
        activity: The activity ORM instance.
        db: Database session.

    Returns:
        Schema with hr_zone_percentages set.
    """
    schema = activity_streams_schema.ActivityStreams.model_validate(activity_stream)

    waypoints = activity_stream.stream_waypoints
    if not waypoints or not isinstance(waypoints, list):
        return schema

    detail_user = users_crud.get_user_by_id(activity.user_id, db)
    if not detail_user:
        return schema

    if detail_user.max_heart_rate:
        max_heart_rate = detail_user.max_heart_rate
    elif detail_user.birthdate:
        year = detail_user.birthdate.year
        current_year = datetime.datetime.now(datetime.UTC).year
        max_heart_rate = 220 - (current_year - year)
    else:
        return schema

    zone_1 = max_heart_rate * 0.6
    zone_2 = max_heart_rate * 0.7
    zone_3 = max_heart_rate * 0.8
    zone_4 = max_heart_rate * 0.9

    hr_values = np.array([float(wp.get("hr")) for wp in waypoints if wp.get("hr") is not None])

    total = len(hr_values)
    if total == 0:
        return schema

    zone_counts = [
        np.sum(hr_values < zone_1),
        np.sum((hr_values >= zone_1) & (hr_values < zone_2)),
        np.sum((hr_values >= zone_2) & (hr_values < zone_3)),
        np.sum((hr_values >= zone_3) & (hr_values < zone_4)),
        np.sum(hr_values >= zone_4),
    ]
    zone_percentages = [round((count / total) * 100, 2) for count in zone_counts]

    has_timer_time = hasattr(activity, "total_timer_time") and activity.total_timer_time
    if has_timer_time:
        zone_time_seconds = [int((percent / 100) * float(activity.total_timer_time)) for percent in zone_percentages]
    else:
        zone_time_seconds = [0, 0, 0, 0, 0]

    zone_hr = {
        "zone_1": f"< {int(zone_1)}",
        "zone_2": (f"{int(zone_1)} - {int(zone_2) - 1}"),
        "zone_3": (f"{int(zone_2)} - {int(zone_3) - 1}"),
        "zone_4": (f"{int(zone_3)} - {int(zone_4) - 1}"),
        "zone_5": f">= {int(zone_4)}",
    }
    schema.hr_zone_percentages = {
        "zone_1": {
            "percent": zone_percentages[0],
            "hr": zone_hr["zone_1"],
            "time_seconds": (zone_time_seconds[0]),
        },
        "zone_2": {
            "percent": zone_percentages[1],
            "hr": zone_hr["zone_2"],
            "time_seconds": (zone_time_seconds[1]),
        },
        "zone_3": {
            "percent": zone_percentages[2],
            "hr": zone_hr["zone_3"],
            "time_seconds": (zone_time_seconds[2]),
        },
        "zone_4": {
            "percent": zone_percentages[3],
            "hr": zone_hr["zone_4"],
            "time_seconds": (zone_time_seconds[3]),
        },
        "zone_5": {
            "percent": zone_percentages[4],
            "hr": zone_hr["zone_5"],
            "time_seconds": (zone_time_seconds[4]),
        },
    }

    return schema
