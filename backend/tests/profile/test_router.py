"""Comprehensive tests for profile.router endpoints."""

import profile.exceptions as profile_exceptions
import profile.schema as profile_schema
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import core.config as core_config

PREFIX = core_config.ROOT_PATH + "/profile"  # /api/v1/profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user_mock(pw_hash: str | None = "hashed_pw") -> MagicMock:
    user = MagicMock()
    user.id = 1
    user.name = "Test User"
    user.username = "testuser"
    user.email = "test@example.com"
    user.city = None
    user.birthdate = None
    user.preferred_language = "us"
    user.gender = "unspecified"
    user.units = "metric"
    user.height = None
    user.max_heart_rate = None
    user.first_day_of_week = "monday"
    user.currency = "euro"
    user.access_type = "regular"
    user.photo_path = None
    user.active = True
    user.mfa_enabled = False
    user.email_verified = True
    user.pending_admin_approval = False
    user.password = pw_hash
    user.external_auth_count = 0
    user.is_strava_linked = 0
    user.is_garminconnect_linked = 0
    user.default_activity_visibility = "public"
    user.hide_activity_start_time = False
    user.hide_activity_location = False
    user.hide_activity_map = False
    user.hide_activity_hr = False
    user.hide_activity_power = False
    user.hide_activity_cadence = False
    user.hide_activity_elevation = False
    user.hide_activity_speed = False
    user.hide_activity_pace = False
    user.hide_activity_laps = False
    user.hide_activity_workout_sets_steps = False
    user.hide_activity_gear = False
    user.has_local_password = False
    return user


def _make_integration_mock() -> MagicMock:
    integ = MagicMock()
    integ.strava_token = None
    integ.garminconnect_token = None
    return integ


def _make_privacy_mock() -> MagicMock:
    p = MagicMock()
    p.default_activity_visibility = "public"
    p.hide_activity_start_time = False
    p.hide_activity_location = False
    p.hide_activity_map = False
    p.hide_activity_hr = False
    p.hide_activity_power = False
    p.hide_activity_cadence = False
    p.hide_activity_elevation = False
    p.hide_activity_speed = False
    p.hide_activity_pace = False
    p.hide_activity_laps = False
    p.hide_activity_workout_sets_steps = False
    p.hide_activity_gear = False
    return p


def _make_session_mock(session_id: str = "session-1") -> MagicMock:
    s = MagicMock()
    s.id = session_id
    s.ip_address = "127.0.0.1"
    s.device_type = "web"
    s.operating_system = "Linux"
    s.operating_system_version = "6.0"
    s.browser = "Firefox"
    s.browser_version = "120.0"
    s.created_at = datetime.now(UTC)
    s.last_activity_at = datetime.now(UTC)
    s.expires_at = datetime.now(UTC)
    s.user_id = 1
    return s


def _make_idp_mock(idp_id: int = 1) -> MagicMock:
    idp = MagicMock()
    idp.id = idp_id
    idp.name = "TestIdP"
    idp.slug = "testidp"
    idp.icon = "icon.png"
    idp.provider_type = "oauth2"
    idp.enabled = True
    return idp


# ===================================================================
# GET /profile
# ===================================================================


class TestReadUsersMe:
    """Tests for GET /profile — read_users_me."""

    @patch("profile.router.users_privacy_settings_crud.get_user_privacy_settings_by_user_id")
    @patch("profile.router.user_integrations_crud.get_user_integrations_by_user_id")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_success(
        self,
        mock_get_user,
        mock_get_integrations,
        mock_get_privacy,
        profile_client,
    ):
        """Happy path: all data found."""
        mock_get_user.return_value = _make_user_mock()
        mock_get_integrations.return_value = _make_integration_mock()
        mock_get_privacy.return_value = _make_privacy_mock()

        response = profile_client.get(PREFIX)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test User"
        assert data["is_strava_linked"] == 0
        assert data["has_local_password"] is True

    @patch("profile.router.users_privacy_settings_crud.get_user_privacy_settings_by_user_id")
    @patch("profile.router.user_integrations_crud.get_user_integrations_by_user_id")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_user_not_found(
        self,
        mock_get_user,
        mock_get_integrations,
        mock_get_privacy,
        profile_client,
    ):
        """Error: user not found → 404."""
        mock_get_user.return_value = None

        response = profile_client.get(PREFIX)

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @patch("profile.router.users_privacy_settings_crud.get_user_privacy_settings_by_user_id")
    @patch("profile.router.user_integrations_crud.get_user_integrations_by_user_id")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_integrations_not_found(
        self,
        mock_get_user,
        mock_get_integrations,
        mock_get_privacy,
        profile_client,
    ):
        """Error: integrations not found → 404."""
        mock_get_user.return_value = _make_user_mock()
        mock_get_integrations.return_value = None

        response = profile_client.get(PREFIX)

        assert response.status_code == 404
        assert response.json()["detail"] == "Could not validate credentials (user integrations not found)"

    @patch("profile.router.users_privacy_settings_crud.get_user_privacy_settings_by_user_id")
    @patch("profile.router.user_integrations_crud.get_user_integrations_by_user_id")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_privacy_not_found(
        self,
        mock_get_user,
        mock_get_integrations,
        mock_get_privacy,
        profile_client,
    ):
        """Error: privacy settings not found → 404."""
        mock_get_user.return_value = _make_user_mock()
        mock_get_integrations.return_value = _make_integration_mock()
        mock_get_privacy.return_value = None

        response = profile_client.get(PREFIX)

        assert response.status_code == 404
        assert "privacy settings" in response.json()["detail"]


# ===================================================================
# GET /profile/sessions
# ===================================================================


class TestReadSessionsMe:
    """Tests for GET /profile/sessions — read_sessions_me."""

    @patch("profile.router.core_config")
    @patch("profile.router.users_session_crud.get_user_sessions")
    def test_success(self, mock_get_sessions, mock_config, profile_client):
        """Happy path: returns sessions."""
        mock_config.settings.ENVIRONMENT = "production"
        mock_get_sessions.return_value = [_make_session_mock()]

        response = profile_client.get(PREFIX + "/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "session-1"

    @patch("profile.router.core_config")
    @patch("profile.router.users_session_crud.get_user_sessions")
    def test_demo_environment(self, mock_get_sessions, mock_config, profile_client):
        """Demo environment returns empty list."""
        mock_config.settings.ENVIRONMENT = "demo"
        mock_get_sessions.return_value = [_make_session_mock()]

        response = profile_client.get(PREFIX + "/sessions")

        assert response.status_code == 200
        assert response.json() == []


# ===================================================================
# POST /profile/idp/{idp_id}/link/token
# ===================================================================


class TestGenerateLinkToken:
    """Tests for POST /profile/idp/{idp_id}/link/token — generate_link_token."""

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_success(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Happy path: generates a link token."""
        mock_get_idp.return_value = _make_idp_mock()
        mock_get_link.return_value = None
        mock_gen_token.return_value = {"token": "tok-1", "expires_at": datetime(2025, 1, 1, tzinfo=UTC)}

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 201
        assert response.json()["token"] == "tok-1"

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_step_up_fails(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Error: step-up verification fails."""
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid credentials")

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "wrong"},
        )

        assert response.status_code == 401

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_idp_not_found(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Error: IDP not found → 404."""
        mock_get_idp.return_value = None

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_idp_disabled(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Error: IDP disabled → 404."""
        idp = _make_idp_mock()
        idp.enabled = False
        mock_get_idp.return_value = idp

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_already_linked(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Error: already linked → 409."""
        mock_get_idp.return_value = _make_idp_mock()
        mock_get_link.return_value = MagicMock()

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 409
        assert "already linked" in response.json()["detail"]

    @patch("profile.router.idp_link_token_utils.generate_idp_link_token")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_idp_not_found_none_return(
        self,
        mock_verify,
        mock_get_idp,
        mock_get_link,
        mock_gen_token,
        profile_client,
    ):
        """Error: IDP get returns None (second branch)."""
        mock_get_idp.return_value = None

        response = profile_client.post(
            PREFIX + "/idp/1/link/token",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404


# ===================================================================
# POST /profile/image
# ===================================================================


class TestUploadProfileImage:
    """Tests for POST /profile/image — upload_profile_image."""

    @patch("profile.router.users_utils.save_user_image_file", new_callable=AsyncMock)
    def test_success(self, mock_save, profile_client):
        """Happy path: upload profile image."""
        mock_save.return_value = "photo.jpg"

        response = profile_client.post(
            PREFIX + "/image",
            files={"file": ("photo.jpg", b"image-data", "image/jpeg")},
        )

        assert response.status_code == 201
        assert response.json() == "photo.jpg"


# ===================================================================
# PUT /profile
# ===================================================================


class TestEditUser:
    """Tests for PUT /profile — edit_user."""

    @patch("profile.router.users_crud.edit_profile_user", new_callable=AsyncMock)
    def test_success(self, mock_edit, profile_client):
        """Happy path: update profile."""
        response = profile_client.put(
            PREFIX,
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert "updated successfully" in response.json()["message"]


# ===================================================================
# PUT /profile/privacy
# ===================================================================


class TestEditProfilePrivacySettings:
    """Tests for PUT /profile/privacy — edit_profile_privacy_settings."""

    @patch("profile.router.users_privacy_settings_crud.edit_user_privacy_settings")
    def test_success(self, mock_edit, profile_client):
        """Happy path: update privacy settings."""
        response = profile_client.put(
            PREFIX + "/privacy",
            json={"default_activity_visibility": "followers"},
        )

        assert response.status_code == 200
        assert "privacy settings updated" in response.json()["message"]


# ===================================================================
# PUT /profile/password
# ===================================================================


class TestEditProfilePassword:
    """Tests for PUT /profile/password — edit_profile_password."""

    @patch("profile.router.auth_security_stores.clear_pending_mfa_for_user")
    @patch("profile.router.users_crud.edit_user_password")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_success(
        self,
        mock_verify,
        mock_edit_password,
        mock_clear_mfa,
        profile_client,
    ):
        """Happy path: update password."""
        response = profile_client.put(
            PREFIX + "/password",
            json={
                "current_password": "oldpass",
                "password": "NewPass123!",
                "mfa_code": None,
            },
        )

        assert response.status_code == 200
        assert "password updated successfully" in response.json()["message"]

    @patch("profile.router.auth_security_stores.clear_pending_mfa_for_user")
    @patch("profile.router.users_crud.edit_user_password")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_step_up_fails(
        self,
        mock_verify,
        mock_edit_password,
        mock_clear_mfa,
        profile_client,
    ):
        """Error: step-up verification fails."""
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid credentials")

        response = profile_client.put(
            PREFIX + "/password",
            json={
                "current_password": "wrong",
                "password": "NewPass123!",
                "mfa_code": None,
            },
        )

        assert response.status_code == 401


# ===================================================================
# PUT /profile/photo
# ===================================================================


class TestDeleteProfilePhoto:
    """Tests for PUT /profile/photo — delete_profile_photo."""

    @patch("profile.router.users_crud.update_user_photo", new_callable=AsyncMock)
    def test_success(self, mock_update, profile_client):
        """Happy path: delete profile photo."""
        mock_update.return_value = None

        response = profile_client.put(PREFIX + "/photo")

        assert response.status_code == 204


# ===================================================================
# DELETE /profile/sessions/{session_id}
# ===================================================================


class TestDeleteProfileSession:
    """Tests for DELETE /profile/sessions/{session_id} — delete_profile_session."""

    @patch("profile.router.users_session_crud.delete_session")
    def test_success(self, mock_delete, profile_client):
        """Happy path: delete session."""
        response = profile_client.delete(PREFIX + "/sessions/session-1")

        assert response.status_code == 204


# ===================================================================
# GET /profile/export
# ===================================================================


class TestExportProfileData:
    """Tests for GET /profile/export — export_profile_data."""

    @patch("profile.router.profile_export_service.ExportService")
    @patch("profile.router.profile_utils.sqlalchemy_obj_to_dict")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_success(
        self,
        mock_get_user,
        mock_to_dict,
        mock_export_service,
        profile_client,
    ):
        """Happy path: returns streaming ZIP."""
        mock_get_user.return_value = _make_user_mock()
        mock_to_dict.return_value = {"name": "Test", "password": "secret"}
        mock_instance = mock_export_service.return_value
        mock_instance.generate_export_archive.return_value = iter([b"zip-data"])

        response = profile_client.get(PREFIX + "/export")

        assert response.status_code == 200
        assert response.content == b"zip-data"

    @patch("profile.router.profile_export_service.ExportService")
    @patch("profile.router.profile_utils.sqlalchemy_obj_to_dict")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_user_not_found(
        self,
        mock_get_user,
        mock_to_dict,
        mock_export_service,
        profile_client,
    ):
        """Error: user not found → 404."""
        mock_get_user.return_value = None

        response = profile_client.get(PREFIX + "/export")

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    @patch("profile.router.profile_export_service.ExportService")
    @patch("profile.router.profile_utils.sqlalchemy_obj_to_dict")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_sensitive_fields_stripped(
        self,
        mock_get_user,
        mock_to_dict,
        mock_export_service,
        profile_client,
    ):
        """Verify sensitive fields are stripped from export dict."""
        mock_get_user.return_value = _make_user_mock()
        mock_to_dict.return_value = {
            "name": "Test",
            "password": "secret",
            "mfa_secret": "sec",
            "access_type": "admin",
        }
        mock_instance = mock_export_service.return_value
        mock_instance.generate_export_archive.return_value = iter([b"data"])

        response = profile_client.get(PREFIX + "/export")

        assert response.status_code == 200
        # Verify sensitive fields were popped before passing to service
        passed_dict = mock_instance.generate_export_archive.call_args[0][0]
        assert "password" not in passed_dict
        assert "mfa_secret" not in passed_dict
        assert "access_type" not in passed_dict
        assert passed_dict["name"] == "Test"

    @pytest.mark.parametrize(
        "exception_cls,expected_status",
        [
            (profile_exceptions.DatabaseConnectionError, 503),
            (profile_exceptions.FileSystemError, 507),
            (profile_exceptions.ZipCreationError, 422),
            (profile_exceptions.MemoryAllocationError, 507),
            (profile_exceptions.DataCollectionError, 422),
            (profile_exceptions.ExportTimeoutError, 408),
        ],
    )
    @patch("profile.router.profile_export_service.ExportService")
    @patch("profile.router.profile_utils.sqlalchemy_obj_to_dict")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_export_exceptions(
        self,
        mock_get_user,
        mock_to_dict,
        mock_export_service,
        exception_cls,
        expected_status,
        profile_client,
    ):
        """Each export exception is translated to the correct HTTP error via handle_import_export_exception."""
        mock_get_user.return_value = _make_user_mock()
        mock_to_dict.return_value = {"name": "Test"}
        mock_instance = mock_export_service.return_value
        mock_instance.generate_export_archive.side_effect = exception_cls("test error")

        response = profile_client.get(PREFIX + "/export")

        assert response.status_code == expected_status

    @patch("profile.router.profile_export_service.ExportService")
    @patch("profile.router.profile_utils.sqlalchemy_obj_to_dict")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_unexpected_exception(
        self,
        mock_get_user,
        mock_to_dict,
        mock_export_service,
        profile_client,
    ):
        """Unexpected exception → 500."""
        mock_get_user.return_value = _make_user_mock()
        mock_to_dict.return_value = {"name": "Test"}
        mock_instance = mock_export_service.return_value
        mock_instance.generate_export_archive.side_effect = RuntimeError("unexpected")

        response = profile_client.get(PREFIX + "/export")

        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"


# ===================================================================
# POST /profile/import
# ===================================================================


class TestImportProfileData:
    """Tests for POST /profile/import — import_profile_data."""

    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_success(
        self,
        mock_validate,
        mock_import_service,
        profile_client,
    ):
        """Happy path: import ZIP data."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(
            return_value={
                "imported": {"activities": 5},
            }
        )

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"zip-data", "application/zip")},
        )

        assert response.status_code == 201
        assert response.json()["imported"]["activities"] == 5

    @pytest.mark.parametrize(
        "exc,expected_status",
        [
            (profile_exceptions.ImportValidationError("test"), 400),
            (profile_exceptions.FileFormatError("test"), 400),
            (profile_exceptions.FileSizeError("test"), 413),
            (profile_exceptions.ActivityLimitError("test"), 413),
            (profile_exceptions.ZipStructureError("test"), 400),
            (profile_exceptions.JSONParseError("test"), 400),
            (profile_exceptions.SchemaValidationError("test"), 400),
        ],
    )
    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_import_validation_exceptions(
        self,
        mock_validate,
        mock_import_service,
        exc,
        expected_status,
        profile_client,
    ):
        """Import validation errors mapped to correct HTTP status."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=exc)

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "exc,expected_status",
        [
            (profile_exceptions.DataIntegrityError("test"), 422),
            (profile_exceptions.ImportTimeoutError("test"), 408),
            (profile_exceptions.DiskSpaceError("test"), 507),
        ],
    )
    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_import_operation_exceptions(
        self,
        mock_validate,
        mock_import_service,
        exc,
        expected_status,
        profile_client,
    ):
        """Import operation errors mapped to correct HTTP status."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=exc)

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == expected_status

    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_value_error(
        self,
        mock_validate,
        mock_import_service,
        profile_client,
    ):
        """ValueError → 400."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=ValueError("bad data"))

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "exc,expected_status",
        [
            (profile_exceptions.MemoryAllocationError("test"), 507),
            (MemoryError("test"), 500),
        ],
    )
    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_memory_errors(
        self,
        mock_validate,
        mock_import_service,
        exc,
        expected_status,
        profile_client,
    ):
        """Memory errors mapped to correct HTTP status."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=exc)

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "exc,expected_status",
        [
            (profile_exceptions.DatabaseConnectionError("test"), 503),
            (profile_exceptions.FileSystemError("test"), 507),
            (profile_exceptions.ZipCreationError("test"), 422),
            (profile_exceptions.DataCollectionError("test"), 422),
            (profile_exceptions.ExportTimeoutError("test"), 408),
        ],
    )
    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_import_system_errors(
        self,
        mock_validate,
        mock_import_service,
        exc,
        expected_status,
        profile_client,
    ):
        """Import system errors (overlap with export) → mapped status."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=exc)

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == expected_status

    @patch("profile.router.profile_import_service.ImportService")
    @patch("profile.router.core_file_uploads.validate_upload", new_callable=AsyncMock)
    def test_unexpected_exception(
        self,
        mock_validate,
        mock_import_service,
        profile_client,
    ):
        """Unexpected exception → 500."""
        mock_validate.return_value = None
        mock_instance = mock_import_service.return_value
        mock_instance.import_from_zip_data = AsyncMock(side_effect=RuntimeError("boom"))

        response = profile_client.post(
            PREFIX + "/import",
            files={"file": ("test.zip", b"data", "application/zip")},
        )

        assert response.status_code == 500
        assert "Import failed" in response.json()["detail"]


# ===================================================================
# GET /profile/mfa/status
# ===================================================================


class TestGetMFAStatus:
    """Tests for GET /profile/mfa/status — get_mfa_status."""

    @patch("profile.router.profile_utils.is_mfa_enabled_for_user")
    def test_enabled(self, mock_is_enabled, profile_client):
        """Returns enabled=True."""
        mock_is_enabled.return_value = True

        response = profile_client.get(PREFIX + "/mfa/status")

        assert response.status_code == 200
        assert response.json()["mfa_enabled"] is True

    @patch("profile.router.profile_utils.is_mfa_enabled_for_user")
    def test_disabled(self, mock_is_enabled, profile_client):
        """Returns enabled=False."""
        mock_is_enabled.return_value = False

        response = profile_client.get(PREFIX + "/mfa/status")

        assert response.status_code == 200
        assert response.json()["mfa_enabled"] is False


# ===================================================================
# GET /profile/mfa/backup-codes/status
# ===================================================================


class TestGetBackupCodeStatus:
    """Tests for GET /profile/mfa/backup-codes/status — get_backup_code_status."""

    @patch("profile.router.mfa_backup_codes_crud.get_user_backup_codes")
    def test_no_codes(self, mock_get_codes, profile_client):
        """No backup codes → has_codes=False."""
        mock_get_codes.return_value = []

        response = profile_client.get(PREFIX + "/mfa/backup-codes/status")

        assert response.status_code == 200
        data = response.json()
        assert data["has_codes"] is False
        assert data["total"] == 0

    @patch("profile.router.mfa_backup_codes_crud.get_user_backup_codes")
    def test_has_codes(self, mock_get_codes, profile_client):
        """Has backup codes with usage counts."""
        code1 = MagicMock()
        code1.used = False
        code2 = MagicMock()
        code2.used = True
        code2.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        code1.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        mock_get_codes.return_value = [code1, code2]

        response = profile_client.get(PREFIX + "/mfa/backup-codes/status")

        assert response.status_code == 200
        data = response.json()
        assert data["has_codes"] is True
        assert data["total"] == 2
        assert data["unused"] == 1
        assert data["used"] == 1


# ===================================================================
# POST /profile/mfa/setup
# ===================================================================


class TestSetupMFA:
    """Tests for POST /profile/mfa/setup — setup_mfa."""

    @patch("profile.router.profile_utils.setup_user_mfa")
    def test_success(self, mock_setup, profile_client, fake_mfa_secret_store):
        """Happy path: create MFA setup."""
        mock_setup.return_value = profile_schema.MFASetupResponse(
            secret="SECRETKEY",
            qr_code="base64qr",
            app_name="Endurain",
        )

        response = profile_client.post(PREFIX + "/mfa/setup")

        assert response.status_code == 201
        data = response.json()
        assert data["secret"] == "SECRETKEY"
        assert data["qr_code"] == "base64qr"
        # Verify secret was stored
        assert fake_mfa_secret_store.get_secret(1) == "SECRETKEY"

    @patch("profile.router.profile_utils.setup_user_mfa")
    def test_store_unavailable(self, mock_setup, profile_client, fake_mfa_secret_store):
        """MFA secret store unavailable → 503."""
        from profile.mfa_store import MFASecretStoreUnavailableError

        mock_setup.return_value = profile_schema.MFASetupResponse(
            secret="SECRETKEY",
            qr_code="base64qr",
            app_name="Endurain",
        )

        def failing_add(user_id, secret):
            raise MFASecretStoreUnavailableError("store down")

        fake_mfa_secret_store.add_secret = failing_add

        response = profile_client.post(PREFIX + "/mfa/setup")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]


# ===================================================================
# PUT /profile/mfa/enable
# ===================================================================


class TestEnableMFA:
    """Tests for PUT /profile/mfa/enable — enable_mfa."""

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_success(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """Happy path: enable MFA."""
        fake_mfa_secret_store.add_secret(1, "SECRETKEY")
        mock_enable.return_value = ["code1", "code2"]

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "123456", "current_password": "pass123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "MFA enabled successfully"
        assert data["backup_codes"] == ["code1", "code2"]
        # Secret should be deleted after success
        assert fake_mfa_secret_store.get_secret(1) is None

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_step_up_fails(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """Step-up fails before any secret operation."""
        fake_mfa_secret_store.add_secret(1, "SECRETKEY")
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid")

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "123456", "current_password": "wrong"},
        )

        assert response.status_code == 401
        # Secret still there (step-up happens first)
        assert fake_mfa_secret_store.get_secret(1) == "SECRETKEY"

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_no_setup_in_progress(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """No setup in progress → 400."""
        # Don't add any secret

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "123456", "current_password": "pass123"},
        )

        assert response.status_code == 400
        assert "No MFA setup in progress" in response.json()["detail"]

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_get_secret_store_unavailable(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """get_secret raises MFASecretStoreUnavailableError → 503."""
        # Patch the fake store's get_secret to raise
        from profile.mfa_store import MFASecretStoreUnavailableError

        def failing_get(uid):
            raise MFASecretStoreUnavailableError("store down")

        fake_mfa_secret_store.get_secret = failing_get

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "123456", "current_password": "pass123"},
        )

        assert response.status_code == 503

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_invalid_mfa_code(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """Invalid MFA code → 400, secret NOT deleted."""
        fake_mfa_secret_store.add_secret(1, "SECRETKEY")
        mock_enable.side_effect = HTTPException(
            status_code=400,
            detail="Invalid MFA code",
        )

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "000000", "current_password": "pass123"},
        )

        assert response.status_code == 400
        # Secret preserved for retry
        assert fake_mfa_secret_store.get_secret(1) == "SECRETKEY"

    @patch("profile.router.profile_utils.enable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_other_http_exception(
        self,
        mock_verify,
        mock_enable,
        profile_client,
        fake_mfa_secret_store,
    ):
        """Other HTTPException (not wrong code) → re-raised, secret deleted."""
        fake_mfa_secret_store.add_secret(1, "SECRETKEY")
        mock_enable.side_effect = HTTPException(
            status_code=409,
            detail="MFA already enabled",
        )

        response = profile_client.put(
            PREFIX + "/mfa/enable",
            json={"mfa_code": "123456", "current_password": "pass123"},
        )

        assert response.status_code == 409
        # Secret deleted for non-wrong-code errors
        assert fake_mfa_secret_store.get_secret(1) is None


# ===================================================================
# PUT /profile/mfa/disable
# ===================================================================


class TestDisableMFA:
    """Tests for PUT /profile/mfa/disable — disable_mfa."""

    @patch("profile.router.profile_utils.disable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_success(self, mock_verify, mock_disable, profile_client):
        """Happy path: disable MFA."""
        response = profile_client.put(
            PREFIX + "/mfa/disable",
            json={"mfa_code": "123456", "current_password": "pass123"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "MFA disabled successfully"

    @patch("profile.router.profile_utils.disable_user_mfa")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_step_up_fails(self, mock_verify, mock_disable, profile_client):
        """Step-up fails before disable."""
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid")

        response = profile_client.put(
            PREFIX + "/mfa/disable",
            json={"mfa_code": "000000", "current_password": "wrong"},
        )

        assert response.status_code == 401


# ===================================================================
# POST /profile/mfa/verify
# ===================================================================


class TestVerifyMFA:
    """Tests for POST /profile/mfa/verify — verify_mfa."""

    @patch("profile.router.profile_utils.verify_user_mfa")
    def test_valid_code(self, mock_verify, profile_client):
        """Valid MFA code → success."""
        mock_verify.return_value = True

        response = profile_client.post(
            PREFIX + "/mfa/verify",
            json={"mfa_code": "123456"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "MFA code verified successfully"

    @patch("profile.router.profile_utils.verify_user_mfa")
    def test_invalid_code(self, mock_verify, profile_client):
        """Invalid MFA code → 400."""
        mock_verify.return_value = False

        response = profile_client.post(
            PREFIX + "/mfa/verify",
            json={"mfa_code": "000000"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid MFA code"


# ===================================================================
# POST /profile/mfa/backup-codes
# ===================================================================


class TestGenerateMFABackupCodes:
    """Tests for POST /profile/mfa/backup-codes — generate_mfa_backup_codes."""

    @patch("profile.router.mfa_backup_codes_crud.create_backup_codes")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_success(
        self,
        mock_get_user,
        mock_verify,
        mock_create,
        profile_client,
    ):
        """Happy path: generate backup codes."""
        user = _make_user_mock()
        user.mfa_enabled = True
        mock_get_user.return_value = user
        mock_create.return_value = ["code1", "code2"]

        response = profile_client.post(
            PREFIX + "/mfa/backup-codes",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["codes"] == ["code1", "code2"]
        assert "created_at" in data

    @patch("profile.router.mfa_backup_codes_crud.create_backup_codes")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_user_not_found(
        self,
        mock_get_user,
        mock_verify,
        mock_create,
        profile_client,
    ):
        """User not found → 404."""
        mock_get_user.return_value = None

        response = profile_client.post(
            PREFIX + "/mfa/backup-codes",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404

    @patch("profile.router.mfa_backup_codes_crud.create_backup_codes")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_mfa_not_enabled(
        self,
        mock_get_user,
        mock_verify,
        mock_create,
        profile_client,
    ):
        """MFA not enabled → 400."""
        user = _make_user_mock()
        user.mfa_enabled = False
        mock_get_user.return_value = user

        response = profile_client.post(
            PREFIX + "/mfa/backup-codes",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 400
        assert "MFA must be enabled" in response.json()["detail"]

    @patch("profile.router.mfa_backup_codes_crud.create_backup_codes")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    @patch("profile.router.users_crud.get_user_by_id")
    def test_step_up_fails(
        self,
        mock_get_user,
        mock_verify,
        mock_create,
        profile_client,
    ):
        """Step-up fails → 401."""
        user = _make_user_mock()
        user.mfa_enabled = True
        mock_get_user.return_value = user
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid")

        response = profile_client.post(
            PREFIX + "/mfa/backup-codes",
            json={"current_password": "wrong"},
        )

        assert response.status_code == 401


# ===================================================================
# GET /profile/idp
# ===================================================================


class TestGetMyIdentityProviders:
    """Tests for GET /profile/idp — get_my_identity_providers."""

    @patch("profile.router.user_idp_utils.enrich_user_identity_providers")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    def test_success(
        self,
        mock_get_links,
        mock_enrich,
        profile_client,
    ):
        """Happy path: returns enriched IdP links."""
        mock_get_links.return_value = [MagicMock()]
        mock_enrich.return_value = [
            {
                "id": 1,
                "user_id": 1,
                "idp_id": 1,
                "idp_subject": "sub",
                "linked_at": "2025-01-01T00:00:00",
                "last_login": None,
                "idp_access_token_expires_at": None,
                "idp_refresh_token_updated_at": None,
                "idp_name": "TestIdP",
                "idp_slug": "testidp",
                "idp_icon": "icon.png",
                "idp_provider_type": "oauth2",
            }
        ]

        response = profile_client.get(PREFIX + "/idp")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["idp_name"] == "TestIdP"

    @patch("profile.router.user_idp_utils.enrich_user_identity_providers")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    def test_no_links(
        self,
        mock_get_links,
        mock_enrich,
        profile_client,
    ):
        """No IdP links → empty list."""
        mock_get_links.return_value = []
        mock_enrich.return_value = []

        response = profile_client.get(PREFIX + "/idp")

        assert response.status_code == 200
        assert response.json() == []


# ===================================================================
# POST /profile/idp/{idp_id}/unlink
# ===================================================================


class TestDeleteMyIdentityProvider:
    """Tests for POST /profile/idp/{idp_id}/unlink — delete_my_identity_provider."""

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_success(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """Happy path: unlink IdP."""
        mock_get_user.return_value = _make_user_mock(pw_hash="hashed")

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 204

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_step_up_fails(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """Step-up fails → 401."""
        mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid")

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "wrong"},
        )

        assert response.status_code == 401

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_idp_not_found(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """IDP not found → 404."""
        mock_get_idp.return_value = None

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_link_not_found(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """Link not found for user → 404."""
        mock_get_idp.return_value = _make_idp_mock()
        mock_get_link.return_value = None

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 404

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_account_lockout(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """Unlinking last auth method → 400."""
        mock_get_user.return_value = _make_user_mock(pw_hash=None)  # SSO-only
        mock_get_idp.return_value = _make_idp_mock()
        mock_get_link.return_value = MagicMock()
        mock_get_all_links.return_value = [MagicMock()]  # only 1 link

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 400
        assert "Cannot unlink" in response.json()["detail"]

    @patch("profile.router.user_idp_crud.delete_user_identity_provider")
    @patch("profile.router.user_idp_crud.get_user_identity_providers_by_user_id")
    @patch("profile.router.user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id")
    @patch("profile.router.idp_crud.get_identity_provider")
    @patch("profile.router.users_crud.get_user_by_id")
    @patch("profile.router.users_utils.verify_step_up_credentials")
    def test_deletion_fails(
        self,
        mock_verify,
        mock_get_user,
        mock_get_idp,
        mock_get_link,
        mock_get_all_links,
        mock_delete,
        profile_client,
    ):
        """Deletion returns False → 500."""
        mock_get_user.return_value = _make_user_mock(pw_hash="hashed")
        mock_get_idp.return_value = _make_idp_mock()
        mock_get_link.return_value = MagicMock()
        mock_get_all_links.return_value = [MagicMock(), MagicMock()]
        mock_delete.return_value = False

        response = profile_client.post(
            PREFIX + "/idp/1/unlink",
            json={"current_password": "pass123"},
        )

        assert response.status_code == 500
        assert "Failed to unlink" in response.json()["detail"]
