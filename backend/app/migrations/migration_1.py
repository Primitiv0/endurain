"""Migration 1: compute elapsed time, HR, power, cadence, speed."""

from datetime import datetime
from sqlalchemy.orm import Session

import activities.activity.crud as activities_crud
import activities.activity.utils as activities_utils

import activities.activity_streams.crud as activity_streams_crud

import migrations.crud as migrations_crud
from migrations.schema import StreamType

import core.logger as core_logger


def process_migration_1(db: Session) -> None:
    """
    Run migration 1: populate elapsed time and stream metrics.

    Args:
        db: The SQLAlchemy database session.

    Returns:
        None

    Raises:
        Exception: Logs errors per-activity; does not re-raise.
    """
    core_logger.print_to_log_and_console("Started migration 1")

    activities_processed_with_no_errors = True

    try:
        activities = activities_crud.get_all_activities(db)
    except Exception as err:
        core_logger.print_to_log_and_console(
            f"Migration 1 - Error fetching activities: {err}", "error", exc=err
        )
        return

    if activities:
        for activity in activities:
            try:
                # Ensure start_time and end_time are datetime objects
                if isinstance(activity.start_time, str):
                    activity.start_time = datetime.strptime(
                        activity.start_time, "%Y-%m-%d %H:%M:%S"
                    )
                if isinstance(activity.end_time, str):
                    activity.end_time = datetime.strptime(
                        activity.end_time, "%Y-%m-%d %H:%M:%S"
                    )

                # Initialize additional fields
                metrics: dict[str, float | None] = {
                    "avg_hr": None,
                    "max_hr": None,
                    "avg_power": None,
                    "max_power": None,
                    "np": None,
                    "avg_cadence": None,
                    "max_cadence": None,
                    "avg_speed": None,
                    "max_speed": None,
                }

                # Get activity streams
                try:
                    activity_streams = activity_streams_crud.get_activity_streams(
                        activity.id, activity.user_id, db
                    )
                except Exception as err:
                    core_logger.print_to_log_and_console(
                        f"Migration 1 - Failed to fetch streams for activity {activity.id}: {err}",
                        "warning",
                        exc=err,
                    )
                    activities_processed_with_no_errors = False
                    continue

                if not activity_streams:
                    core_logger.print_to_log_and_console(
                        f"Migration 1 - No streams found for activity {activity.id}. Skipping stream processing.",
                        "info",
                    )
                    continue

                # Map stream processing functions
                stream_processing = {
                    StreamType.HEART_RATE: ("avg_hr", "max_hr", "hr"),
                    StreamType.POWER: ("avg_power", "max_power", "power", "np"),
                    StreamType.CADENCE: ("avg_cadence", "max_cadence", "cad"),
                    StreamType.ELEVATION: None,
                    StreamType.SPEED: ("avg_speed", "max_speed", "vel"),
                    StreamType.PACE: None,
                    StreamType.LATLONG: None,
                }

                for stream in activity_streams:
                    stream_type = StreamType(stream.stream_type)
                    proc = stream_processing.get(stream_type)
                    if proc is not None:
                        attr_avg, attr_max, stream_key = proc[:3]
                        metrics[attr_avg], metrics[attr_max] = (
                            activities_utils.calculate_avg_and_max(
                                stream.stream_waypoints,
                                stream_key,
                            )
                        )
                        # Special handling for normalized power
                        if stream_type == StreamType.POWER:
                            metrics["np"] = activities_utils.calculate_np(
                                stream.stream_waypoints
                            )

                # Calculate elapsed time once
                elapsed_time_seconds = (
                    activity.end_time - activity.start_time
                ).total_seconds()

                # Set fields on the activity object
                activity.total_elapsed_time = elapsed_time_seconds
                activity.total_timer_time = elapsed_time_seconds
                activity.max_speed = metrics["max_speed"]
                activity.max_power = metrics["max_power"]
                activity.normalized_power = metrics["np"]
                activity.average_hr = metrics["avg_hr"]
                activity.max_hr = metrics["max_hr"]
                activity.average_cad = metrics["avg_cadence"]
                activity.max_cad = metrics["max_cadence"]

                # Update the activity in the database
                activities_crud.edit_activity(activity.user_id, activity, db)
                core_logger.print_to_log_and_console(
                    f"Migration 1 - Processed activity: {activity.id} - {activity.name}"
                )
            except Exception as err:
                activities_processed_with_no_errors = False
                core_logger.print_to_log_and_console(
                    f"Migration 1 - Failed to process activity {activity.id}: {err}",
                    "error",
                    exc=err,
                )

    # Mark migration as executed
    if activities_processed_with_no_errors:
        try:
            migrations_crud.set_migration_as_executed(1, db)
        except Exception as err:
            core_logger.print_to_log_and_console(
                f"Migration 1 - Failed to set migration as executed: {err}",
                "error",
                exc=err,
            )
            return
    else:
        core_logger.print_to_log_and_console(
            "Migration 1 failed to process all activities. Will try again later.",
            "error",
        )

    core_logger.print_to_log_and_console("Finished migration 1")
