"""Utilities for parsing GPX files into activity data."""

from datetime import datetime
from pathlib import Path
from typing import TypedDict

import gpxpy
import gpxpy.gpx
from fastapi import HTTPException, status
from geopy.distance import geodesic
from sqlalchemy.orm import Session
from timezonefinder import TimezoneFinder

import activities.activity.utils as activities_utils
import activities.activity.schema as activities_schema
import core.config as core_config
import core.logger as core_logger
import users.users_default_gear.utils as user_default_gear_utils
import users.users_privacy_settings.models as users_privacy_settings_models
import users.users_privacy_settings.utils as users_privacy_settings_utils

# ISO 8601 datetime format used throughout this module
_DT_FMT = "%Y-%m-%dT%H:%M:%S"

# Garmin TrackPointExtension XML namespace paths
_HR_NS = (
    ".//{http://www.garmin.com/xmlschemas"
    "/TrackPointExtension/v1}hr"
)
_CAD_NS = (
    ".//{http://www.garmin.com/xmlschemas"
    "/TrackPointExtension/v1}cad"
)

# Activity type IDs that do not use GPS-based timezone
# detection (e.g. indoor/pool activities)
_ACTIVITY_TYPE_POOL_SWIM = 3
_ACTIVITY_TYPE_TREADMILL = 7


class LapMetrics(TypedDict):
    """
    Typed dictionary for a single lap's metrics.

    Attributes:
        start_time: ISO timestamp of lap start.
        start_position_lat: Latitude of lap start.
        start_position_long: Longitude of lap start.
        end_position_lat: Latitude of lap end.
        end_position_long: Longitude of lap end.
        total_elapsed_time: Elapsed seconds.
        total_timer_time: Timer seconds.
        total_distance: Distance in metres.
        avg_heart_rate: Average HR in bpm.
        max_heart_rate: Maximum HR in bpm.
        avg_cadence: Average cadence.
        max_cadence: Maximum cadence.
        avg_power: Average power in watts.
        max_power: Maximum power in watts.
        total_ascent: Total ascent in metres.
        total_descent: Total descent in metres.
        normalized_power: Normalized power.
        enhanced_avg_pace: Average pace (min/km).
        enhanced_avg_speed: Average speed (m/s).
        enhanced_max_pace: Maximum pace (min/km).
        enhanced_max_speed: Maximum speed (m/s).
    """

    start_time: str
    start_position_lat: float | None
    start_position_long: float | None
    end_position_lat: float | None
    end_position_long: float | None
    total_elapsed_time: float
    total_timer_time: float
    total_distance: float
    avg_heart_rate: int | None
    max_heart_rate: int | None
    avg_cadence: int | None
    max_cadence: int | None
    avg_power: int | None
    max_power: int | None
    total_ascent: int | None
    total_descent: int | None
    normalized_power: int | None
    enhanced_avg_pace: float | None
    enhanced_avg_speed: float | None
    enhanced_max_pace: float | None
    enhanced_max_speed: float | None


class ParsedGpxData(TypedDict):
    """
    Typed dictionary for parsed GPX file output.

    Attributes:
        activity: Populated Activity schema.
        is_elevation_set: Whether elevation data exists.
        ele_waypoints: List of elevation waypoints.
        is_power_set: Whether power data exists.
        power_waypoints: List of power waypoints.
        is_heart_rate_set: Whether HR data exists.
        hr_waypoints: List of heart rate waypoints.
        is_velocity_set: Whether velocity data exists.
        vel_waypoints: List of velocity waypoints.
        pace_waypoints: List of pace waypoints.
        is_cadence_set: Whether cadence data exists.
        cad_waypoints: List of cadence waypoints.
        is_lat_lon_set: Whether GPS data exists.
        lat_lon_waypoints: List of GPS waypoints.
        laps: List of computed lap metrics.
    """

    activity: activities_schema.Activity
    is_elevation_set: bool
    ele_waypoints: list[dict]
    is_power_set: bool
    power_waypoints: list[dict]
    is_heart_rate_set: bool
    hr_waypoints: list[dict]
    is_velocity_set: bool
    vel_waypoints: list[dict]
    pace_waypoints: list[dict]
    is_cadence_set: bool
    cad_waypoints: list[dict]
    is_lat_lon_set: bool
    lat_lon_waypoints: list[dict]
    laps: list[LapMetrics]


def _filter_waypoints(
    waypoints: list[dict],
    start_time: str,
    end_time: str,
) -> list[dict]:
    """
    Filter waypoints within a time range.

    Args:
        waypoints: List of waypoint dicts with a 'time' key in ISO format.
        start_time: ISO start time string.
        end_time: ISO end time string.

    Returns:
        Filtered list of waypoint dicts.
    """
    start_dt = datetime.strptime(start_time, _DT_FMT)
    end_dt = datetime.strptime(end_time, _DT_FMT)
    return [
        wp
        for wp in waypoints
        if start_dt
        <= datetime.strptime(wp["time"], _DT_FMT)
        <= end_dt
    ]


def _extract_extension_data(
    point: gpxpy.gpx.GPXTrackPoint,
) -> tuple[int, int, int]:
    """
    Extract HR, cadence, and power from extensions.

    Args:
        point: A gpxpy trackpoint with optional
            extension elements.

    Returns:
        Tuple of (heart_rate, cadence, power) as ints.
    """
    heart_rate: int = 0
    cadence: int = 0
    power: int = 0

    if not point.extensions:
        return heart_rate, cadence, power

    for extension in point.extensions:
        tag = extension.tag
        if tag.endswith("TrackPointExtension"):
            hr_el = extension.find(_HR_NS)
            if hr_el is not None and hr_el.text:
                heart_rate = int(hr_el.text)
            cad_el = extension.find(_CAD_NS)
            if cad_el is not None and cad_el.text:
                cadence = int(cad_el.text)
            # OpenTracks fallback
            if hr_el is None and cad_el is None:
                for child in extension:
                    if (
                        child.tag.endswith("hr")
                        and child.text
                    ):
                        heart_rate = int(child.text)
                    elif (
                        child.tag.endswith("cad")
                        and child.text
                    ):
                        cadence = int(child.text)
        elif tag.endswith("power"):
            power = (
                int(extension.text)
                if extension.text
                else 0
            )
        elif tag.endswith("heartrate"):
            # Tissot smartwatch and similar devices
            heart_rate = (
                int(extension.text)
                if extension.text
                else 0
            )

    return heart_rate, cadence, power


def _compute_lap_metrics(
    start_time: str,
    end_time: str,
    start_point: dict,
    end_point: dict,
    total_distance: float,
    ele_waypoints: list[dict],
    power_waypoints: list[dict],
    hr_waypoints: list[dict],
    cad_waypoints: list[dict],
    vel_waypoints: list[dict],
) -> LapMetrics:
    """
    Compute metrics for a single activity lap.

    Args:
        start_time: ISO timestamp of lap start.
        end_time: ISO timestamp of lap end.
        start_point: Lat/lon dict of lap start.
        end_point: Lat/lon dict of lap end.
        total_distance: Lap distance in km.
        ele_waypoints: Full elevation stream.
        power_waypoints: Full power stream.
        hr_waypoints: Full HR stream.
        cad_waypoints: Full cadence stream.
        vel_waypoints: Full velocity stream.

    Returns:
        Dict with all computed lap metrics.
    """
    lap_ele = _filter_waypoints(
        ele_waypoints, start_time, end_time,
    )
    lap_power = _filter_waypoints(
        power_waypoints, start_time, end_time,
    )
    lap_hr = _filter_waypoints(
        hr_waypoints, start_time, end_time,
    )
    lap_cad = _filter_waypoints(
        cad_waypoints, start_time, end_time,
    )
    lap_vel = _filter_waypoints(
        vel_waypoints, start_time, end_time,
    )

    ele_gain, ele_loss = None, None
    if lap_ele:
        ele_gain, ele_loss = (
            activities_utils
            .compute_elevation_gain_and_loss(
                elevations=lap_ele,
            )
        )

    avg_hr, max_hr = None, None
    if lap_hr:
        avg_hr, max_hr = (
            activities_utils.calculate_avg_and_max(
                lap_hr, "hr",
            )
        )

    avg_cad, max_cad = None, None
    if lap_cad:
        avg_cad, max_cad = (
            activities_utils.calculate_avg_and_max(
                lap_cad, "cad",
            )
        )

    avg_speed, max_speed = None, None
    if lap_vel:
        avg_speed, max_speed = (
            activities_utils.calculate_avg_and_max(
                lap_vel, "vel",
            )
        )

    avg_power, max_power, norm_power = None, None, None
    if lap_power:
        avg_power, max_power = (
            activities_utils.calculate_avg_and_max(
                lap_power, "power",
            )
        )
        norm_power = activities_utils.calculate_np(
            lap_power,
        )

    elapsed = (
        datetime.strptime(end_time, _DT_FMT)
        - datetime.strptime(start_time, _DT_FMT)
    ).total_seconds()

    return {
        "start_time": start_time,
        "start_position_lat": start_point["lat"],
        "start_position_long": start_point["lon"],
        "end_position_lat": end_point["lat"],
        "end_position_long": end_point["lon"],
        "total_elapsed_time": elapsed,
        "total_timer_time": elapsed,
        "total_distance": total_distance * 1000,
        "avg_heart_rate": (
            round(avg_hr) if avg_hr else None
        ),
        "max_heart_rate": (
            round(max_hr) if max_hr else None
        ),
        "avg_cadence": (
            round(avg_cad) if avg_cad else None
        ),
        "max_cadence": (
            round(max_cad) if max_cad else None
        ),
        "avg_power": (
            round(avg_power) if avg_power else None
        ),
        "max_power": (
            round(max_power) if max_power else None
        ),
        "total_ascent": (
            round(ele_gain) if ele_gain else None
        ),
        "total_descent": (
            round(ele_loss) if ele_loss else None
        ),
        "normalized_power": (
            round(norm_power) if norm_power else None
        ),
        "enhanced_avg_pace": (
            1 / avg_speed if avg_speed else None
        ),
        "enhanced_avg_speed": avg_speed,
        "enhanced_max_pace": (
            1 / max_speed if max_speed else None
        ),
        "enhanced_max_speed": max_speed,
    }


def _init_parsing_state(
    activity_name_input: str | None,
    timezone: str,
) -> dict:
    """
    Initialize mutable state for a GPX parse run.

    Args:
        activity_name_input: Optional user-supplied name.
        timezone: Default timezone string.

    Returns:
        Dict with all tracking fields at default values.
    """
    return {
        "activity_type": "Workout",
        "calories": None,
        "distance": 0,
        "avg_hr": None,
        "max_hr": None,
        "avg_cadence": None,
        "max_cadence": None,
        "first_waypoint_time": None,
        "last_waypoint_time": None,
        "avg_power": None,
        "max_power": None,
        "ele_gain": None,
        "ele_loss": None,
        "normalized_power": None,
        "avg_speed": None,
        "max_speed": None,
        "activity_name": (
            activity_name_input or "Workout"
        ),
        "activity_description": None,
        "location_resolved": False,
        "gear_id": None,
        "city": None,
        "town": None,
        "country": None,
        "pace": 0,
        "timezone": timezone,
        "lat_lon_waypoints": [],
        "ele_waypoints": [],
        "hr_waypoints": [],
        "cad_waypoints": [],
        "power_waypoints": [],
        "vel_waypoints": [],
        "pace_waypoints": [],
        "prev_latitude": None,
        "prev_longitude": None,
        "is_lat_lon_set": False,
        "is_elevation_set": False,
        "is_power_set": False,
        "is_heart_rate_set": False,
        "is_cadence_set": False,
        "is_velocity_set": False,
    }


def _process_track_metadata(
    track: gpxpy.gpx.GPXTrack,
    gpx: gpxpy.gpx.GPX,
    state: dict,
) -> None:
    """
    Extract track-level metadata into parsing state.

    Args:
        track: GPX track object.
        gpx: Root GPX object.
        state: Mutable parse state dict.

    Returns:
        None
    """
    state["activity_name"] = (
        track.name or gpx.name or "Workout"
    )
    state["activity_description"] = (
        track.description or gpx.description or None
    )
    state["activity_type"] = track.type or "Workout"


def _process_trackpoint(
    point: gpxpy.gpx.GPXTrackPoint,
    state: dict,
) -> None:
    """
    Process a single trackpoint and update parsing state.

    Args:
        point: GPX trackpoint to process.
        state: Mutable parse state dict.

    Returns:
        None
    """
    latitude = point.latitude
    longitude = point.longitude
    elevation = point.elevation
    time = point.time

    # Skip trackpoints without time (OsmAnd exports)
    if time is None:
        return

    if (
        state["prev_latitude"] is not None
        and state["prev_longitude"] is not None
    ):
        state["distance"] += geodesic(
            (
                state["prev_latitude"],
                state["prev_longitude"],
            ),
            (latitude, longitude),
        ).meters

    if elevation != 0:
        state["is_elevation_set"] = True

    if state["first_waypoint_time"] is None:
        state["first_waypoint_time"] = time

    if not state["location_resolved"]:
        location_data = (
            activities_utils
            .location_based_on_coordinates(
                latitude,
                longitude,
            )
        )
        if location_data:
            state["city"] = location_data["city"]
            state["town"] = location_data["town"]
            state["country"] = (
                location_data["country"]
            )
            state["location_resolved"] = True

    heart_rate, cadence, power = (
        _extract_extension_data(point)
    )

    if heart_rate != 0:
        state["is_heart_rate_set"] = True
    if cadence != 0:
        state["is_cadence_set"] = True
    if power != 0:
        state["is_power_set"] = True
    else:
        power = None

    instant_speed = (
        activities_utils.calculate_instant_speed(
            state["last_waypoint_time"],
            time,
            latitude,
            longitude,
            state["prev_latitude"],
            state["prev_longitude"],
        )
    )

    instant_pace = 0
    if instant_speed > 0:
        instant_pace = 1 / instant_speed
        state["is_velocity_set"] = True

    timestamp = time.strftime(_DT_FMT)

    if (
        latitude is not None
        and longitude is not None
    ):
        state["lat_lon_waypoints"].append(
            {
                "time": timestamp,
                "lat": latitude,
                "lon": longitude,
            }
        )
        state["is_lat_lon_set"] = True

    activities_utils.append_if_not_none(
        state["ele_waypoints"],
        timestamp,
        elevation,
        "ele",
    )
    activities_utils.append_if_not_none(
        state["hr_waypoints"],
        timestamp,
        heart_rate,
        "hr",
    )
    activities_utils.append_if_not_none(
        state["cad_waypoints"],
        timestamp,
        cadence,
        "cad",
    )
    activities_utils.append_if_not_none(
        state["power_waypoints"],
        timestamp,
        power,
        "power",
    )
    activities_utils.append_if_not_none(
        state["vel_waypoints"],
        timestamp,
        instant_speed,
        "vel",
    )
    activities_utils.append_if_not_none(
        state["pace_waypoints"],
        timestamp,
        instant_pace,
        "pace",
    )

    state["prev_latitude"] = latitude
    state["prev_longitude"] = longitude
    state["last_waypoint_time"] = time


def _compute_derived_metrics(
    state: dict,
    user_id: int,
    db: Session,
    tf: TimezoneFinder,
) -> None:
    """
    Compute derived activity metrics and update state.

    Args:
        state: Mutable parse state dict.
        user_id: ID of the user.
        db: SQLAlchemy database session.
        tf: Initialized TimezoneFinder instance.

    Returns:
        None
    """
    if state["ele_waypoints"]:
        gain, loss = (
            activities_utils
            .compute_elevation_gain_and_loss(
                elevations=state["ele_waypoints"],
            )
        )
        state["ele_gain"] = gain
        state["ele_loss"] = loss

    state["pace"] = activities_utils.calculate_pace(
        state["distance"],
        state["first_waypoint_time"],
        state["last_waypoint_time"],
    )

    state["activity_type"] = (
        activities_utils.define_activity_type(
            state["activity_type"],
        )
    )

    state["gear_id"] = (
        user_default_gear_utils
        .get_user_default_gear_by_activity_type(
            user_id,
            state["activity_type"],
            db,
        )
    )

    if state["hr_waypoints"]:
        state["avg_hr"], state["max_hr"] = (
            activities_utils.calculate_avg_and_max(
                state["hr_waypoints"], "hr",
            )
        )

    if state["cad_waypoints"]:
        (
            state["avg_cadence"],
            state["max_cadence"],
        ) = activities_utils.calculate_avg_and_max(
            state["cad_waypoints"], "cad",
        )

    if state["vel_waypoints"]:
        state["avg_speed"], state["max_speed"] = (
            activities_utils.calculate_avg_and_max(
                state["vel_waypoints"], "vel",
            )
        )

    if state["power_waypoints"]:
        state["avg_power"], state["max_power"] = (
            activities_utils.calculate_avg_and_max(
                state["power_waypoints"], "power",
            )
        )
        state["normalized_power"] = (
            activities_utils.calculate_np(
                state["power_waypoints"],
            )
        )

    activity_type = state["activity_type"]
    lat_lon = state["lat_lon_waypoints"]
    if activity_type not in (
        _ACTIVITY_TYPE_POOL_SWIM,
        _ACTIVITY_TYPE_TREADMILL,
    ):
        if state["is_lat_lon_set"]:
            state["timezone"] = tf.timezone_at(
                lat=lat_lon[0]["lat"],
                lng=lat_lon[0]["lon"],
            )


def _build_activity_schema(
    state: dict,
    user_id: int,
    user_privacy_settings: (
        users_privacy_settings_models.UsersPrivacySettings
    ),
) -> activities_schema.Activity:
    """
    Build an Activity Pydantic schema from parsed state.

    Args:
        state: Parsed GPX state dict.
        user_id: ID of the user.
        user_privacy_settings: ORM privacy settings object.

    Returns:
        Populated Activity schema instance.
    """
    ups = user_privacy_settings
    elapsed = (
        state["last_waypoint_time"]
        - state["first_waypoint_time"]
    ).total_seconds()
    return activities_schema.Activity(
        user_id=user_id,
        name=state["activity_name"],
        description=state["activity_description"],
        distance=(
            round(state["distance"])
            if state["distance"]
            else 0
        ),
        activity_type=state["activity_type"],
        start_time=(
            state["first_waypoint_time"]
            .strftime(_DT_FMT)
        ),
        end_time=(
            state["last_waypoint_time"]
            .strftime(_DT_FMT)
        ),
        timezone=state["timezone"],
        total_elapsed_time=elapsed,
        total_timer_time=elapsed,
        city=state["city"],
        town=state["town"],
        country=state["country"],
        elevation_gain=(
            round(state["ele_gain"])
            if state["ele_gain"]
            else None
        ),
        elevation_loss=(
            round(state["ele_loss"])
            if state["ele_loss"]
            else None
        ),
        pace=state["pace"],
        average_speed=state["avg_speed"],
        max_speed=state["max_speed"],
        average_power=(
            round(state["avg_power"])
            if state["avg_power"]
            else None
        ),
        max_power=(
            round(state["max_power"])
            if state["max_power"]
            else None
        ),
        normalized_power=(
            round(state["normalized_power"])
            if state["normalized_power"]
            else None
        ),
        average_hr=(
            round(state["avg_hr"])
            if state["avg_hr"]
            else None
        ),
        max_hr=(
            round(state["max_hr"])
            if state["max_hr"]
            else None
        ),
        average_cad=(
            round(state["avg_cadence"])
            if state["avg_cadence"]
            else None
        ),
        max_cad=(
            round(state["max_cadence"])
            if state["max_cadence"]
            else None
        ),
        calories=state["calories"],
        visibility=(
            users_privacy_settings_utils
            .visibility_to_int(
                ups.default_activity_visibility
            )
        ),
        gear_id=state["gear_id"],
        strava_gear_id=None,
        strava_activity_id=None,
        garminconnect_activity_id=None,
        garminconnect_gear_id=None,
        hide_start_time=(
            ups.hide_activity_start_time or False
        ),
        hide_location=(
            ups.hide_activity_location or False
        ),
        hide_map=ups.hide_activity_map or False,
        hide_hr=ups.hide_activity_hr or False,
        hide_power=(
            ups.hide_activity_power or False
        ),
        hide_cadence=(
            ups.hide_activity_cadence or False
        ),
        hide_elevation=(
            ups.hide_activity_elevation or False
        ),
        hide_speed=(
            ups.hide_activity_speed or False
        ),
        hide_pace=(
            ups.hide_activity_pace or False
        ),
        hide_laps=(
            ups.hide_activity_laps or False
        ),
        hide_workout_sets_steps=(
            ups.hide_activity_workout_sets_steps
            or False
        ),
        hide_gear=(
            ups.hide_activity_gear or False
        ),
    )


def parse_gpx_file(
    file: str,
    user_id: int,
    user_privacy_settings: (
        users_privacy_settings_models.UsersPrivacySettings
    ),
    db: Session,
    activity_name_input: str | None = None,
) -> ParsedGpxData:
    """
    Parse a GPX file into structured activity data.

    Args:
        file: Path to the GPX file on disk.
        user_id: ID of the user uploading the file.
        user_privacy_settings: ORM privacy settings for
            the user.
        db: SQLAlchemy database session.
        activity_name_input: Optional override for the
            activity name.

    Returns:
        ParsedGpxData with Activity schema, waypoint
        arrays, lap data, and boolean stream flags.

    Raises:
        HTTPException: 400 if the GPX has no tracks,
            no segments, or no valid timed trackpoints.
        HTTPException: 500 if the file cannot be read.
    """
    try:
        tf = TimezoneFinder()
        state = _init_parsing_state(
            activity_name_input,
            core_config.TZ,
        )

        with Path(file).open(
            "r", encoding="utf-8"
        ) as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            if not gpx.tracks:
                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Invalid GPX file - no tracks"
                        " found in the GPX file"
                    ),
                )

            for track in gpx.tracks:
                _process_track_metadata(
                    track, gpx, state
                )

                if not track.segments:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_400_BAD_REQUEST
                        ),
                        detail=(
                            "Invalid GPX file - "
                            "no segments found in "
                            "the GPX file"
                        ),
                    )

                for segment in track.segments:
                    for point in segment.points:
                        _process_trackpoint(
                            point, state
                        )

        if (
            state["first_waypoint_time"] is None
            or state["last_waypoint_time"] is None
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Invalid GPX file - no trackpoints"
                    " with valid time data found"
                ),
            )

        _compute_derived_metrics(
            state, user_id, db, tf
        )

        activity = _build_activity_schema(
            state, user_id, user_privacy_settings
        )

        laps = generate_activity_laps(
            state["lat_lon_waypoints"],
            state["ele_waypoints"],
            state["power_waypoints"],
            state["hr_waypoints"],
            state["cad_waypoints"],
            state["vel_waypoints"],
        )

        return ParsedGpxData(
            activity=activity,
            is_elevation_set=(
                state["is_elevation_set"]
            ),
            ele_waypoints=state["ele_waypoints"],
            is_power_set=state["is_power_set"],
            power_waypoints=(
                state["power_waypoints"]
            ),
            is_heart_rate_set=(
                state["is_heart_rate_set"]
            ),
            hr_waypoints=state["hr_waypoints"],
            is_velocity_set=(
                state["is_velocity_set"]
            ),
            vel_waypoints=state["vel_waypoints"],
            pace_waypoints=(
                state["pace_waypoints"]
            ),
            is_cadence_set=(
                state["is_cadence_set"]
            ),
            cad_waypoints=state["cad_waypoints"],
            is_lat_lon_set=(
                state["is_lat_lon_set"]
            ),
            lat_lon_waypoints=(
                state["lat_lon_waypoints"]
            ),
            laps=laps,
        )

    except HTTPException as http_err:
        raise http_err
    except (
        gpxpy.gpx.GPXException,
        OSError,
        ValueError,
    ) as err:
        core_logger.print_to_log(
            f"Error in parse_gpx_file - {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Failed to parse GPX file",
        ) from err


def generate_activity_laps(
    lat_lon_waypoints: list[dict],
    ele_waypoints: list[dict],
    power_waypoints: list[dict],
    hr_waypoints: list[dict],
    cad_waypoints: list[dict],
    vel_waypoints: list[dict],
    distance_per_lap_km: float = 1.0,
) -> list[LapMetrics]:
    """
    Split waypoints into distance-based laps.

    Args:
        lat_lon_waypoints: List of lat/lon dicts.
        ele_waypoints: List of elevation dicts.
        power_waypoints: List of power dicts.
        hr_waypoints: List of heart rate dicts.
        cad_waypoints: List of cadence dicts.
        vel_waypoints: List of velocity dicts.
        distance_per_lap_km: Km per lap (default 1.0).

    Returns:
        List of lap dicts with computed metrics.
    """
    laps: list[LapMetrics] = []
    current_lap_distance = 0.0
    lap_start = None

    for i in range(1, len(lat_lon_waypoints)):
        prev_point = lat_lon_waypoints[i - 1]
        current_point = lat_lon_waypoints[i]

        segment_distance = geodesic(
            (prev_point["lat"], prev_point["lon"]),
            (
                current_point["lat"],
                current_point["lon"],
            ),
        ).kilometers

        current_lap_distance += segment_distance

        if lap_start is None:
            lap_start = prev_point

        if current_lap_distance >= distance_per_lap_km:
            laps.append(
                _compute_lap_metrics(
                    start_time=lap_start["time"],
                    end_time=current_point["time"],
                    start_point=lap_start,
                    end_point=current_point,
                    total_distance=(
                        current_lap_distance
                    ),
                    ele_waypoints=ele_waypoints,
                    power_waypoints=power_waypoints,
                    hr_waypoints=hr_waypoints,
                    cad_waypoints=cad_waypoints,
                    vel_waypoints=vel_waypoints,
                )
            )

            lap_start = current_point
            current_lap_distance = 0.0

    if lap_start is not None and current_lap_distance > 0:
        laps.append(
            _compute_lap_metrics(
                start_time=lap_start["time"],
                end_time=(
                    lat_lon_waypoints[-1]["time"]
                ),
                start_point=lap_start,
                end_point=lat_lon_waypoints[-1],
                total_distance=current_lap_distance,
                ele_waypoints=ele_waypoints,
                power_waypoints=power_waypoints,
                hr_waypoints=hr_waypoints,
                cad_waypoints=cad_waypoints,
                vel_waypoints=vel_waypoints,
            )
        )

    return laps
