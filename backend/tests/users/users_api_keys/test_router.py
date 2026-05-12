"""Tests for users_api_keys API endpoints."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

import users.users_api_keys.models as users_api_keys_models
import users.users_api_keys.schema as users_api_keys_schema


class TestGetUserApiKeys:
    """
    Test suite for GET /api_keys endpoint.
    """

    @patch("users.users_api_keys.router.users_api_keys_crud.get_api_keys_by_user_id")
    def test_get_user_api_keys_success(
        self, mock_get_keys, fast_api_client, fast_api_app
    ):
        """Test successful retrieval of all API keys returns 200 with a list."""
        # Arrange
        now = datetime.now(timezone.utc)
        mock_key = MagicMock(spec=users_api_keys_models.UsersApiKeys)
        mock_key.id = "some-uuid"
        mock_key.user_id = 1
        mock_key.name = "FitoTrack"
        mock_key.key_prefix = "abcdefgh"
        mock_key.scopes = '["activities:upload"]'
        mock_key.expires_at = None
        mock_key.last_used_at = None
        mock_key.created_at = now
        mock_key.is_active = True
        mock_get_keys.return_value = [mock_key]

        # Act
        response = fast_api_client.get(
            "/api_keys",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @patch("users.users_api_keys.router.users_api_keys_crud.get_api_keys_by_user_id")
    def test_get_user_api_keys_empty(
        self, mock_get_keys, fast_api_client, fast_api_app
    ):
        """Test that an empty list is returned when the user has no API keys."""
        # Arrange
        mock_get_keys.return_value = []

        # Act
        response = fast_api_client.get(
            "/api_keys",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 200
        assert response.json() == []


class TestCreateUserApiKey:
    """
    Test suite for POST /api_keys endpoint.
    """

    @patch("users.users_api_keys.router.users_api_keys_crud.create_api_key")
    @patch("users.users_api_keys.router.users_api_keys_utils.validate_api_key_scopes")
    @patch("users.users_api_keys.router.users_crud.get_user_by_id")
    def test_create_user_api_key_success(
        self,
        mock_get_user,
        mock_validate_scopes,
        mock_create,
        fast_api_client,
        fast_api_app,
    ):
        """Test successful API key creation returns 201 with the key in the response."""
        # Arrange
        now = datetime.now(timezone.utc)
        mock_user = MagicMock()
        mock_user.access_type = "regular"
        mock_get_user.return_value = mock_user

        mock_validate_scopes.return_value = None

        mock_orm_key = MagicMock(spec=users_api_keys_models.UsersApiKeys)
        mock_orm_key.id = "new-uuid"
        mock_orm_key.user_id = 1
        mock_orm_key.name = "FitoTrack"
        mock_orm_key.key_prefix = "abcdefgh"
        mock_orm_key.scopes = '["activities:upload"]'
        mock_orm_key.expires_at = None
        mock_orm_key.last_used_at = None
        mock_orm_key.created_at = now
        mock_orm_key.is_active = True
        mock_create.return_value = (mock_orm_key, "endurain_rawsecretkey")

        payload = {
            "name": "FitoTrack",
            "scopes": ["activities:upload"],
        }

        # Act
        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "key" in data
        assert data["key"] == "endurain_rawsecretkey"

    @patch("users.users_api_keys.router.users_crud.get_user_by_id")
    def test_create_user_api_key_user_not_found_returns_404(
        self, mock_get_user, fast_api_client, fast_api_app
    ):
        """Test that 404 is returned when the authenticated user is not found."""
        # Arrange
        mock_get_user.return_value = None

        payload = {
            "name": "FitoTrack",
            "scopes": ["activities:upload"],
        }

        # Act
        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 404

    @patch("users.users_api_keys.router.users_api_keys_utils.validate_api_key_scopes")
    @patch("users.users_api_keys.router.users_crud.get_user_by_id")
    def test_create_user_api_key_scope_exceeds_permission_returns_400(
        self, mock_get_user, mock_validate_scopes, fast_api_client, fast_api_app
    ):
        """Test that 400 is returned when requested scopes exceed the user's own permissions."""
        # Arrange
        mock_user = MagicMock()
        mock_user.access_type = "regular"
        mock_get_user.return_value = mock_user
        mock_validate_scopes.side_effect = ValueError(
            "Scopes not permitted for this user: {'users:write'}"
        )

        payload = {
            "name": "FitoTrack",
            "scopes": ["activities:upload"],
        }

        # Act
        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 400

    def test_create_user_api_key_invalid_scope_returns_422(
        self, fast_api_client, fast_api_app
    ):
        """Test that 422 is returned for an unknown scope (Pydantic validation failure)."""
        # Arrange — schema validator rejects unknown scopes before the endpoint runs
        payload = {
            "name": "FitoTrack",
            "scopes": ["fake:scope_that_does_not_exist"],
        }

        # Act
        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 422

    def test_create_user_api_key_empty_name_returns_422(
        self, fast_api_client, fast_api_app
    ):
        """Test that 422 is returned when the name is empty (min_length violation)."""
        payload = {
            "name": "",
            "scopes": ["activities:upload"],
        }

        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 422

    def test_create_user_api_key_empty_scopes_returns_422(
        self, fast_api_client, fast_api_app
    ):
        """Test that 422 is returned when the scopes list is empty."""
        payload = {
            "name": "FitoTrack",
            "scopes": [],
        }

        response = fast_api_client.post(
            "/api_keys",
            json=payload,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert response.status_code == 422


class TestRevokeUserApiKey:
    """
    Test suite for PATCH /api_keys/{api_key_id}/revoke endpoint.
    """

    @patch("users.users_api_keys.router.users_api_keys_crud.revoke_api_key")
    def test_revoke_user_api_key_success(
        self, mock_revoke, fast_api_client, fast_api_app
    ):
        """Test successful key revocation returns 204 No Content."""
        # Arrange
        mock_revoke.return_value = None

        # Act
        response = fast_api_client.patch(
            "/api_keys/some-uuid/revoke",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 204

    @patch("users.users_api_keys.router.users_api_keys_crud.revoke_api_key")
    def test_revoke_user_api_key_not_found_returns_404(
        self, mock_revoke, fast_api_client, fast_api_app
    ):
        """Test that 404 is returned when the key is not found or belongs to another user."""
        # Arrange
        mock_revoke.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found for user",
        )

        # Act
        response = fast_api_client.patch(
            "/api_keys/nonexistent-uuid/revoke",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 404


class TestDeleteUserApiKey:
    """
    Test suite for DELETE /api_keys/{api_key_id} endpoint.
    """

    @patch("users.users_api_keys.router.users_api_keys_crud.delete_api_key")
    def test_delete_user_api_key_success(
        self, mock_delete, fast_api_client, fast_api_app
    ):
        """Test successful key deletion returns 204 No Content."""
        # Arrange
        mock_delete.return_value = None

        # Act
        response = fast_api_client.delete(
            "/api_keys/some-uuid",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 204

    @patch("users.users_api_keys.router.users_api_keys_crud.delete_api_key")
    def test_delete_user_api_key_not_found_returns_404(
        self, mock_delete, fast_api_client, fast_api_app
    ):
        """Test that 404 is returned when the key does not exist."""
        # Arrange
        mock_delete.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found for user",
        )

        # Act
        response = fast_api_client.delete(
            "/api_keys/nonexistent-uuid",
            headers={"Authorization": "Bearer mock_token"},
        )

        # Assert
        assert response.status_code == 404
