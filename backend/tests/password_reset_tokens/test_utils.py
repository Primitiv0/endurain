"""Tests for password reset token utilities."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

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
        "password_reset_tokens_crud.mark_user_password_reset_tokens_used"
    )
    @patch("password_reset_tokens.utils.users_crud.edit_user_password")
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.claim_password_reset_token"
    )
    @patch(
        "password_reset_tokens.utils.auth_security_stores."
        "clear_pending_mfa_for_user"
    )
    def test_revokes_sessions_after_successful_reset(
        self,
        mock_clear_pending_mfa,
        mock_claim_token,
        mock_edit_password,
        mock_mark_user_tokens_used,
        mock_delete_sessions,
        mock_db,
    ):
        """
        Test password reset deletes existing user sessions.
        """
        # Arrange
        user_id = 42
        token = "plain-reset-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        mock_claim_token.return_value = user_id
        password_hasher = MagicMock()

        # Act
        password_reset_tokens_utils.use_password_reset_token(
            token,
            "new-password",
            password_hasher,
            mock_db,
        )

        # Assert
        mock_claim_token.assert_called_once_with(token_hash, mock_db)
        mock_edit_password.assert_called_once_with(
            user_id,
            "new-password",
            password_hasher,
            mock_db,
            commit=False,
        )
        mock_mark_user_tokens_used.assert_called_once_with(user_id, mock_db)
        mock_delete_sessions.assert_called_once_with(
            user_id, mock_db, commit=False
        )
        mock_db.commit.assert_called_once_with()
        mock_clear_pending_mfa.assert_called_once_with(user_id)

    @patch("password_reset_tokens.utils.users_crud.edit_user_password")
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.claim_password_reset_token"
    )
    def test_invalid_token_raises_bad_request(
        self,
        mock_claim_token,
        mock_edit_password,
        mock_db,
    ):
        """
        Test invalid password reset token is rejected.
        """
        # Arrange
        mock_claim_token.return_value = None
        password_hasher = MagicMock()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            password_reset_tokens_utils.use_password_reset_token(
                "plain-reset-token",
                "new-password",
                password_hasher,
                mock_db,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        mock_edit_password.assert_not_called()
        mock_db.commit.assert_not_called()

    @patch(
        "password_reset_tokens.utils.auth_security_stores."
        "clear_pending_mfa_for_user"
    )
    @patch(
        "password_reset_tokens.utils.users_sessions_crud."
        "delete_sessions_by_user"
    )
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.mark_user_password_reset_tokens_used"
    )
    @patch("password_reset_tokens.utils.users_crud.edit_user_password")
    @patch(
        "password_reset_tokens.utils."
        "password_reset_tokens_crud.claim_password_reset_token"
    )
    def test_rolls_back_when_commit_fails(
        self,
        mock_claim_token,
        mock_edit_password,
        mock_mark_user_tokens_used,
        mock_delete_sessions,
        mock_clear_pending_mfa,
        mock_db,
    ):
        """
        Test failed reset transaction rolls back database changes.
        """
        # Arrange
        mock_claim_token.return_value = 42
        mock_db.commit.side_effect = SQLAlchemyError("commit failed")
        password_hasher = MagicMock()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            password_reset_tokens_utils.use_password_reset_token(
                "plain-reset-token",
                "new-password",
                password_hasher,
                mock_db,
            )

        assert (
            exc_info.value.status_code
            == status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        mock_edit_password.assert_called_once()
        mock_mark_user_tokens_used.assert_called_once()
        mock_delete_sessions.assert_called_once()
        mock_db.rollback.assert_called_once_with()
        mock_clear_pending_mfa.assert_not_called()
