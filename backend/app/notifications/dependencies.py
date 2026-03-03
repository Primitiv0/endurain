"""Notification dependency validators."""

import core.dependencies as core_dependencies


def validate_notification_id(
    notification_id: int,
) -> None:
    """
    Validate the provided notification ID.

    Args:
        notification_id: The ID to validate.

    Raises:
        ValueError: If the ID is less than 0.
    """
    core_dependencies.validate_id(
        id=notification_id,
        min=0,
        message="Invalid notification ID",
    )
