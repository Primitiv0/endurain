"""Tests for MFA reads sourced from the ``users_mfa`` table.

Verifies that MFA logic in ``profile.utils`` reads
``mfa_enabled`` and ``mfa_secret`` from ``user.auth_mfa``
(the ``users_mfa`` row) and not from the legacy ``users``
columns.

"""

import profile.utils as profile_utils
from typing import Any
from unittest.mock import MagicMock, patch

import auth.mfa.models as auth_mfa_models
import pytest
import users.users.models as users_models
from fastapi import HTTPException, status

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(
    user_id: int = 1,
    mfa_enabled: bool = False,
    mfa_secret: str | None = None,
) -> MagicMock:
    """
    Return a mock Users row whose auth_mfa mirrors the given MFA state.

    Both the legacy columns and the auth_mfa row are populated so that
    tests can assert which source the code is actually reading.
    """
    mfa_row: MagicMock | None
    if mfa_enabled or mfa_secret:
        mfa_row = MagicMock(spec=auth_mfa_models.AuthUserMFA)
        mfa_row.mfa_enabled = mfa_enabled
        mfa_row.mfa_secret = mfa_secret
    else:
        mfa_row = None

    user = MagicMock(spec=users_models.Users)
    user.id = user_id
    user.username = "testuser"
    # Legacy columns (must NOT be read — source of truth is auth_mfa)
    user.mfa_enabled = False
    user.mfa_secret = None
    # New source of truth
    user.auth_mfa = mfa_row
    return user


def _patch_get_user(user: MagicMock) -> Any:
    """Patch users_crud.get_user_by_id to return the given user."""
    return patch(
        "profile.utils.users_crud.get_user_by_id",
        return_value=user,
    )


# ---------------------------------------------------------------------------
# setup_user_mfa — reads mfa_enabled from auth_mfa
# ---------------------------------------------------------------------------


class TestSetupUserMFAReadSwitch:
    """setup_user_mfa reads mfa_enabled from auth_mfa, not users columns."""

    def test_raises_when_auth_mfa_enabled(self, mock_db):
        """
        Raises 400 when auth_mfa.mfa_enabled is True,
        even though the legacy users.mfa_enabled is False.
        """
        user = _make_user(mfa_enabled=True, mfa_secret="enc")
        # Confirm legacy column disagrees — proves the read came from auth_mfa
        assert user.mfa_enabled is False

        with _patch_get_user(user), pytest.raises(HTTPException) as exc:
            profile_utils.setup_user_mfa(1, mock_db)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enabled" in exc.value.detail

    def test_proceeds_when_auth_mfa_disabled(self, mock_db):
        """
        Returns MFASetupResponse when auth_mfa.mfa_enabled is False.
        """
        user = _make_user(mfa_enabled=False)
        user.auth_mfa = MagicMock(spec=auth_mfa_models.AuthUserMFA)
        user.auth_mfa.mfa_enabled = False

        with _patch_get_user(user):
            result = profile_utils.setup_user_mfa(1, mock_db)

        assert result is not None

    def test_proceeds_when_auth_mfa_row_missing(self, mock_db):
        """
        Returns MFASetupResponse when auth_mfa is None
        (pre-migration edge case).
        """
        user = _make_user()
        user.auth_mfa = None

        with _patch_get_user(user):
            result = profile_utils.setup_user_mfa(1, mock_db)

        assert result is not None


# ---------------------------------------------------------------------------
# enable_user_mfa — reads mfa_enabled from auth_mfa
# ---------------------------------------------------------------------------


class TestEnableUserMFAReadSwitch:
    """enable_user_mfa reads mfa_enabled from auth_mfa."""

    def test_raises_when_auth_mfa_already_enabled(self, mock_db):
        """
        Raises 400 when auth_mfa says MFA is already on.
        """
        user = _make_user(mfa_enabled=True, mfa_secret="enc")
        assert user.mfa_enabled is False  # legacy column is wrong on purpose

        with _patch_get_user(user), pytest.raises(HTTPException) as exc:
            profile_utils.enable_user_mfa(1, "secret", "123456", MagicMock(), mock_db)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "already enabled" in exc.value.detail


# ---------------------------------------------------------------------------
# disable_user_mfa — reads mfa_enabled from auth_mfa
# ---------------------------------------------------------------------------


class TestDisableUserMFAReadSwitch:
    """disable_user_mfa reads mfa_enabled from auth_mfa."""

    def test_raises_when_auth_mfa_not_enabled(self, mock_db):
        """
        Raises 400 when auth_mfa says MFA is off, even if legacy
        column had it on.
        """
        user = _make_user(mfa_enabled=False)
        # Force legacy column to True to prove it is NOT being read
        user.mfa_enabled = True

        with _patch_get_user(user), pytest.raises(HTTPException) as exc:
            profile_utils.disable_user_mfa(1, mock_db)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "not enabled" in exc.value.detail

    def test_raises_when_auth_mfa_row_missing(self, mock_db):
        """
        Raises 400 when auth_mfa is None (treated as disabled).
        """
        user = _make_user()
        user.auth_mfa = None
        user.mfa_enabled = True  # legacy column True — must be ignored

        with _patch_get_user(user), pytest.raises(HTTPException) as exc:
            profile_utils.disable_user_mfa(1, mock_db)

        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# verify_user_mfa — reads mfa_enabled + mfa_secret from auth_mfa
# ---------------------------------------------------------------------------


class TestVerifyUserMFAReadSwitch:
    """verify_user_mfa reads both fields from auth_mfa."""

    def test_returns_false_when_auth_mfa_disabled(self, mock_db):
        """
        Returns False when auth_mfa.mfa_enabled is False,
        even if the legacy column was True.
        """
        user = _make_user(mfa_enabled=False)
        user.mfa_enabled = True  # legacy — must be ignored
        user.mfa_secret = "enc"  # legacy — must be ignored

        with _patch_get_user(user):
            result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), mock_db)

        assert result is False

    def test_returns_false_when_auth_mfa_row_missing(self, mock_db):
        """Returns False when auth_mfa is None."""
        user = _make_user()
        user.auth_mfa = None
        user.mfa_enabled = True  # legacy True — must be ignored

        with _patch_get_user(user):
            result = profile_utils.verify_user_mfa(1, "123456", MagicMock(), mock_db)

        assert result is False

    def test_uses_auth_mfa_secret_for_totp(self, mock_db):
        """
        Decrypts the secret from auth_mfa.mfa_secret, not
        from the legacy users.mfa_secret column.
        """
        user = _make_user(mfa_enabled=True, mfa_secret="auth_enc_secret")
        user.mfa_secret = "WRONG_legacy_secret"  # must be ignored

        with (
            _patch_get_user(user),
            patch(
                "profile.utils.core_cryptography.decrypt_token_fernet",
                return_value=None,  # decrypt fails → returns False cleanly
            ) as mock_decrypt,
        ):
            profile_utils.verify_user_mfa(1, "123456", MagicMock(), mock_db)

        mock_decrypt.assert_called_once_with("auth_enc_secret")


# ---------------------------------------------------------------------------
# is_mfa_enabled_for_user — reads from auth_mfa
# ---------------------------------------------------------------------------


class TestIsMFAEnabledForUserReadSwitch:
    """is_mfa_enabled_for_user reads from auth_mfa."""

    def test_returns_true_when_auth_mfa_enabled_with_secret(self, mock_db):
        """
        Returns True only when auth_mfa row is enabled AND has a secret.
        """
        user = _make_user(mfa_enabled=True, mfa_secret="enc")
        # Legacy columns deliberately wrong
        user.mfa_enabled = False
        user.mfa_secret = None

        with _patch_get_user(user):
            result = profile_utils.is_mfa_enabled_for_user(1, mock_db)

        assert result is True

    def test_returns_false_when_auth_mfa_enabled_no_secret(self, mock_db):
        """Returns False when mfa_enabled but secret is None."""
        user = _make_user(mfa_enabled=True, mfa_secret=None)

        with _patch_get_user(user):
            result = profile_utils.is_mfa_enabled_for_user(1, mock_db)

        assert result is False

    def test_returns_false_when_auth_mfa_row_missing(self, mock_db):
        """Returns False when auth_mfa is None."""
        user = _make_user()
        user.auth_mfa = None
        user.mfa_enabled = True  # legacy True — must be ignored
        user.mfa_secret = "enc"  # legacy — must be ignored

        with _patch_get_user(user):
            result = profile_utils.is_mfa_enabled_for_user(1, mock_db)

        assert result is False

    def test_returns_false_when_user_not_found(self, mock_db):
        """Returns False when user does not exist."""
        with patch(
            "profile.utils.users_crud.get_user_by_id",
            return_value=None,
        ):
            result = profile_utils.is_mfa_enabled_for_user(99, mock_db)

        assert result is False
