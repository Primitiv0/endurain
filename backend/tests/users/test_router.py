"""Tests for user management router functions."""

from unittest.mock import MagicMock, patch

import pytest

import users.users.router as users_router
import users.users.schema as users_schema


class TestEditUserPassword:
    """
    Test suite for admin password reset route.
    """

    @pytest.mark.asyncio
    @patch("users.users.router.users_sessions_crud.delete_sessions_by_user")
    @patch("users.users.router.users_crud.edit_user_password")
    async def test_revokes_target_sessions_after_password_reset(
        self,
        mock_edit_password,
        mock_delete_sessions,
        mock_db,
    ):
        """
        Test admin password resets delete existing target sessions.
        """
        user_id = 42
        new_password = "new-secure-password"
        identity_service = MagicMock()
        user_attributes = users_schema.UsersAdminEditPassword(password=new_password)

        result = await users_router.edit_user_password(
            user_id=user_id,
            _validate_id=MagicMock(),
            user_attributes=user_attributes,
            _check_scope=MagicMock(),
            identity_service=identity_service,
            db=mock_db,
        )

        mock_edit_password.assert_called_once_with(
            user_id,
            new_password,
            identity_service,
            mock_db,
        )
        mock_delete_sessions.assert_called_once_with(user_id, mock_db)
        assert result == {"message": f"User ID {user_id} password updated successfully"}
