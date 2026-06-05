"""Tests for users.users.utils module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session


class TestGetUserByIdOr404:
    """get_user_by_id_or_404: retrieve user or raise 404."""

    def test_returns_user_when_found(self):
        from users.users.utils import get_user_by_id_or_404

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()

        with patch("users.users.crud.get_user_by_id", return_value=mock_user):
            result = get_user_by_id_or_404(1, mock_db)

        assert result == mock_user

    def test_raises_404_when_user_is_none(self):
        from users.users.utils import get_user_by_id_or_404

        mock_db = MagicMock(spec=Session)

        with patch("users.users.crud.get_user_by_id", return_value=None), pytest.raises(HTTPException) as exc:
            get_user_by_id_or_404(1, mock_db)

        assert exc.value.status_code == 404


class TestGetAdminUsersOr404:
    """get_admin_users_or_404: retrieve admin users or raise 404."""

    def test_returns_admins_when_found(self):
        from users.users.utils import get_admin_users_or_404

        mock_db = MagicMock(spec=Session)
        mock_admin = MagicMock()

        with patch("users.users.crud.get_users_admin", return_value=[mock_admin]):
            result = get_admin_users_or_404(mock_db)

        assert result == [mock_admin]

    def test_raises_404_when_empty(self):
        from users.users.utils import get_admin_users_or_404

        mock_db = MagicMock(spec=Session)

        with patch("users.users.crud.get_users_admin", return_value=[]), pytest.raises(HTTPException) as exc:
            get_admin_users_or_404(mock_db)

        assert exc.value.status_code == 404


class TestCheckPasswordAndHash:
    """check_password_and_hash: validate and hash password."""

    def test_admin_user_uses_admin_min_length(self):
        from users.users.utils import check_password_and_hash

        mock_identity = MagicMock()
        mock_identity.validate_and_hash_password.return_value = "hashed_admin_pw"
        mock_settings = MagicMock()
        mock_settings.password_length_admin_users = 12
        mock_settings.password_type = "strict"

        result = check_password_and_hash("AdminPass1", mock_identity, mock_settings, "admin")

        assert result == "hashed_admin_pw"
        mock_identity.validate_and_hash_password.assert_called_once_with("AdminPass1", 12, "strict")

    def test_regular_user_uses_regular_min_length(self):
        from users.users.utils import check_password_and_hash

        mock_identity = MagicMock()
        mock_identity.validate_and_hash_password.return_value = "hashed_regular_pw"
        mock_settings = MagicMock()
        mock_settings.password_length_regular_users = 8
        mock_settings.password_type = "strict"

        result = check_password_and_hash("RegularPass1", mock_identity, mock_settings, "regular")

        assert result == "hashed_regular_pw"
        mock_identity.validate_and_hash_password.assert_called_once_with("RegularPass1", 8, "strict")


class TestCheckUserIsActive:
    """check_user_is_active: verify user is active."""

    def test_active_user_passes(self):
        from users.users.utils import check_user_is_active

        mock_user = MagicMock()
        mock_user.active = True

        check_user_is_active(mock_user)

    def test_inactive_user_raises_403(self):
        from users.users.utils import check_user_is_active

        mock_user = MagicMock()
        mock_user.active = False

        with pytest.raises(HTTPException) as exc:
            check_user_is_active(mock_user)

        assert exc.value.status_code == 403


class TestCreateUserDefaultData:
    """create_user_default_data: create default data for new user."""

    def test_calls_all_five_crud_functions(self):
        from users.users.utils import create_user_default_data

        mock_db = MagicMock(spec=Session)

        with (
            patch("users.users_integrations.crud.create_user_integrations") as mock_integrations,
            patch("users.users_privacy_settings.crud.create_user_privacy_settings") as mock_privacy,
            patch("health.health_targets.crud.create_health_targets") as mock_targets,
            patch("users.users_default_gear.crud.create_user_default_gear") as mock_gear,
            patch("auth.mfa.crud.create_users_mfa_row") as mock_mfa,
        ):
            create_user_default_data(1, mock_db)

        mock_integrations.assert_called_once_with(1, mock_db)
        mock_privacy.assert_called_once_with(1, mock_db)
        mock_targets.assert_called_once_with(1, mock_db)
        mock_gear.assert_called_once_with(1, mock_db)
        mock_mfa.assert_called_once_with(1, mock_db)


class TestSaveUserImageFile:
    """save_user_image_file: validate and save user image."""

    @pytest.mark.asyncio
    async def test_raises_400_when_filename_is_none(self):
        from users.users.utils import save_user_image_file

        mock_file = MagicMock()
        mock_file.filename = None
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc:
            await save_user_image_file(1, mock_file, mock_db)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_filename_empty(self):
        from users.users.utils import save_user_image_file

        mock_file = MagicMock()
        mock_file.filename = ""
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc:
            await save_user_image_file(1, mock_file, mock_db)

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_415_for_unsupported_extension(self):
        from users.users.utils import save_user_image_file

        mock_file = MagicMock()
        mock_file.filename = "avatar.txt"
        mock_db = MagicMock(spec=Session)

        with pytest.raises(HTTPException) as exc:
            await save_user_image_file(1, mock_file, mock_db)

        assert exc.value.status_code == 415

    @pytest.mark.asyncio
    async def test_success_saves_file_and_updates_db(self):
        from users.users.utils import save_user_image_file

        mock_file = MagicMock()
        mock_file.filename = "avatar.png"
        mock_db = MagicMock(spec=Session)

        with (
            patch("core.file_uploads.save_validated_upload", new_callable=AsyncMock),
            patch(
                "users.users.crud.update_user_photo",
                new_callable=AsyncMock,
                return_value="/path/to/user_images/1.png",
            ),
        ):
            result = await save_user_image_file(1, mock_file, mock_db)

        assert result == "/path/to/user_images/1.png"


class TestDeleteUserPhotoFilesystem:
    """delete_user_photo_filesystem: delete user photo files."""

    @pytest.mark.asyncio
    async def test_calls_delete_files_by_pattern(self):
        from users.users.utils import delete_user_photo_filesystem

        with patch(
            "core.file_uploads.delete_files_by_pattern",
            new_callable=AsyncMock,
        ) as mock_delete:
            await delete_user_photo_filesystem(42)

        mock_delete.assert_called_once()
        args, _ = mock_delete.call_args
        assert args[1] == "42.*"


class TestVerifyStepUpCredentials:
    """verify_step_up_credentials: step-up verification for sensitive operations."""

    def test_no_local_password_no_mfa_success(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = None
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=False),
        ):
            verify_step_up_credentials(1, None, None, mock_identity, mock_db)

    def test_no_local_password_mfa_missing_code_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = None
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, None, None, mock_identity, mock_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == "MFA code required for this operation"

    def test_no_local_password_mfa_wrong_code_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = None
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            patch("profile.utils.verify_user_mfa", return_value=False),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, None, "wrong_code", mock_identity, mock_db)

        assert exc.value.status_code == 401

    def test_no_local_password_mfa_correct_code_success(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = None
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            patch("profile.utils.verify_user_mfa", return_value=True),
        ):
            verify_step_up_credentials(1, None, "123456", mock_identity, mock_db)

    def test_local_password_missing_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, None, None, mock_identity, mock_db)

        assert exc.value.status_code == 401

    def test_local_password_wrong_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()
        mock_identity.verify_password.return_value = False

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, "wrong_pw", None, mock_identity, mock_db)

        assert exc.value.status_code == 401

    def test_local_password_correct_no_mfa_success(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()
        mock_identity.verify_password.return_value = True

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=False),
        ):
            verify_step_up_credentials(1, "correct_pw", None, mock_identity, mock_db)

    def test_local_password_correct_mfa_missing_code_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()
        mock_identity.verify_password.return_value = True

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, "correct_pw", None, mock_identity, mock_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == "MFA code required for this operation"

    def test_local_password_correct_mfa_correct_code_success(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()
        mock_identity.verify_password.return_value = True

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            patch("profile.utils.verify_user_mfa", return_value=True),
        ):
            verify_step_up_credentials(1, "correct_pw", "123456", mock_identity, mock_db)

    def test_local_password_correct_mfa_wrong_code_raises_401(self):
        from users.users.utils import verify_step_up_credentials

        mock_user = MagicMock()
        mock_user.password = "hashed_pw"
        mock_db = MagicMock(spec=Session)
        mock_identity = MagicMock()
        mock_identity.verify_password.return_value = True

        with (
            patch("users.users.utils.get_user_by_id_or_404", return_value=mock_user),
            patch("profile.utils.is_mfa_enabled_for_user", return_value=True),
            patch("profile.utils.verify_user_mfa", return_value=False),
            pytest.raises(HTTPException) as exc,
        ):
            verify_step_up_credentials(1, "correct_pw", "wrong_code", mock_identity, mock_db)

        assert exc.value.status_code == 401
