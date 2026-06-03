"""Centralized timezone conversion utilities."""

from datetime import datetime
from zoneinfo import ZoneInfo

import core.config as core_config


def format_aware_datetime(
    dt: datetime | str,
    tz_name: str | None = None,
) -> str:
    """
    Convert a datetime to a timezone-aware string.

    Assumes UTC if the datetime has no tzinfo.
    Converts to the specified timezone (or the
    server default) and formats as ISO 8601 without
    offset.

    Args:
        dt: A datetime object or ISO 8601 string.
        tz_name: IANA timezone name. Falls back to
            the server TZ setting if None.

    Returns:
        Formatted datetime string without offset.
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    timezone = ZoneInfo(tz_name) if tz_name else ZoneInfo(core_config.settings.TZ)

    return dt.astimezone(timezone).strftime("%Y-%m-%dT%H:%M:%S")
