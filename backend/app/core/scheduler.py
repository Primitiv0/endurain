"""Background scheduler setup for recurring maintenance jobs."""

from collections.abc import Callable, Sequence

import activities.activity.utils as activities_utils
import auth.oauth_state.utils as oauth_state_utils
import auth.security_stores as auth_security_stores
import auth.sessions.utils as users_session_utils
import core.logger as core_logger
import core.network as core_network
import garmin.activity_utils as garmin_activity_utils
import garmin.health_utils as garmin_health_utils
import password_reset_tokens.utils as password_reset_tokens_utils
import sign_up_tokens.utils as sign_up_tokens_utils
import strava.activity_utils as strava_activity_utils
import strava.utils as strava_utils
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from auth.sessions.rotated_refresh_tokens import (
    utils as rotated_tokens_utils,
)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """
    Start the scheduler and register recurring jobs.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    if not scheduler.running:
        scheduler.start()

    add_scheduler_job(
        strava_utils.refresh_strava_tokens,
        "interval",
        60,
        [True],
        "refresh Strava user tokens every 60 minutes",
    )

    add_scheduler_job(
        strava_activity_utils.retrieve_strava_users_activities_for_days,
        "interval",
        60,
        [1, True],
        "retrieve last day Strava users activities",
    )

    add_scheduler_job(
        garmin_activity_utils.retrieve_garminconnect_users_activities_for_days,
        "interval",
        60,
        [1],
        "retrieve last day Garmin Connect users activities",
    )

    add_scheduler_job(
        garmin_health_utils.retrieve_garminconnect_users_health_for_days,
        "interval",
        240,
        [1],
        "retrieve last day Garmin Connect users health data",
    )

    add_scheduler_job(
        password_reset_tokens_utils.delete_invalid_tokens_from_db,
        "interval",
        60,
        [],
        "delete invalid password reset tokens from the database",
    )

    add_scheduler_job(
        sign_up_tokens_utils.delete_invalid_tokens_from_db,
        "interval",
        60,
        [],
        "delete invalid sign-up tokens from the database",
    )

    add_scheduler_job(
        oauth_state_utils.delete_expired_oauth_states_from_db,
        "interval",
        5,
        [],
        "delete expired OAuth states from the database",
    )

    add_scheduler_job(
        users_session_utils.cleanup_idle_sessions,
        "interval",
        15,
        [],
        "delete expired sessions from the database",
    )

    add_scheduler_job(
        rotated_tokens_utils.cleanup_expired_rotated_tokens,
        "interval",
        1,
        [],
        "delete expired rotated tokens from the database",
    )

    add_scheduler_job(
        auth_security_stores.cleanup_expired_pending_mfa_logins,
        "interval",
        5,
        [],
        "evict expired pending MFA login entries",
    )

    add_scheduler_job(
        activities_utils.generate_missing_activity_thumbnails,
        "interval",
        60,
        [],
        "generate thumbnails for activities missing one",
    )

    add_scheduler_job(
        core_network.refresh_trusted_proxy_hostnames,
        "interval",
        1,
        [],
        "refresh trusted proxy hostname resolutions",
    )


def _scheduler_job_id(description: str) -> str:
    """
    Build a stable scheduler job ID from its description.

    Args:
        description: Human-readable job description.

    Returns:
        Stable APScheduler job identifier.

    Raises:
        None.
    """
    return "endurain_" + "_".join(description.lower().split())


def add_scheduler_job(
    func: Callable[..., object],
    interval: str,
    minutes: int,
    args: Sequence[object],
    description: str,
) -> None:
    """
    Register or replace a recurring scheduler job.

    Args:
        func: Callable to execute.
        interval: APScheduler trigger name.
        minutes: Interval length in minutes.
        args: Positional arguments passed to func.
        description: Human-readable job description.

    Returns:
        None.

    Raises:
        None.
    """
    try:
        core_logger.print_to_log(f"Added scheduler job to {description} every {minutes} minutes")
        scheduler.add_job(
            func,
            interval,
            minutes=minutes,
            args=list(args),
            id=_scheduler_job_id(description),
            replace_existing=True,
        )
    except Exception as err:
        core_logger.print_to_log(
            f"Failed to add scheduler job to {description}: {type(err).__name__}",
            "error",
            exc=err,
        )


def stop_scheduler() -> None:
    """
    Stop the scheduler if it is running.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
