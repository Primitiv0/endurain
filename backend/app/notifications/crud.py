"""CRUD operations for notifications."""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

import notifications.models as notifications_models
import notifications.schema as notifications_schema

import core.decorators as core_decorators


@core_decorators.handle_db_errors
def get_user_notification_by_id(
    notification_id: int,
    user_id: int,
    db: Session,
) -> notifications_models.Notification | None:
    """
    Retrieve a notification by ID for a user.

    Args:
        notification_id: The notification ID.
        user_id: The owning user ID.
        db: Database session.

    Returns:
        Notification model if found, otherwise None.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(notifications_models.Notification).where(
        notifications_models.Notification.user_id == user_id,
        notifications_models.Notification.id == notification_id,
    )
    return db.execute(stmt).scalars().first()


@core_decorators.handle_db_errors
def get_user_notifications(
    user_id: int,
    db: Session,
) -> list[notifications_models.Notification]:
    """
    Retrieve all notifications for a user.

    Args:
        user_id: The owning user ID.
        db: Database session.

    Returns:
        List of Notification models for the user.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(notifications_models.Notification).where(
        notifications_models.Notification.user_id == user_id
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def get_user_notifications_count(
    user_id: int,
    db: Session,
) -> int:
    """
    Count notifications for a user.

    Args:
        user_id: The owning user ID.
        db: Database session.

    Returns:
        Number of notifications for the user.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = (
        select(func.count())
        .select_from(notifications_models.Notification)
        .where(notifications_models.Notification.user_id == user_id)
    )
    return db.execute(stmt).scalar_one()


@core_decorators.handle_db_errors
def get_user_notifications_with_pagination(
    user_id: int,
    db: Session,
    page_number: int = 1,
    num_records: int = 5,
) -> list[notifications_models.Notification]:
    """
    Retrieve paginated notifications for a user.

    Args:
        user_id: The owning user ID.
        db: Database session.
        page_number: Page number (default 1).
        num_records: Records per page (default 5).

    Returns:
        List of Notification models for the page.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = (
        select(notifications_models.Notification)
        .where(notifications_models.Notification.user_id == user_id)
        .order_by(desc(notifications_models.Notification.created_at))
        .offset((page_number - 1) * num_records)
        .limit(num_records)
    )
    return db.execute(stmt).scalars().all()


@core_decorators.handle_db_errors
def create_notification(
    notification: notifications_schema.NotificationCreate,
    db: Session,
) -> notifications_models.Notification:
    """
    Create a new notification record.

    Args:
        notification: The notification data to create.
        db: Database session.

    Returns:
        The newly created Notification model.

    Raises:
        HTTPException: If a database error occurs.
    """
    new_notification = notifications_models.Notification(
        user_id=notification.user_id,
        type=notification.type,
        options=notification.options,
        read=False,
        created_at=func.now(),
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


@core_decorators.handle_db_errors
def mark_notification_as_read(
    notification_id: int,
    user_id: int,
    db: Session,
) -> notifications_models.Notification | None:
    """
    Mark a notification as read for a user.

    Args:
        notification_id: The notification ID.
        user_id: The owning user ID.
        db: Database session.

    Returns:
        Updated Notification model, or None if not found.

    Raises:
        HTTPException: If a database error occurs.
    """
    stmt = select(notifications_models.Notification).where(
        notifications_models.Notification.user_id == user_id,
        notifications_models.Notification.id == notification_id,
    )
    notification = db.execute(stmt).scalars().first()
    if notification is None:
        return None
    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification
