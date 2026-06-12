"""Utility functions for activity stream data."""

import datetime

import numpy as np

import activities.activity.models as activity_models
import activities.activity_streams.constants as activity_streams_constants
import activities.activity_streams.models as activity_streams_models
import activities.activity_streams.schema as activity_streams_schema

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
    activity_stream: activity_streams_models.ActivityStreams,
) -> activity_streams_schema.ActivityStreams:
    """
    Transform a stream to a Pydantic schema.

    Args:
        activity_stream: The stream ORM instance.

    Returns:
        The activity stream as a schema.
    """
    return activity_streams_schema.ActivityStreams.model_validate(activity_stream)


def resolve_max_heart_rate(user) -> int | None:
    """
    Resolve a user's max heart rate.

    Args:
        user: The user ORM instance (must expose max_heart_rate and birthdate).

    Returns:
        The stored max HR, the age-derived value (220 - age), or None.
    """
    if user.max_heart_rate:
        return user.max_heart_rate
    if user.birthdate:
        current_year = datetime.datetime.now(datetime.UTC).year
        return 220 - (current_year - user.birthdate.year)
    return None


def compute_hr_zone_breakdown(
    waypoints: list[dict],
    max_heart_rate: int,
    total_timer_time,
) -> dict | None:
    """
    Compute the HR zone breakdown for a set of waypoints.

    Args:
        waypoints: List of waypoint dicts (each may contain an "hr" key).
        max_heart_rate: The user's max heart rate.
        total_timer_time: Activity total timer time in seconds (may be falsy).

    Returns:
        A dict of zone_1..zone_5 entries, or None if it cannot be computed.
    """
    if not waypoints or not isinstance(waypoints, list):
        return None

    zone_1 = max_heart_rate * 0.6
    zone_2 = max_heart_rate * 0.7
    zone_3 = max_heart_rate * 0.8
    zone_4 = max_heart_rate * 0.9

    hr_values = np.array([float(wp.get("hr")) for wp in waypoints if wp.get("hr") is not None])
    total = len(hr_values)
    if total == 0:
        return None

    zone_counts = [
        np.sum(hr_values < zone_1),
        np.sum((hr_values >= zone_1) & (hr_values < zone_2)),
        np.sum((hr_values >= zone_2) & (hr_values < zone_3)),
        np.sum((hr_values >= zone_3) & (hr_values < zone_4)),
        np.sum(hr_values >= zone_4),
    ]
    zone_percentages = [round((count / total) * 100, 2) for count in zone_counts]

    if total_timer_time:
        zone_time_seconds = [int((percent / 100) * float(total_timer_time)) for percent in zone_percentages]
    else:
        zone_time_seconds = [0, 0, 0, 0, 0]

    zone_hr = {
        "zone_1": f"< {int(zone_1)}",
        "zone_2": f"{int(zone_1)} - {int(zone_2) - 1}",
        "zone_3": f"{int(zone_2)} - {int(zone_3) - 1}",
        "zone_4": f"{int(zone_3)} - {int(zone_4) - 1}",
        "zone_5": f">= {int(zone_4)}",
    }

    return {
        "zone_1": {"percent": zone_percentages[0], "hr": zone_hr["zone_1"], "time_seconds": zone_time_seconds[0]},
        "zone_2": {"percent": zone_percentages[1], "hr": zone_hr["zone_2"], "time_seconds": zone_time_seconds[1]},
        "zone_3": {"percent": zone_percentages[2], "hr": zone_hr["zone_3"], "time_seconds": zone_time_seconds[2]},
        "zone_4": {"percent": zone_percentages[3], "hr": zone_hr["zone_4"], "time_seconds": zone_time_seconds[3]},
        "zone_5": {"percent": zone_percentages[4], "hr": zone_hr["zone_5"], "time_seconds": zone_time_seconds[4]},
    }


def build_zone_percentages(user, activity, waypoints: list[dict]) -> dict | None:
    """
    Build the metric-keyed zone_percentages payload for a stream.

    Args:
        user: The user ORM instance.
        activity: The activity ORM instance.
        waypoints: The HR stream waypoints.

    Returns:
        {"hr": {...}} when HR zones can be computed, otherwise None.
    """
    max_heart_rate = resolve_max_heart_rate(user)
    if not max_heart_rate:
        return None
    total_timer_time = getattr(activity, "total_timer_time", None)
    hr_block = compute_hr_zone_breakdown(waypoints, max_heart_rate, total_timer_time)
    if hr_block is None:
        return None
    return {"hr": hr_block}
