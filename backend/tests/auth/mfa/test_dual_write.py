"""Tests for dual-write behaviour introduced in PR 9.

Verifies that ``users.users.crud.update_user_mfa`` writes MFA
state to both the legacy ``users`` columns and the new
``users_mfa`` table.  Tests use a mock DB session — no live
database required.
"""

from unittest.mock import MagicMock, call, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import users.users.crud as users_crud
import auth.mfa.models as auth_mfa_models
import users.users.models as users_models


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user(user_id: int = 1) -> MagicMock:
    """Return a mock Users row with bare minimum attributes."""
    user = MagicMock(spec=users_models.Users)
    user.id = user_id
    user.mfa_enabled = False
    user.mfa_secret = None
    return user


def _make_mock_mfa_row(user_id: int = 1) -> MagicMock:
    """Return a mock AuthUserMFA row."""
    row = MagicMock(spec=auth_mfa_models.AuthUserMFA)
    row.user_id = user_id
    row.mfa_enabled = False
    row.mfa_secret = None
    return row


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestUpdateUserMFADualWrite:
    """Dual-write tests for update_user_mfa."""

    def _setup_db(
        self,
        mock_db: MagicMock,
        mock_user: MagicMock,
        mfa_row: MagicMock | None,
    ) -> None:
        """Wire mock DB to return user from utils and mfa_row from execute."""
        # users_utils.get_user_by_id_or_404 is called inside the function;
        # patch it at the call site used by crud.
        self._user_patch = patch(
            "users.users.utils.get_user_by_id_or_404",
            return_value=mock_user,
        )
        self._user_patch.start()

        # db.execute().scalar_one_or_none() → mfa_row
        mock_db.execute.return_value.scalar_one_or_none.return_value = mfa_row

    def teardown_method(self):
        """Stop all patches after each test."""
        try:
            self._user_patch.stop()
        except AttributeError:
            pass

    # ------------------------------------------------------------------
    # Enable MFA — existing users_mfa row present
    # ------------------------------------------------------------------

    def test_enable_does_not_write_to_legacy_columns(self, mock_db):
        """
        After PR 11, legacy user columns must NOT be touched
        by update_user_mfa — only users_mfa is written.
        """
        user = _make_mock_user()
        mfa_row = _make_mock_mfa_row()
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db, "enc_secret")

        # user mock attributes stay at their initial values
        assert user.mfa_enabled is False
        assert user.mfa_secret is None

    def test_enable_writes_to_users_mfa_row(self, mock_db):
        """
        users_mfa row is updated when enabling MFA.
        """
        user = _make_mock_user()
        mfa_row = _make_mock_mfa_row()
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db, "enc_secret")

        assert mfa_row.mfa_enabled is True
        assert mfa_row.mfa_secret == "enc_secret"

    def test_enable_commits(self, mock_db):
        """db.commit() is called after dual-write enable."""
        user = _make_mock_user()
        mfa_row = _make_mock_mfa_row()
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db, "enc_secret")

        mock_db.commit.assert_called_once()

    # ------------------------------------------------------------------
    # Disable MFA — existing users_mfa row present
    # ------------------------------------------------------------------

    def test_disable_does_not_touch_legacy_columns(self, mock_db):
        """
        After PR 11, legacy user columns must NOT be cleared by
        update_user_mfa — only users_mfa is written.
        """
        user = _make_mock_user()
        user.mfa_enabled = True
        user.mfa_secret = "old_enc_secret"
        mfa_row = _make_mock_mfa_row()
        mfa_row.mfa_enabled = True
        mfa_row.mfa_secret = "old_enc_secret"
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db)

        # user mock attributes stay at their initial values
        assert user.mfa_enabled is True
        assert user.mfa_secret == "old_enc_secret"

    def test_disable_clears_users_mfa_row(self, mock_db):
        """
        users_mfa row is cleared when disabling MFA.
        """
        user = _make_mock_user()
        user.mfa_enabled = True
        user.mfa_secret = "old_enc_secret"
        mfa_row = _make_mock_mfa_row()
        mfa_row.mfa_enabled = True
        mfa_row.mfa_secret = "old_enc_secret"
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db)

        assert mfa_row.mfa_enabled is False
        assert mfa_row.mfa_secret is None

    def test_disable_commits(self, mock_db):
        """db.commit() is called after dual-write disable."""
        user = _make_mock_user()
        mfa_row = _make_mock_mfa_row()
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db)

        mock_db.commit.assert_called_once()

    # ------------------------------------------------------------------
    # users_mfa row missing (fresh install before backfill)
    # ------------------------------------------------------------------

    def test_missing_mfa_row_creates_new_on_enable(self, mock_db):
        """
        When users_mfa row does not exist, a new one is created.
        """
        user = _make_mock_user()
        self._setup_db(mock_db, user, None)  # no existing row

        mock_new_row = MagicMock(spec=auth_mfa_models.AuthUserMFA)
        mock_stmt = MagicMock()
        with patch(
            "users.users.crud.select",
            return_value=mock_stmt,
        ), patch(
            "users.users.crud.auth_mfa_models.AuthUserMFA",
            return_value=mock_new_row,
        ) as MockClass:
            users_crud.update_user_mfa(1, mock_db, "enc_secret")

            MockClass.assert_called_once_with(
                user_id=1,
                mfa_enabled=True,
                mfa_secret="enc_secret",
            )
            mock_db.add.assert_called_once_with(mock_new_row)

    def test_missing_mfa_row_creates_disabled_on_disable(self, mock_db):
        """
        When users_mfa row does not exist and MFA is being
        disabled, a new disabled row is created.
        """
        user = _make_mock_user()
        self._setup_db(mock_db, user, None)

        mock_new_row = MagicMock(spec=auth_mfa_models.AuthUserMFA)
        mock_stmt = MagicMock()
        with patch(
            "users.users.crud.select",
            return_value=mock_stmt,
        ), patch(
            "users.users.crud.auth_mfa_models.AuthUserMFA",
            return_value=mock_new_row,
        ) as MockClass:
            users_crud.update_user_mfa(1, mock_db)

            MockClass.assert_called_once_with(
                user_id=1,
                mfa_enabled=False,
                mfa_secret=None,
            )
            mock_db.add.assert_called_once_with(mock_new_row)

    # ------------------------------------------------------------------
    # Consistency between both stores
    # ------------------------------------------------------------------

    def test_users_mfa_row_correct_after_enable(self, mock_db):
        """users_mfa row holds enabled=True, secret after enable."""
        user = _make_mock_user()
        mfa_row = _make_mock_mfa_row()
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db, "sec")

        assert mfa_row.mfa_enabled is True
        assert mfa_row.mfa_secret == "sec"

    def test_users_mfa_row_correct_after_disable(self, mock_db):
        """users_mfa row holds enabled=False, secret=None after disable."""
        user = _make_mock_user()
        user.mfa_enabled = True
        user.mfa_secret = "sec"
        mfa_row = _make_mock_mfa_row()
        mfa_row.mfa_enabled = True
        mfa_row.mfa_secret = "sec"
        self._setup_db(mock_db, user, mfa_row)

        users_crud.update_user_mfa(1, mock_db)

        assert mfa_row.mfa_enabled is False
        assert mfa_row.mfa_secret is None
