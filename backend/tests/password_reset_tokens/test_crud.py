"""Tests for password reset token CRUD operations."""

from sqlalchemy.sql import operators

import password_reset_tokens.crud as password_reset_tokens_crud


class TestClaimPasswordResetToken:
    """Test suite for claim_password_reset_token function."""

    def test_claim_password_reset_token_success(self, mock_db):
        """Test valid password reset token is claimed atomically."""
        # Arrange
        token_hash = "hashed-token"
        mock_db.execute.return_value.scalar_one_or_none.return_value = 42

        # Act
        result = password_reset_tokens_crud.claim_password_reset_token(
            token_hash, mock_db
        )

        # Assert
        assert result == 42
        stmt = mock_db.execute.call_args.args[0]
        criteria = stmt._where_criteria
        assert any(
            criterion.left.name == "token_hash"
            and criterion.operator is operators.eq
            for criterion in criteria
        )
        assert any(
            criterion.left.name == "used"
            and criterion.operator is operators.is_
            for criterion in criteria
        )
        assert any(
            criterion.left.name == "expires_at"
            and criterion.operator is operators.gt
            for criterion in criteria
        )
        assert [column.name for column in stmt._returning] == ["user_id"]
        mock_db.commit.assert_not_called()

    def test_claim_password_reset_token_invalid(self, mock_db):
        """Test invalid password reset token claim returns None."""
        # Arrange
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Act
        result = password_reset_tokens_crud.claim_password_reset_token(
            "hashed-token", mock_db
        )

        # Assert
        assert result is None
        mock_db.commit.assert_not_called()


class TestMarkUserPasswordResetTokensUsed:
    """Test suite for mark_user_password_reset_tokens_used function."""

    def test_mark_user_password_reset_tokens_used_success(self, mock_db):
        """Test all unused user reset tokens are invalidated."""
        # Arrange
        user_id = 42
        mock_db.execute.return_value.rowcount = 3

        # Act
        result = (
            password_reset_tokens_crud.mark_user_password_reset_tokens_used(
                user_id, mock_db
            )
        )

        # Assert
        assert result == 3
        stmt = mock_db.execute.call_args.args[0]
        criteria = stmt._where_criteria
        assert any(
            criterion.left.name == "user_id"
            and criterion.operator is operators.eq
            for criterion in criteria
        )
        assert any(
            criterion.left.name == "used"
            and criterion.operator is operators.is_
            for criterion in criteria
        )
        mock_db.commit.assert_not_called()