"""Tests for password reset token utilities."""

from unittest.mock import MagicMock, patch

import password_reset_tokens.utils as password_reset_tokens_utils


class TestUsePasswordResetToken:
    """
    Test suite for use_password_reset_token function.
    """

    @patch(
        "password_reset_tokens.utils.users_sessions_crud."
        "delete_sessions_by_user"
    )
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.mark_password_reset_token_used"
    )
    @patch("password_reset_tokens.utils.users_crud.edit_user_password")
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.get_password_reset_token_by_hash"
    )
    def test_revokes_sessions_after_successful_reset(
        self,
        mock_get_token,
        mock_edit_password,
        mock_mark_used,
        mock_delete_sessions,
        mock_db,
    ):
        """
        Test password reset deletes existing user sessions.
        """
        # Arrange
        db_token = MagicMock()
        db_token.id = "reset-token-id"
        db_token.user_id = 42
        mock_get_token.return_value = db_token
        password_hasher = MagicMock()

        # Act
        password_reset_tokens_utils.use_password_reset_token(
            "plain-reset-token",
            "new-password",
            password_hasher,
            mock_db,
        )

        # Assert
        mock_edit_password.assert_called_once_with(
            db_token.user_id,
            "new-password",
            password_hasher,
            mock_db,
        )
        mock_mark_used.assert_called_once_with(db_token.id, mock_db)
        mock_delete_sessions.assert_called_once_with(db_token.user_id, mock_db)