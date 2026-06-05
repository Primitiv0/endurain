"""Tests for core.timezone module."""

from datetime import UTC, datetime
from unittest.mock import patch

import core.config as core_config
import core.timezone as core_timezone


class TestFormatAwareDatetime:
    """Tests for format_aware_datetime function."""

    def test_naive_datetime_assumes_utc(self):
        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = core_timezone.format_aware_datetime(dt)
        assert result == "2025-01-15T10:30:00"

    def test_aware_datetime_utc(self):
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = core_timezone.format_aware_datetime(dt)
        assert result == "2025-01-15T10:30:00"

    def test_string_parsed_and_formatted(self):
        result = core_timezone.format_aware_datetime("2025-01-15T10:30:00")
        assert result == "2025-01-15T10:30:00"

    def test_custom_tz_name(self):
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = core_timezone.format_aware_datetime(dt, tz_name="America/New_York")
        assert result == "2025-01-15T05:30:00"

    def test_patched_tz_setting(self):
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        with patch.object(core_config.settings, "TZ", "America/New_York"):
            result = core_timezone.format_aware_datetime(dt)
        assert result == "2025-01-15T05:30:00"

    def test_output_format(self):
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = core_timezone.format_aware_datetime(dt)
        assert result == "2025-01-15T10:30:00"
