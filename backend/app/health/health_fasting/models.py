"""
SQLAlchemy models for health fasting tracking.

This module defines the database models for storing user fasting sessions,
including timing, duration, type, and status information.
"""

from datetime import date as date_type, datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class HealthFasting(Base):
    """
    User fasting session tracking data.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users table.
        date: Calendar date of the fasting session.
        fast_start_time_utc: Start time of fast in UTC.
        fast_end_time_utc: End time of fast in UTC (null if ongoing).
        fast_start_time_local: Start time of fast in local timezone.
        fast_end_time_local: End time of fast in local timezone.
        target_duration_seconds: User's target fasting duration.
        actual_duration_seconds: Calculated duration when completed.
        fasting_type: Type of fasting protocol.
        status: Current status of the fasting session.
        timezone: User's timezone for local time display.
        notes: Optional notes about the fasting session.
        source: Data source for the record.
        user: Relationship to Users model.
    """

    __tablename__ = "health_fasting"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID that the health_fasting belongs",
    )
    date: Mapped[date_type] = mapped_column(
        nullable=False,
        index=True,
        comment="Calendar date of the fasting session",
    )
    fast_start_time_utc: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Start time of fast in UTC",
    )
    fast_end_time_utc: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="End time of fast in UTC (null if ongoing)",
    )
    fast_start_time_local: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="Start time of fast in local timezone",
    )
    fast_end_time_local: Mapped[datetime | None] = mapped_column(
        nullable=True,
        comment="End time of fast in local timezone",
    )
    target_duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Target fasting duration in seconds",
    )
    actual_duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Actual fasting duration in seconds",
    )
    fasting_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Type of fasting protocol (16:8, 18:6, etc.)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
        comment="Status: in_progress, completed, broken, cancelled",
    )
    timezone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="User timezone for local time display",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional notes about the fasting session",
    )
    source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Data source (manual, garmin, etc.)",
    )

    # Define a relationship to the Users model
    # TODO: Change to Mapped["User"] when all modules use mapped
    users = relationship("Users", back_populates="health_fasting")
