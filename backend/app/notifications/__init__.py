"""
Notifications module for user notification management.

This module handles the creation, retrieval, and management of user
notifications including activity alerts, follower requests, and admin approval
notifications.

Exports:
    - CRUD: get_user_notification_by_id, get_user_notifications,
        get_user_notifications_count, get_user_notifications_with_pagination,
        create_notification, mark_notification_as_read
    - Schemas: NotificationBase, NotificationCreate, NotificationRead
    - Models: Notification (ORM model)
    - Constants: NotificationType
    - Utils: create_new_activity_notification,
        create_new_duplicate_start_time_activity_notification,
        create_new_follower_request_notification,
        create_accepted_follower_request_notification,
        create_admin_new_sign_up_approval_request_notification
"""

from .crud import (
    get_user_notification_by_id,
    get_user_notifications,
    get_user_notifications_count,
    get_user_notifications_with_pagination,
    create_notification,
    mark_notification_as_read,
)
from .models import Notification as NotificationModel
from .schema import (
    NotificationBase,
    NotificationCreate,
    NotificationRead,
)
from .constants import NotificationType
from .utils import (
    create_new_activity_notification,
    create_new_duplicate_start_time_activity_notification,
    create_new_follower_request_notification,
    create_accepted_follower_request_notification,
    create_admin_new_sign_up_approval_request_notification,
)

__all__ = [
    # CRUD operations
    "get_user_notification_by_id",
    "get_user_notifications",
    "get_user_notifications_count",
    "get_user_notifications_with_pagination",
    "create_notification",
    "mark_notification_as_read",
    # Database model
    "NotificationModel",
    # Pydantic schemas
    "NotificationBase",
    "NotificationCreate",
    "NotificationRead",
    # Constants
    "NotificationType",
    # Utility functions
    "create_new_activity_notification",
    "create_new_duplicate_start_time_activity_notification",
    "create_new_follower_request_notification",
    "create_accepted_follower_request_notification",
    "create_admin_new_sign_up_approval_request_notification",
]
