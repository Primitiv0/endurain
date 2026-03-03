"""Notification database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class Notification(Base):
    """
    User notification data.

    Attributes:
        id: Primary key.
        user_id: Foreign key to users table.
        type: Notification type.
        options: Notification options (JSON).
        read: Whether the notification has been read.
        created_at: Notification creation date.
        users: Relationship to Users model.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID that the notification belongs to",
    )
    type: Mapped[int] = mapped_column(
        nullable=False,
        comment="Notification type",
    )
    options: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Notification options (JSON)",
    )
    read: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment=("Has the notification been read (True) or not (False)"),
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=func.now(),
        comment=("Notification creation date (DateTime)"),
    )

    # Define a relationship to the Users model
    # TODO: Change to Mapped["User"] when all modules use
    # mapped
    users = relationship("Users", back_populates="notifications")
