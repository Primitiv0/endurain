"""Tests for users.users.models module."""

import types


class TestHasLocalPassword:
    """Users.has_local_password: True when a credential row exists."""

    def _call(self, local_credential):
        from users.users.models import Users

        obj = types.SimpleNamespace(local_credential=local_credential)
        return Users.has_local_password.fget(obj)

    def test_returns_true_when_credential_row_exists(self):
        assert self._call(object()) is True

    def test_returns_false_when_no_credential_row(self):
        assert self._call(None) is False
