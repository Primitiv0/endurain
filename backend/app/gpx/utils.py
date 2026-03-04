"""Utilities for parsing GPX files into activity data."""

from datetime import datetime
from pathlib import Path

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
) -> tuple[int | str, int | str, int]:
    """
    Extract HR, cadence, and power from extensions.

    Args:
        point: A gpxpy trackpoint with optional extension elements.

    Returns:
        Tuple of (heart_rate, cadence, power).
    """
    heart_rate: int | str = 0
    cadence: int | str = 0
    power: int = 0

    if not point.extensions:
        return heart_rate, cadence, power

    for extension in point.extensions:
        tag = extension.tag
        if tag.endswith("TrackPointExtension"):
            hr_el = extension.find(_HR_NS)
            if hr_el is not None:
                heart_rate = hr_el.text
            cad_el = extension.find(_CAD_NS)
            if cad_el is not None:
                cadence = cad_el.text
            # OpenTracks fallback
            if hr_el is None and cad_el is None:
                for child in extension:
                    if child.tag.endswith("hr"):
                        heart_rate = child.text
                    elif child.tag.endswith("cad"):
                        cadence = child.text
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
) -> dict:
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


def parse_gpx_file(
    file: str,
    user_id: int,
    user_privacy_settings: (
        users_privacy_settings_models.UsersPrivacySettings
    ),
    db: Session,
    activity_name_input: str | None = None,
) -> dict:
    """
    Parse a GPX file into structured activity data.

    Args:
        file: Path to the GPX file on disk.
        user_id: ID of the user uploading the file.
        user_privacy_settings: ORM privacy settings for the user.
        db: SQLAlchemy database session.
        activity_name_input: Optional override for the activity name.

    Returns:
        Dict containing the Activity schema, waypoint
        arrays, lap data, and boolean stream flags.

    Raises:
        HTTPException: 400 if the GPX has no tracks, no segments, or no valid 
            timed trackpoints.
        HTTPException: 500 if the file cannot be read.
    """
    try:
        # Create an instance of TimezoneFinder
        tf = TimezoneFinder()
        timezone = core_config.TZ

        # Initialize default values for various variables
        activity_type = "Workout"
        calories = None
        distance = 0
        avg_hr = None
        max_hr = None
        avg_cadence = None
        max_cadence = None
        first_waypoint_time = None
        last_waypoint_time = None
        avg_power = None
        max_power = None
        ele_gain = None
        ele_loss = None
        normalized_power = None
        avg_speed = None
        max_speed = None
        activity_name = (
            activity_name_input
            if activity_name_input
            else "Workout"
        )
        activity_description = None
        location_resolved = False
        gear_id = None

        city = None
        town = None
        country = None
        pace = 0

        # Arrays to store waypoint data
        lat_lon_waypoints = []
        ele_waypoints = []
        hr_waypoints = []
        cad_waypoints = []
        power_waypoints = []
        vel_waypoints = []
        pace_waypoints = []

        # Initialize variables to store previous latitude and longitude
        prev_latitude, prev_longitude = None, None

        # Stream detection flags for elevation, power,
        # HR, cadence, and velocity
        is_lat_lon_set = False
        is_elevation_set = False
        is_power_set = False
        is_heart_rate_set = False
        is_cadence_set = False
        is_velocity_set = False

        # Parse the GPX file
        with Path(file).open("r", encoding="utf-8") as gpx_file:
            gpx = gpxpy.parse(gpx_file)

            if gpx.tracks:
                # Iterate over tracks in the GPX file
                for track in gpx.tracks:
                    # Set activity name, description, and type if available
                    activity_name = (
                        track.name
                        if track.name
                        else gpx.name if gpx.name else "Workout"
                    )
                    activity_description = (
                        track.description
                        if track.description
                        else gpx.description if gpx.description else None
                    )
                    activity_type = track.type if track.type else "Workout"

                    if track.segments:
                        # Iterate over segments in each track
                        for segment in track.segments:
                            # Iterate over points in each segment
                            for point in segment.points:
                                # Extract coordinates, elevation, time
                                latitude = point.latitude
                                longitude = point.longitude
                                elevation = point.elevation
                                time = point.time

                                # Skip trackpoints without time
                                # (common in OsmAnd exports)
                                if time is None:
                                    continue

                                # Calculate distance between waypoints
                                if (
                                    prev_latitude is not None
                                    and prev_longitude is not None
                                ):
                                    distance += geodesic(
                                        (prev_latitude, prev_longitude),
                                        (latitude, longitude),
                                    ).meters

                                if elevation != 0:
                                    is_elevation_set = True

                                if first_waypoint_time is None:
                                    first_waypoint_time = point.time

                                if not location_resolved:
                                    # Geocode first trackpoint
                                    location_data = (
                                        activities_utils
                                        .location_based_on_coordinates(
                                            latitude,
                                            longitude,
                                        )
                                    )

                                    # Extract city, town, country
                                    if location_data:
                                        city = location_data["city"]
                                        town = location_data["town"]
                                        country = (
                                            location_data["country"]
                                        )
                                        location_resolved = True

                                # Extract HR, cadence, and power
                                heart_rate, cadence, power = (
                                    _extract_extension_data(point)
                                )

                                # Check if heart rate, cadence, power are set
                                if heart_rate != 0:
                                    is_heart_rate_set = True

                                if cadence != 0:
                                    is_cadence_set = True

                                if power != 0:
                                    is_power_set = True
                                else:
                                    power = None

                                # Calculate instant speed, pace, and update 
                                # waypoint arrays
                                instant_speed = (
                                    activities_utils.calculate_instant_speed(
                                        last_waypoint_time,
                                        time,
                                        latitude,
                                        longitude,
                                        prev_latitude,
                                        prev_longitude,
                                    )
                                )

                                # Calculate instant pace
                                instant_pace = 0
                                if instant_speed > 0:
                                    instant_pace = 1 / instant_speed
                                    is_velocity_set = True

                                timestamp = time.strftime(_DT_FMT)

                                # Append waypoint data to respective arrays
                                if latitude is not None and longitude is not None:
                                    lat_lon_waypoints.append(
                                        {
                                            "time": timestamp,
                                            "lat": latitude,
                                            "lon": longitude,
                                        }
                                    )
                                    is_lat_lon_set = True

                                activities_utils.append_if_not_none(
                                    ele_waypoints, timestamp, elevation, "ele"
                                )
                                activities_utils.append_if_not_none(
                                    hr_waypoints, timestamp, heart_rate, "hr"
                                )
                                activities_utils.append_if_not_none(
                                    cad_waypoints, timestamp, cadence, "cad"
                                )
                                activities_utils.append_if_not_none(
                                    power_waypoints, timestamp, power, "power"
                                )
                                activities_utils.append_if_not_none(
                                    vel_waypoints, timestamp, instant_speed, "vel"
                                )
                                activities_utils.append_if_not_none(
                                    pace_waypoints, timestamp, instant_pace, "pace"
                                )

                                # Update previous latitude, longitude, and last
                                # waypoint time
                                prev_latitude, prev_longitude, last_waypoint_time = (
                                    latitude,
                                    longitude,
                                    time,
                                )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid GPX file - no segments found in the GPX file",
                        )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid GPX file - no tracks found in the GPX file",
                )

        # Check if we have at least one valid trackpoint with time data
        if first_waypoint_time is None or last_waypoint_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GPX file - no trackpoints with valid time data found",
            )

        # Calculate elevation gain/loss, pace, average speed, and average power
        if ele_waypoints:
            ele_gain, ele_loss = activities_utils.compute_elevation_gain_and_loss(
                elevations=ele_waypoints
            )

        pace = activities_utils.calculate_pace(
            distance, first_waypoint_time, last_waypoint_time
        )

        # Activity type
        activity_type = activities_utils.define_activity_type(activity_type)

        gear_id = user_default_gear_utils.get_user_default_gear_by_activity_type(
            user_id, activity_type, db
        )

        # Calculate average and maximum heart rate
        if hr_waypoints:
            avg_hr, max_hr = (
                activities_utils.calculate_avg_and_max(
                    hr_waypoints, "hr",
                )
            )

        # Calculate average and maximum cadence
        if cad_waypoints:
            avg_cadence, max_cadence = (
                activities_utils.calculate_avg_and_max(
                    cad_waypoints, "cad",
                )
            )

        # Calculate average and maximum velocity
        if vel_waypoints:
            avg_speed, max_speed = (
                activities_utils.calculate_avg_and_max(
                    vel_waypoints, "vel",
                )
            )

        # Calculate average and maximum power
        if power_waypoints:
            avg_power, max_power = (
                activities_utils.calculate_avg_and_max(
                    power_waypoints, "power",
                )
            )

            # Calculate normalised power
            normalized_power = (
                activities_utils.calculate_np(
                    power_waypoints,
                )
            )

        # Calculate the elapsed time
        elapsed_time = last_waypoint_time - first_waypoint_time

        if activity_type not in (
            _ACTIVITY_TYPE_POOL_SWIM,
            _ACTIVITY_TYPE_TREADMILL,
        ):
            if is_lat_lon_set:
                timezone = tf.timezone_at(
                    lat=lat_lon_waypoints[0]["lat"],
                    lng=lat_lon_waypoints[0]["lon"],
                )

        # Create an Activity object with parsed data
        activity = activities_schema.Activity(
            user_id=user_id,
            name=activity_name,
            description=activity_description,
            distance=round(distance) if distance else 0,
            activity_type=activity_type,
            start_time=first_waypoint_time.strftime(_DT_FMT),
            end_time=last_waypoint_time.strftime(_DT_FMT),
            timezone=timezone,
            total_elapsed_time=elapsed_time.total_seconds(),
            total_timer_time=elapsed_time.total_seconds(),
            city=city,
            town=town,
            country=country,
            elevation_gain=round(ele_gain) if ele_gain else None,
            elevation_loss=round(ele_loss) if ele_loss else None,
            pace=pace,
            average_speed=avg_speed,
            max_speed=max_speed,
            average_power=round(avg_power) if avg_power else None,
            max_power=round(max_power) if max_power else None,
            normalized_power=(
                round(normalized_power)
                if normalized_power
                else None
            ),
            average_hr=round(avg_hr) if avg_hr else None,
            max_hr=round(max_hr) if max_hr else None,
            average_cad=round(avg_cadence) if avg_cadence else None,
            max_cad=round(max_cadence) if max_cadence else None,
            calories=calories,
            visibility=users_privacy_settings_utils.visibility_to_int(
                user_privacy_settings.default_activity_visibility
            ),
            gear_id=gear_id,
            strava_gear_id=None,
            strava_activity_id=None,
            garminconnect_activity_id=None,
            garminconnect_gear_id=None,
            hide_start_time=user_privacy_settings.hide_activity_start_time or False,
            hide_location=user_privacy_settings.hide_activity_location or False,
            hide_map=user_privacy_settings.hide_activity_map or False,
            hide_hr=user_privacy_settings.hide_activity_hr or False,
            hide_power=user_privacy_settings.hide_activity_power or False,
            hide_cadence=user_privacy_settings.hide_activity_cadence or False,
            hide_elevation=user_privacy_settings.hide_activity_elevation or False,
            hide_speed=user_privacy_settings.hide_activity_speed or False,
            hide_pace=user_privacy_settings.hide_activity_pace or False,
            hide_laps=user_privacy_settings.hide_activity_laps or False,
            hide_workout_sets_steps=user_privacy_settings.hide_activity_workout_sets_steps
            or False,
            hide_gear=user_privacy_settings.hide_activity_gear or False,
        )

        # Generate activity laps
        laps = generate_activity_laps(
            lat_lon_waypoints,
            ele_waypoints,
            power_waypoints,
            hr_waypoints,
            cad_waypoints,
            vel_waypoints,
        )

        # Return parsed data as a dictionary
        return {
            "activity": activity,
            "is_elevation_set": is_elevation_set,
            "ele_waypoints": ele_waypoints,
            "is_power_set": is_power_set,
            "power_waypoints": power_waypoints,
            "is_heart_rate_set": is_heart_rate_set,
            "hr_waypoints": hr_waypoints,
            "is_velocity_set": is_velocity_set,
            "vel_waypoints": vel_waypoints,
            "pace_waypoints": pace_waypoints,
            "is_cadence_set": is_cadence_set,
            "cad_waypoints": cad_waypoints,
            "is_lat_lon_set": is_lat_lon_set,
            "lat_lon_waypoints": lat_lon_waypoints,
            "laps": laps,
        }

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
) -> list[dict]:
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
    laps = []
    current_lap_distance = 0.0
    lap_start = None

    for i in range(1, len(lat_lon_waypoints)):
        prev_point = lat_lon_waypoints[i - 1]
        current_point = lat_lon_waypoints[i]

        segment_distance = geodesic(
            (prev_point["lat"], prev_point["lon"]),
            (current_point["lat"], current_point["lon"]),
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
                    total_distance=current_lap_distance,
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
                end_time=lat_lon_waypoints[-1]["time"],
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
