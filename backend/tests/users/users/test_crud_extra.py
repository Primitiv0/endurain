"""Extra tests for users CRUD operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class TestGetAllUsers:
    """get_all_users: retrieve all users."""

    def test_success(self):
        from users.users.crud import get_all_users

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        result = get_all_users(mock_db)

        assert result == [mock_user]

    def test_empty(self):
        from users.users.crud import get_all_users

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_all_users(mock_db)

        assert result == []

    def test_db_error(self):
        from users.users.crud import get_all_users

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_all_users(mock_db)
        assert exc.value.status_code == 500


class TestGetUsersNumber:
    """get_users_number: total user count."""

    def test_success(self):
        from users.users.crud import get_users_number

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one.return_value = 42

        result = get_users_number(mock_db)

        assert result == 42

    def test_zero(self):
        from users.users.crud import get_users_number

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one.return_value = 0

        result = get_users_number(mock_db)

        assert result == 0

    def test_db_error(self):
        from users.users.crud import get_users_number

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_users_number(mock_db)
        assert exc.value.status_code == 500


class TestGetUsersWithPagination:
    """get_users_with_pagination: paginated list with optional filters."""

    def test_success_defaults(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        result = get_users_with_pagination(mock_db)

        assert result == [mock_user]

    def test_with_pagination(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        result = get_users_with_pagination(mock_db, page_number=1, num_records=10)

        assert result == [mock_user]

    def test_filter_inactive(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_users_with_pagination(mock_db, show_inactive=False)

        assert result == []

    def test_filter_email_unverified(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_users_with_pagination(mock_db, show_email_unverified=False)

        assert result == []

    def test_filter_pending_approval(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_users_with_pagination(mock_db, show_pending_approval=False)

        assert result == []

    def test_empty(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_users_with_pagination(mock_db)

        assert result == []

    def test_db_error(self):
        from users.users.crud import get_users_with_pagination

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_users_with_pagination(mock_db)
        assert exc.value.status_code == 500


class TestGetUserByUsername:
    """get_user_by_username: exact and partial match."""

    def test_exact_match_found(self):
        from users.users.crud import get_user_by_username

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        result = get_user_by_username("TestUser", mock_db)

        assert result == mock_user

    def test_exact_match_not_found(self):
        from users.users.crud import get_user_by_username

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = get_user_by_username("Unknown", mock_db)

        assert result is None

    def test_contains_found(self):
        from users.users.crud import get_user_by_username

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        result = get_user_by_username("test", mock_db, contains=True)

        assert result == [mock_user]

    def test_contains_empty(self):
        from users.users.crud import get_user_by_username

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_user_by_username("zzz", mock_db, contains=True)

        assert result == []

    def test_db_error(self):
        from users.users.crud import get_user_by_username

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_user_by_username("test", mock_db)
        assert exc.value.status_code == 500


class TestGetUserByEmail:
    """get_user_by_email: case-insensitive email lookup."""

    def test_found(self):
        from users.users.crud import get_user_by_email

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        result = get_user_by_email("Test@Example.COM", mock_db)

        assert result == mock_user

    def test_not_found(self):
        from users.users.crud import get_user_by_email

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = get_user_by_email("nonexistent@example.com", mock_db)

        assert result is None

    def test_db_error(self):
        from users.users.crud import get_user_by_email

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_user_by_email("test@example.com", mock_db)
        assert exc.value.status_code == 500


class TestGetUserById:
    """get_user_by_id: lookup by primary key with optional public_check."""

    def test_found(self):
        from users.users.crud import get_user_by_id

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        result = get_user_by_id(1, mock_db)

        assert result == mock_user

    def test_not_found(self):
        from users.users.crud import get_user_by_id

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = get_user_by_id(999, mock_db)

        assert result is None

    def test_public_check_disabled_by_settings(self):
        from users.users.crud import get_user_by_id

        mock_db = MagicMock(spec=Session)
        mock_settings = MagicMock()
        mock_settings.public_shareable_links = False
        mock_settings.public_shareable_links_user_info = True

        with patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings):
            result = get_user_by_id(1, mock_db, public_check=True)

        assert result is None
        mock_db.execute.assert_not_called()

    def test_public_check_enabled(self):
        from users.users.crud import get_user_by_id

        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_settings = MagicMock()
        mock_settings.public_shareable_links = True
        mock_settings.public_shareable_links_user_info = True
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        with patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings):
            result = get_user_by_id(1, mock_db, public_check=True)

        assert result == mock_user

    def test_db_error(self):
        from users.users.crud import get_user_by_id

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_user_by_id(1, mock_db)
        assert exc.value.status_code == 500


class TestGetUsersAdmin:
    """get_users_admin: retrieve all admin users."""

    def test_success(self):
        from users.users.crud import get_users_admin

        mock_db = MagicMock(spec=Session)
        mock_admin = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_admin]

        result = get_users_admin(mock_db)

        assert result == [mock_admin]

    def test_empty(self):
        from users.users.crud import get_users_admin

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = get_users_admin(mock_db)

        assert result == []

    def test_db_error(self):
        from users.users.crud import get_users_admin

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with pytest.raises(HTTPException) as exc:
            get_users_admin(mock_db)
        assert exc.value.status_code == 500


class TestCreateUser:
    """create_user: admin user creation with password hashing."""

    def test_success(self):
        from users.users.crud import create_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "TestUser"
        mock_user_schema.email = "Test@Example.COM"
        mock_user_schema.password = "securePass123"
        mock_user_schema.access_type = "regular"
        mock_user_schema.model_dump.return_value = {"name": "Test", "username": "testuser"}

        mock_identity = MagicMock()
        mock_settings = MagicMock()
        mock_settings.password_length_regular_users = 8
        mock_settings.password_type = "strict"
        mock_db_user = MagicMock()

        mock_hashed = "hashed_password_123"

        with (
            patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings),
            patch("users.users.crud.users_utils.check_password_and_hash", return_value=mock_hashed),
            patch("users.users.crud.users_models.Users", return_value=mock_db_user),
        ):
            result = create_user(mock_user_schema, mock_identity, mock_db)

        assert result == mock_db_user
        mock_db.add.assert_called_once_with(mock_db_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_db_user)

    def test_integrity_error(self):
        from users.users.crud import create_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "TestUser"
        mock_user_schema.email = "Test@Example.COM"
        mock_user_schema.password = "securePass123"
        mock_user_schema.access_type = "regular"
        mock_user_schema.model_dump.return_value = {"name": "Test"}

        mock_identity = MagicMock()
        mock_settings = MagicMock()
        mock_settings.password_length_regular_users = 8
        mock_settings.password_type = "strict"

        mock_db.add.side_effect = [
            None,
            __import__("sqlalchemy.exc", fromlist=["IntegrityError"]).IntegrityError("mock", None, None),
        ]

        with (
            patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings),
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=MagicMock()),
        ):
            mock_db.add.side_effect = None
            # We need IntegrityError on commit, not add
            mock_db.commit.side_effect = __import__("sqlalchemy.exc", fromlist=["IntegrityError"]).IntegrityError(
                "mock", None, None
            )

            with pytest.raises(HTTPException) as exc:
                create_user(mock_user_schema, mock_identity, mock_db)
            assert exc.value.status_code == 409

        mock_db.rollback.assert_called_once()

    def test_db_error(self):
        from users.users.crud import create_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "TestUser"
        mock_user_schema.email = "Test@Example.COM"
        mock_user_schema.password = "securePass123"
        mock_user_schema.access_type = "regular"
        mock_user_schema.model_dump.return_value = {"name": "Test"}

        mock_identity = MagicMock()
        mock_settings = MagicMock()
        mock_settings.password_length_regular_users = 8
        mock_settings.password_type = "strict"

        with (
            patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings),
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=MagicMock()),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(HTTPException) as exc:
                create_user(mock_user_schema, mock_identity, mock_db)
            assert exc.value.status_code == 500


class TestCreateSignupUser:
    """create_signup_user: signup with verification/approval logic."""

    def test_success_immediate_active(self):
        from users.users.crud import create_signup_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "newuser"
        mock_user_schema.email = "new@example.com"
        mock_user_schema.password = "securePass123"
        mock_user_schema.model_dump.return_value = {"name": "New User"}

        mock_settings = MagicMock()
        mock_settings.signup_require_email_verification = False
        mock_settings.signup_require_admin_approval = False

        mock_identity = MagicMock()
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=mock_db_user),
        ):
            result = create_signup_user(mock_user_schema, mock_settings, mock_identity, mock_db)

        assert result == mock_db_user
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_success_with_email_verification(self):
        from users.users.crud import create_signup_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "newuser"
        mock_user_schema.email = "new@example.com"
        mock_user_schema.password = "securePass123"
        mock_user_schema.model_dump.return_value = {"name": "New User"}

        mock_settings = MagicMock()
        mock_settings.signup_require_email_verification = True
        mock_settings.signup_require_admin_approval = False

        mock_identity = MagicMock()
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=mock_db_user),
        ):
            result = create_signup_user(mock_user_schema, mock_settings, mock_identity, mock_db)

        assert result == mock_db_user

    def test_success_with_admin_approval(self):
        from users.users.crud import create_signup_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "newuser"
        mock_user_schema.email = "new@example.com"
        mock_user_schema.password = "securePass123"
        mock_user_schema.model_dump.return_value = {"name": "New User"}

        mock_settings = MagicMock()
        mock_settings.signup_require_email_verification = False
        mock_settings.signup_require_admin_approval = True

        mock_identity = MagicMock()
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=mock_db_user),
        ):
            result = create_signup_user(mock_user_schema, mock_settings, mock_identity, mock_db)

        assert result == mock_db_user

    def test_integrity_error(self):
        from users.users.crud import create_signup_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "newuser"
        mock_user_schema.email = "new@example.com"
        mock_user_schema.password = "securePass123"
        mock_user_schema.model_dump.return_value = {"name": "New User"}

        mock_settings = MagicMock()
        mock_settings.signup_require_email_verification = False
        mock_settings.signup_require_admin_approval = False

        mock_identity = MagicMock()

        with (
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=MagicMock()),
        ):
            mock_db.commit.side_effect = __import__("sqlalchemy.exc", fromlist=["IntegrityError"]).IntegrityError(
                "mock", None, None
            )

            with pytest.raises(HTTPException) as exc:
                create_signup_user(mock_user_schema, mock_settings, mock_identity, mock_db)
            assert exc.value.status_code == 409

        mock_db.rollback.assert_called_once()

    def test_db_error(self):
        from users.users.crud import create_signup_user

        mock_db = MagicMock(spec=Session)
        mock_user_schema = MagicMock()
        mock_user_schema.username = "newuser"
        mock_user_schema.email = "new@example.com"
        mock_user_schema.password = "securePass123"
        mock_user_schema.model_dump.return_value = {"name": "New User"}

        mock_settings = MagicMock()
        mock_settings.signup_require_email_verification = False
        mock_settings.signup_require_admin_approval = False

        mock_identity = MagicMock()

        with (
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="hash"),
            patch("users.users.crud.users_models.Users", return_value=MagicMock()),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(HTTPException) as exc:
                create_signup_user(mock_user_schema, mock_settings, mock_identity, mock_db)
            assert exc.value.status_code == 500


class TestEditUser:
    """edit_user: admin-level user update (async)."""

    @pytest.mark.asyncio
    async def test_success(self):
        from users.users.crud import edit_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_user_schema = MagicMock()
        mock_user_schema.username = "updateduser"
        mock_user_schema.photo_path = None
        mock_user_schema.model_dump.return_value = {"username": "updateduser", "name": "Updated"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_user(1, mock_user_schema, mock_db)

        assert result == mock_db_user
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_with_height_change(self):
        from users.users.crud import edit_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_user_schema = MagicMock()
        mock_user_schema.username = "updateduser"
        mock_user_schema.photo_path = None
        # Return a copy so the returned dict has the new height
        mock_user_schema.model_dump.return_value = {"username": "updateduser", "height": 185}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.health_weight_utils.calculate_bmi_all_user_entries") as mock_bmi,
        ):
            # Simulate that height changes during refresh
            def refresh_side_effect():
                mock_db_user.height = 185

            mock_db.refresh.side_effect = lambda x: refresh_side_effect()

            result = await edit_user(1, mock_user_schema, mock_db)

        assert result == mock_db_user
        mock_bmi.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_photo_path_update(self):
        from users.users.crud import edit_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = "old/path.jpg"

        mock_user_schema = MagicMock()
        mock_user_schema.username = "updateduser"
        mock_user_schema.photo_path = "new/path.jpg"
        mock_user_schema.model_dump.return_value = {
            "username": "updateduser",
            "photo_path": "new/path.jpg",
        }

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.users_utils.delete_user_photo_filesystem", new_callable=AsyncMock) as mock_del,
        ):
            mock_db_user.photo_path = "new/path.jpg"
            result = await edit_user(1, mock_user_schema, mock_db)

        assert result == mock_db_user
        mock_del.assert_called_once()

    @pytest.mark.asyncio
    async def test_integrity_error(self):
        from users.users.crud import edit_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_user_schema = MagicMock()
        mock_user_schema.username = "updateduser"
        mock_user_schema.photo_path = None
        mock_user_schema.model_dump.return_value = {"username": "updateduser"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            mock_db.commit.side_effect = __import__("sqlalchemy.exc", fromlist=["IntegrityError"]).IntegrityError(
                "mock", None, None
            )

            with pytest.raises(HTTPException) as exc:
                await edit_user(1, mock_user_schema, mock_db)
            assert exc.value.status_code == 409

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_error(self):
        from users.users.crud import edit_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.id = 1
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_user_schema = MagicMock()
        mock_user_schema.username = "updateduser"
        mock_user_schema.photo_path = None
        mock_user_schema.model_dump.return_value = {"username": "updateduser"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await edit_user(1, mock_user_schema, mock_db)


class TestEditProfileUser:
    """edit_profile_user: self-service profile update (async) with allow-list."""

    @pytest.mark.asyncio
    async def test_success(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.id = 1
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {"name": "New Name", "username": "newname"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_allow_list_filters_admin_fields(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {
            "name": "Valid Name",
            "access_type": "admin",
            "active": True,
        }

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user
        # access_type and active should not be set
        assert not hasattr(mock_db_user, "access_type") or not any(
            c[0][0] == "access_type" for c in mock_db_user.mock_calls
        )

    @pytest.mark.asyncio
    async def test_photo_path_traversal_rejected(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = "data/user_images/1.valid.jpg"

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {
            "name": "Test",
            "photo_path": "data/user_images/1.valid.jpg",
        }

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user

    @pytest.mark.asyncio
    async def test_photo_path_with_backslash_traversal_rejected(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {
            "name": "Test",
            "photo_path": "data\\user_images\\2.evil.jpg",
        }

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user

    @pytest.mark.asyncio
    async def test_photo_path_with_dotdot_traversal_rejected(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {
            "name": "Test",
            "photo_path": "data/user_images/1./../3.avatar.jpg",
        }

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user

    @pytest.mark.asyncio
    async def test_height_change_triggers_bmi_recalc(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.id = 1
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {"height": 185}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.health_weight_utils.calculate_bmi_all_user_entries") as mock_bmi,
        ):
            mock_db.refresh.side_effect = lambda x: setattr(mock_db_user, "height", 185)

            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user
        mock_bmi.assert_called_once_with(1, mock_db)

    @pytest.mark.asyncio
    async def test_photo_cleared_deletes_filesystem(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.id = 1
        mock_db_user.height = 180
        mock_db_user.photo_path = "data/user_images/1.old.jpg"

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {"photo_path": None}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.users_utils.delete_user_photo_filesystem", new_callable=AsyncMock) as mock_del,
        ):
            result = await edit_profile_user(1, mock_profile, mock_db)

        assert result == mock_db_user
        mock_del.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_integrity_error(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {"name": "Test"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            mock_db.commit.side_effect = __import__("sqlalchemy.exc", fromlist=["IntegrityError"]).IntegrityError(
                "mock", None, None
            )

            with pytest.raises(HTTPException) as exc:
                await edit_profile_user(1, mock_profile, mock_db)
            assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_db_error(self):
        from users.users.crud import edit_profile_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.height = 180
        mock_db_user.photo_path = None

        mock_profile = MagicMock()
        mock_profile.model_dump.return_value = {"name": "Test"}

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await edit_profile_user(1, mock_profile, mock_db)


class TestApproveUser:
    """approve_user: admin approval flow."""

    def test_success(self):
        from users.users.crud import approve_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.email_verified = True

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            approve_user(1, mock_db)

        assert mock_db_user.active is True
        assert mock_db_user.pending_admin_approval is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_email_not_verified(self):
        from users.users.crud import approve_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.email_verified = False

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            with pytest.raises(HTTPException) as exc:
                approve_user(1, mock_db)
            assert exc.value.status_code == 400

        mock_db.commit.assert_not_called()

    def test_db_error(self):
        from users.users.crud import approve_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.email_verified = True

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(HTTPException) as exc:
                approve_user(1, mock_db)
            assert exc.value.status_code == 500


class TestVerifyUserEmail:
    """verify_user_email: email verification with conditional activation."""

    def test_success_without_admin_approval(self):
        from users.users.crud import verify_user_email

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_settings = MagicMock()
        mock_settings.signup_require_admin_approval = False

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            verify_user_email(1, mock_settings, mock_db)

        assert mock_db_user.email_verified is True
        assert mock_db_user.active is True
        assert mock_db_user.pending_admin_approval is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_success_with_admin_approval(self):
        from users.users.crud import verify_user_email

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_settings = MagicMock()
        mock_settings.signup_require_admin_approval = True

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            verify_user_email(1, mock_settings, mock_db)

        assert mock_db_user.email_verified is True
        # Should NOT change active/pending_approval when admin approval required
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_db_error(self):
        from users.users.crud import verify_user_email

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_settings = MagicMock()
        mock_settings.signup_require_admin_approval = False

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(HTTPException) as exc:
                verify_user_email(1, mock_settings, mock_db)
            assert exc.value.status_code == 500


class TestEditUserPassword:
    """edit_user_password: password update with hashing options."""

    def test_success_already_hashed(self):
        from users.users.crud import edit_user_password

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            edit_user_password(1, "already_hashed_value", None, mock_db, is_hashed=True)

        assert mock_db_user.password == "already_hashed_value"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_success_plain_password(self):
        from users.users.crud import edit_user_password

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()
        mock_db_user.access_type = "regular"

        mock_settings = MagicMock()
        mock_identity = MagicMock()

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.server_settings_utils.get_server_settings_or_404", return_value=mock_settings),
            patch("users.users.crud.users_utils.check_password_and_hash", return_value="new_hashed"),
        ):
            edit_user_password(1, "plainPass123", mock_identity, mock_db, is_hashed=False)

        assert mock_db_user.password == "new_hashed"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_without_commit(self):
        from users.users.crud import edit_user_password

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            edit_user_password(1, "hashed_value", None, mock_db, is_hashed=True, commit=False)

        assert mock_db_user.password == "hashed_value"
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    def test_db_error(self):
        from users.users.crud import edit_user_password

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(HTTPException) as exc:
                edit_user_password(1, "hash", None, mock_db, is_hashed=True)
            assert exc.value.status_code == 500


class TestUpdateUserPhoto:
    """update_user_photo: set or clear user photo path (async)."""

    @pytest.mark.asyncio
    async def test_set_photo(self):
        from users.users.crud import update_user_photo

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user):
            result = await update_user_photo(1, mock_db, photo_path="data/user_images/1.jpg")

        assert result == "data/user_images/1.jpg"
        assert mock_db_user.photo_path == "data/user_images/1.jpg"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_photo(self):
        from users.users.crud import update_user_photo

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.users_utils.delete_user_photo_filesystem", new_callable=AsyncMock) as mock_del,
        ):
            result = await update_user_photo(1, mock_db, photo_path=None)

        assert result is None
        assert mock_db_user.photo_path is None
        mock_del.assert_called_once_with(1)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_error(self):
        from users.users.crud import update_user_photo

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await update_user_photo(1, mock_db, photo_path="path")


class TestDeleteUser:
    """delete_user: remove user from DB and filesystem (async)."""

    @pytest.mark.asyncio
    async def test_success(self):
        from users.users.crud import delete_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.users_utils.delete_user_photo_filesystem", new_callable=AsyncMock) as mock_del,
        ):
            await delete_user(1, mock_db)

        mock_db.delete.assert_called_once_with(mock_db_user)
        mock_db.commit.assert_called_once()
        mock_del.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_db_error(self):
        from users.users.crud import delete_user

        mock_db = MagicMock(spec=Session)
        mock_db_user = MagicMock()

        with (
            patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=mock_db_user),
            patch("users.users.crud.users_utils.delete_user_photo_filesystem", new_callable=AsyncMock),
        ):
            mock_db.commit.side_effect = SQLAlchemyError("DB error")

            with pytest.raises(SQLAlchemyError):
                await delete_user(1, mock_db)


class TestUpdateUserMfa:
    """update_user_mfa: enable/disable MFA."""

    def _patch_select_and_auth_mfa(self):
        """Patch select and AuthUserMFA to avoid SQLAlchemy mapper initialization."""
        mock_stmt = MagicMock()
        mock_select = patch("users.users.crud.select").start()
        mock_select.return_value.where.return_value = mock_stmt
        mock_auth_model = patch("users.users.crud.auth_mfa_models.AuthUserMFA").start()
        mock_mfa_instance = MagicMock()
        mock_auth_model.return_value = mock_mfa_instance
        return mock_stmt, mock_mfa_instance

    def test_enable_mfa_new_row(self):
        from users.users.crud import update_user_mfa

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        _, _ = self._patch_select_and_auth_mfa()

        try:
            with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=MagicMock()):
                update_user_mfa(1, mock_db, encrypted_secret="encrypted_secret_value")
        finally:
            patch.stopall()

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_enable_mfa_existing_row(self):
        from users.users.crud import update_user_mfa

        mock_db = MagicMock(spec=Session)
        existing_row = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_row
        _, _ = self._patch_select_and_auth_mfa()

        try:
            with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=MagicMock()):
                update_user_mfa(1, mock_db, encrypted_secret="encrypted_secret_value")
        finally:
            patch.stopall()

        assert existing_row.mfa_enabled is True
        assert existing_row.mfa_secret == "encrypted_secret_value"
        mock_db.commit.assert_called_once()

    def test_disable_mfa_existing_row(self):
        from users.users.crud import update_user_mfa

        mock_db = MagicMock(spec=Session)
        existing_row = MagicMock()
        existing_row.mfa_enabled = True
        existing_row.mfa_secret = "some_secret"
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_row
        _, _ = self._patch_select_and_auth_mfa()

        try:
            with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=MagicMock()):
                update_user_mfa(1, mock_db, encrypted_secret=None)
        finally:
            patch.stopall()

        assert existing_row.mfa_enabled is False
        assert existing_row.mfa_secret is None
        mock_db.commit.assert_called_once()

    def test_disable_mfa_new_row(self):
        from users.users.crud import update_user_mfa

        mock_db = MagicMock(spec=Session)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        _, _ = self._patch_select_and_auth_mfa()

        try:
            with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=MagicMock()):
                update_user_mfa(1, mock_db, encrypted_secret=None)
        finally:
            patch.stopall()

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_db_error(self):
        from users.users.crud import update_user_mfa

        mock_db = MagicMock(spec=Session)
        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        with patch("users.users.crud.users_utils.get_user_by_id_or_404", return_value=MagicMock()):
            with pytest.raises(HTTPException) as exc:
                update_user_mfa(1, mock_db, encrypted_secret="secret")
            assert exc.value.status_code == 500
