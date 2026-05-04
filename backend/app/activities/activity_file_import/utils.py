"""Shared utilities for activity file import normalization."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

import activities.activity.schema as activities_schema
import users.users_privacy_settings.models as users_privacy_settings_models
import users.users_privacy_settings.utils as users_privacy_settings_utils

# ISO 8601 datetime format used throughout the import pipeline
_DT_FMT = "%Y-%m-%dT%H:%M:%S"

# Canonical keys present in every activity file payload's waypoint streams.
# Used as documentation and for IDE hint support.
STREAM_KEYS: tuple[str, ...] = (
    "is_elevation_set",
    "ele_waypoints",
    "is_power_set",
    "power_waypoints",
    "is_heart_rate_set",
    "hr_waypoints",
    "is_velocity_set",
    "vel_waypoints",
    "pace_waypoints",
    "is_cadence_set",
    "cad_waypoints",
    "is_lat_lon_set",
    "lat_lon_waypoints",
)


def build_activity_privacy_kwargs(
    user_privacy_settings: users_privacy_settings_models.UsersPrivacySettings,
) -> dict[str, bool | int]:
    """Build privacy field kwargs for Activity schema from ORM model.

    Args:
        user_privacy_settings: The ORM privacy-settings record for the
            activity owner.

    Returns:
        A dict with all 16 privacy fields ready to unpack into an
        Activity constructor call.
    """
    ups = user_privacy_settings
    return {
        "visibility": users_privacy_settings_utils.visibility_to_int(
            ups.default_activity_visibility
        ),
        "hide_start_time": ups.hide_activity_start_time or False,
        "hide_location": ups.hide_activity_location or False,
        "hide_map": ups.hide_activity_map or False,
        "hide_hr": ups.hide_activity_hr or False,
        "hide_power": ups.hide_activity_power or False,
        "hide_cadence": ups.hide_activity_cadence or False,
        "hide_elevation": ups.hide_activity_elevation or False,
        "hide_speed": ups.hide_activity_speed or False,
        "hide_pace": ups.hide_activity_pace or False,
        "hide_laps": ups.hide_activity_laps or False,
        "hide_workout_sets_steps": (ups.hide_activity_workout_sets_steps or False),
        "hide_gear": ups.hide_activity_gear or False,
    }


def build_activity_file_payload(
    activity: activities_schema.Activity,
    waypoints: dict[str, list[dict]],
    laps: list[dict],
    extras: dict | None = None,
) -> dict:
    """Build normalized activity file import payload.

    Args:
        activity: Populated Activity schema instance.
        waypoints: Dict keyed by stream name (e.g. ``'lat_lon_waypoints'``,
            ``'ele_waypoints'``, …) mapping to lists of waypoint dicts.
        laps: List of lap dicts for the activity.
        extras: Optional format-specific extras (e.g. FIT sets /
            workout_steps).

    Returns:
        A dict containing the activity, all stream flags/lists, laps, and
        any extras — matching the structure expected by
        ``activities/activity/utils.py`` callers.
    """
    payload: dict = {
        "activity": activity,
        "is_elevation_set": bool(waypoints.get("ele_waypoints")),
        "ele_waypoints": waypoints.get("ele_waypoints", []),
        "is_power_set": bool(waypoints.get("power_waypoints")),
        "power_waypoints": waypoints.get("power_waypoints", []),
        "is_heart_rate_set": bool(waypoints.get("hr_waypoints")),
        "hr_waypoints": waypoints.get("hr_waypoints", []),
        "is_velocity_set": bool(waypoints.get("vel_waypoints")),
        "vel_waypoints": waypoints.get("vel_waypoints", []),
        "pace_waypoints": waypoints.get("pace_waypoints", []),
        "is_cadence_set": bool(waypoints.get("cad_waypoints")),
        "cad_waypoints": waypoints.get("cad_waypoints", []),
        "is_lat_lon_set": bool(waypoints.get("lat_lon_waypoints")),
        "lat_lon_waypoints": waypoints.get("lat_lon_waypoints", []),
        "laps": laps,
    }
    if extras:
        payload.update(extras)
    return payload


# ---------------------------------------------------------------------------
# Phase 6 placeholder: lap generation helpers
# ---------------------------------------------------------------------------


class LapMetrics(TypedDict):
    """Aggregated metrics for a single activity lap."""

    start_time: str
    end_time: str
    distance: float | None
    avg_hr: float | None
    max_hr: float | None
    avg_cadence: float | None
    avg_power: float | None
    max_power: float | None
    normalized_power: float | None
    avg_speed: float | None
    max_speed: float | None
    avg_pace: float | None


def filter_waypoints_by_time_range(
    waypoints: list[dict],
    start_time: datetime,
    end_time: datetime,
) -> list[dict]:
    """Return waypoints whose time falls within [start_time, end_time].

    Args:
        waypoints: List of waypoint dicts each containing a ``'time'``
            key with an ISO 8601 string or datetime value.
        start_time: Inclusive lower bound.
        end_time: Inclusive upper bound.

    Returns:
        Filtered list of waypoint dicts.
    """
    raise NotImplementedError("Implemented in Phase 6")


def generate_activity_laps(
    lap_data: list[dict],
    waypoints: dict[str, list[dict]],
) -> list[dict]:
    """Generate lap metric dicts from lap boundaries and waypoint streams.

    Args:
        lap_data: List of raw lap dicts with at least ``'start_time'``
            and ``'end_time'`` keys.
        waypoints: Dict of stream lists (same keys as ``STREAM_KEYS``).

    Returns:
        List of ``LapMetrics``-shaped dicts with aggregated metrics.
    """
    raise NotImplementedError("Implemented in Phase 6")


# ---------------------------------------------------------------------------
# Phase 7 placeholder: FIT session stream filtering
# ---------------------------------------------------------------------------


def filter_streams_by_time_range(
    streams: dict[str, list[dict]],
    start_time: datetime,
    end_time: datetime,
) -> dict[str, list[dict]]:
    """Filter all waypoint streams to a time range.

    Args:
        streams: Dict keyed by stream name mapping to lists of waypoint
            dicts, each containing a ``'time'`` key.
        start_time: Inclusive lower bound.
        end_time: Inclusive upper bound.

    Returns:
        New dict with the same keys, each stream filtered to the given
        time range.
    """
    raise NotImplementedError("Implemented in Phase 7")


# ---------------------------------------------------------------------------
# Phase 8 placeholders: location / timezone resolution
# ---------------------------------------------------------------------------


def resolve_location(
    latitude: float,
    longitude: float,
) -> dict[str, str] | None:
    """Get city, town, and country via geocoding.

    Args:
        latitude: WGS-84 latitude in decimal degrees.
        longitude: WGS-84 longitude in decimal degrees.

    Returns:
        Dict with keys ``'city'``, ``'town'``, ``'country'``, or
        ``None`` on geocoding error.
    """
    raise NotImplementedError("Implemented in Phase 8")


def resolve_timezone_from_lat_lon(
    latitude: float,
    longitude: float,
    fallback_tz: str,
) -> str:
    """Get timezone string via TimezoneFinder with a fallback.

    Args:
        latitude: WGS-84 latitude in decimal degrees.
        longitude: WGS-84 longitude in decimal degrees.
        fallback_tz: Timezone string to return when TimezoneFinder
            returns ``None``.

    Returns:
        IANA timezone string (e.g. ``'Europe/Lisbon'``).
    """
    raise NotImplementedError("Implemented in Phase 8")


# ---------------------------------------------------------------------------
# Phase 9 placeholder: power summary helper
# ---------------------------------------------------------------------------


def calculate_power_metrics(
    power_waypoints: list[dict],
) -> tuple[float | None, float | None, float | None]:
    """Calculate average, max, and normalised power from a power stream.

    Args:
        power_waypoints: List of waypoint dicts each containing a
            ``'power'`` key with a numeric value.

    Returns:
        Tuple of ``(avg_power, max_power, normalized_power)``.  Any
        value may be ``None`` if the stream is empty or contains no
        valid readings.
    """
    raise NotImplementedError("Implemented in Phase 9")
