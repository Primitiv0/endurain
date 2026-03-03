"""Utility functions for notification creation."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.database import SessionLocal
import core.logger as core_logger

import notifications.constants as notifications_constants
import notifications.crud as notifications_crud
import notifications.models as notifications_models
import notifications.schema as notifications_schema

import users.users.crud as users_crud
import users.users.models as users_models
import users.users.utils as users_utils

import websocket.manager as websocket_manager
import websocket.utils as websocket_utils


async def _create_and_notify(
    notification_data: notifications_schema.NotificationCreate,
    ws_message: str,
    notify_user_id: int,
    ws_manager: websocket_manager.WebSocketManager,
    db: Session,
) -> notifications_models.Notification:
    """
    Create notification and send WebSocket message.

    Args:
        notification_data: The notification to create.
        ws_message: WebSocket message type string.
        notify_user_id: User to notify via WebSocket.
        ws_manager: WebSocket manager instance.
        db: Database session.

    Returns:
        The created Notification model.
    """
    notification = notifications_crud.create_notification(notification_data, db)
    json_data = {
        "message": ws_message,
        "notification_id": notification.id,
    }
    await websocket_utils.notify_frontend(notify_user_id, ws_manager, json_data)
    return notification


async def create_new_activity_notification(
    user_id: int,
    activity_id: int,
    websocket_manager: websocket_manager.WebSocketManager,
) -> notifications_models.Notification:
    """
    Create a new activity notification.

    Args:
        user_id: The user ID to notify.
        activity_id: The new activity ID.
        websocket_manager: WebSocket manager instance.

    Returns:
        The created Notification model.

    Raises:
        HTTPException: If creation or notify fails.
    """
    with SessionLocal() as db:
        try:
            return await _create_and_notify(
                notifications_schema.NotificationCreate(
                    user_id=user_id,
                    type=(notifications_constants.NotificationType.NEW_ACTIVITY),
                    options={
                        "activity_id": activity_id,
                    },
                ),
                "NEW_ACTIVITY_NOTIFICATION",
                user_id,
                websocket_manager,
                db,
            )
        except HTTPException as http_err:
            raise http_err
        except Exception as err:
            core_logger.print_to_log(
                f"Error in create_new_activity_notification: {err}",
                "error",
                exc=err,
            )
            raise HTTPException(
                status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail="Internal Server Error",
            ) from err


async def create_new_duplicate_start_time_activity_notification(
    user_id: int,
    activity_id: int,
    websocket_manager: websocket_manager.WebSocketManager,
) -> notifications_models.Notification:
    """
    Create a duplicate start time notification.

    Args:
        user_id: The user ID to notify.
        activity_id: The duplicate activity ID.
        websocket_manager: WebSocket manager instance.

    Returns:
        The created Notification model.

    Raises:
        HTTPException: If creation or notify fails.
    """
    with SessionLocal() as db:
        try:
            return await _create_and_notify(
                notifications_schema.NotificationCreate(
                    user_id=user_id,
                    type=(notifications_constants.NotificationType.DUPLICATE_ACTIVITY),
                    options={
                        "activity_id": activity_id,
                    },
                ),
                "NEW_DUPLICATE_ACTIVITY_START_TIME" "_NOTIFICATION",
                user_id,
                websocket_manager,
                db,
            )
        except HTTPException as http_err:
            raise http_err
        except Exception as err:
            core_logger.print_to_log(
                "Error in create_new_duplicate_start_time_activity"
                f"_notification: {err}",
                "error",
                exc=err,
            )
            raise HTTPException(
                status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail="Internal Server Error",
            ) from err


async def create_new_follower_request_notification(
    user_id: int,
    target_user_id: int,
    websocket_manager: websocket_manager.WebSocketManager,
    db: Session,
) -> notifications_models.Notification:
    """
    Create a new follower request notification.

    Args:
        user_id: The requesting user ID.
        target_user_id: The user to notify.
        websocket_manager: WebSocket manager instance.
        db: Database session.

    Returns:
        The created Notification model.

    Raises:
        HTTPException: If user not found or error.
    """
    try:
        user = users_crud.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=(status.HTTP_404_NOT_FOUND),
                detail="User not found",
            )
        return await _create_and_notify(
            notifications_schema.NotificationCreate(
                user_id=target_user_id,
                type=(notifications_constants.NotificationType.NEW_FOLLOWER_REQUEST),
                options={
                    "user_id": user_id,
                    "user_name": user.name,
                    "user_username": user.username,
                },
            ),
            "NEW_FOLLOWER_REQUEST_NOTIFICATION",
            target_user_id,
            websocket_manager,
            db,
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        core_logger.print_to_log(
            f"Error in create_new_follower_request_notification: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


async def create_accepted_follower_request_notification(
    user_id: int,
    target_user_id: int,
    websocket_manager: websocket_manager.WebSocketManager,
    db: Session,
) -> notifications_models.Notification:
    """
    Create an accepted follower request notification.

    Args:
        user_id: The accepting user ID.
        target_user_id: The user to notify.
        websocket_manager: WebSocket manager instance.
        db: Database session.

    Returns:
        The created Notification model.

    Raises:
        HTTPException: If user not found or error.
    """
    try:
        user = users_crud.get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(
                status_code=(status.HTTP_404_NOT_FOUND),
                detail="User not found",
            )
        return await _create_and_notify(
            notifications_schema.NotificationCreate(
                user_id=target_user_id,
                type=(
                    notifications_constants.NotificationType.NEW_FOLLOWER_REQUEST_ACCEPTED
                ),
                options={
                    "user_id": user_id,
                    "user_name": user.name,
                    "user_username": user.username,
                },
            ),
            "NEW_FOLLOWER_REQUEST_ACCEPTED" "_NOTIFICATION",
            user_id,
            websocket_manager,
            db,
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        core_logger.print_to_log(
            f"Error in create_accepted_follower_request_notification: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err


async def create_admin_new_sign_up_approval_request_notification(
    user: users_models.Users,
    websocket_manager: websocket_manager.WebSocketManager,
    db: Session,
) -> None:
    """
    Notify all admins of a new sign-up request.

    Args:
        user: The user requesting sign-up.
        websocket_manager: WebSocket manager instance.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: If creation or notify fails.
    """
    try:
        admins = users_utils.get_admin_users_or_404(db)
        for admin in admins:
            await _create_and_notify(
                notifications_schema.NotificationCreate(
                    user_id=admin.id,
                    type=(
                        notifications_constants.NotificationType.ADMIN_NEW_SIGN_UP_APPROVAL_REQUEST
                    ),
                    options={
                        "user_id": user.id,
                        "user_name": user.name,
                        "user_username": (user.username),
                    },
                ),
                "ADMIN_NEW_SIGN_UP_APPROVAL" "_REQUEST_NOTIFICATION",
                admin.id,
                websocket_manager,
                db,
            )
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        core_logger.print_to_log(
            "Error in create_admin_new_sign_up_approval_request"
            f"_notification: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Internal Server Error",
        ) from err
