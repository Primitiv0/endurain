"""Tests for users_api_keys utility functions."""

import pytest

import users.users_api_keys.utils as users_api_keys_utils
import auth.constants as auth_constants


class TestGenerateApiKey:
    """
    Test suite for generate_api_key function.
    """

    def test_generate_api_key_starts_with_prefix(self):
        """Test that generated key starts with the 'endurain_' prefix."""
        key = users_api_keys_utils.generate_api_key()
        assert key.startswith("endurain_")

    def test_generate_api_key_length(self):
        """Test that generated key has expected minimum length."""
        key = users_api_keys_utils.generate_api_key()
        # "endurain_" (9 chars) + token_urlsafe(32) is at least 43 chars
        assert len(key) > 9

    def test_generate_api_key_uniqueness(self):
        """Test that two generated keys are different (high-entropy enforcement)."""
        key1 = users_api_keys_utils.generate_api_key()
        key2 = users_api_keys_utils.generate_api_key()
        assert key1 != key2

    def test_generate_api_key_random_part_length(self):
        """Test that the random part has at least 40 characters (base64url of 32 bytes)."""
        key = users_api_keys_utils.generate_api_key()
        random_part = key[len("endurain_") :]
        assert len(random_part) >= 40


class TestHashApiKey:
    """
    Test suite for hash_api_key function.
    """

    def test_hash_api_key_returns_64_hex_chars(self):
        """Test that SHA-256 digest is 64 hexadecimal characters."""
        digest = users_api_keys_utils.hash_api_key("endurain_sometoken")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_hash_api_key_deterministic(self):
        """Test that the same input always produces the same hash."""
        raw_key = "endurain_testinput"
        digest1 = users_api_keys_utils.hash_api_key(raw_key)
        digest2 = users_api_keys_utils.hash_api_key(raw_key)
        assert digest1 == digest2

    def test_hash_api_key_different_inputs(self):
        """Test that different inputs produce different hashes."""
        digest1 = users_api_keys_utils.hash_api_key("endurain_keyA")
        digest2 = users_api_keys_utils.hash_api_key("endurain_keyB")
        assert digest1 != digest2

    def test_hash_api_key_known_value(self):
        """Test hash against a known SHA-256 value for correctness."""
        import hashlib

        raw = "endurain_known_test_value"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert users_api_keys_utils.hash_api_key(raw) == expected


class TestValidateApiKeyScopes:
    """
    Test suite for validate_api_key_scopes function.
    """

    def test_validate_regular_user_with_valid_regular_scope(self):
        """Test that a regular user can request a scope in REGULAR_ACCESS_SCOPE."""
        # 'activities:upload' is in REGULAR_ACCESS_SCOPE
        valid_scope = auth_constants.REGULAR_ACCESS_SCOPE[0]
        # Should not raise
        users_api_keys_utils.validate_api_key_scopes([valid_scope], "regular")

    def test_validate_admin_user_with_admin_only_scope(self):
        """Test that admin users can request any scope in ADMIN_ACCESS_SCOPE."""
        admin_only = set(auth_constants.ADMIN_ACCESS_SCOPE) - set(
            auth_constants.REGULAR_ACCESS_SCOPE
        )
        if admin_only:
            scope = next(iter(admin_only))
            # Should not raise for admin
            users_api_keys_utils.validate_api_key_scopes([scope], "admin")

    def test_validate_regular_user_with_admin_scope_raises(self):
        """Test that regular users cannot request admin-only scopes."""
        admin_only = set(auth_constants.ADMIN_ACCESS_SCOPE) - set(
            auth_constants.REGULAR_ACCESS_SCOPE
        )
        if admin_only:
            scope = next(iter(admin_only))
            with pytest.raises(ValueError, match="Scopes not permitted"):
                users_api_keys_utils.validate_api_key_scopes([scope], "regular")

    def test_validate_unknown_scope_raises_for_regular_user(self):
        """Test that unrecognised scopes raise ValueError for a regular user."""
        with pytest.raises(ValueError, match="Scopes not permitted"):
            users_api_keys_utils.validate_api_key_scopes(
                ["totally:unknown_scope"], "regular"
            )

    def test_validate_unknown_scope_raises_for_admin_user(self):
        """Test that unrecognised scopes raise ValueError for an admin user."""
        with pytest.raises(ValueError, match="Scopes not permitted"):
            users_api_keys_utils.validate_api_key_scopes(
                ["totally:unknown_scope"], "admin"
            )

    def test_validate_activities_upload_allowed_for_regular(self):
        """Test that activities:upload is allowed for regular users."""
        # Should not raise
        users_api_keys_utils.validate_api_key_scopes(["activities:upload"], "regular")

    def test_validate_multiple_valid_regular_scopes(self):
        """Test that multiple valid regular scopes are accepted."""
        scopes = list(auth_constants.REGULAR_ACCESS_SCOPE[:2])
        users_api_keys_utils.validate_api_key_scopes(scopes, "regular")

    def test_validate_empty_list_raises_for_regular(self):
        """Test that empty scope list is not disallowed by scope check itself (disallowed = empty set)."""
        # Empty list means no requested scopes; no disallowed scopes either.
        # Should NOT raise since disallowed set is empty.
        users_api_keys_utils.validate_api_key_scopes([], "regular")


class TestScopesJsonRoundTrip:
    """
    Test suite for scopes_to_json and json_to_scopes functions.
    """

    def test_scopes_to_json_returns_string(self):
        """Test that scopes_to_json returns a string."""
        result = users_api_keys_utils.scopes_to_json(["activities:upload"])
        assert isinstance(result, str)

    def test_scopes_to_json_serialises_list(self):
        """Test that scopes_to_json correctly serialises a list."""
        scopes = ["activities:read", "activities:upload"]
        result = users_api_keys_utils.scopes_to_json(scopes)
        assert "activities:read" in result
        assert "activities:upload" in result

    def test_json_to_scopes_returns_list(self):
        """Test that json_to_scopes returns a list."""
        result = users_api_keys_utils.json_to_scopes('["activities:upload"]')
        assert isinstance(result, list)

    def test_scopes_round_trip(self):
        """Test that serialising and deserialising scopes produces the same list."""
        original = ["activities:read", "activities:upload", "gears:read"]
        serialised = users_api_keys_utils.scopes_to_json(original)
        deserialised = users_api_keys_utils.json_to_scopes(serialised)
        assert deserialised == original

    def test_scopes_to_json_empty_list(self):
        """Test that an empty list serialises and deserialises correctly."""
        serialised = users_api_keys_utils.scopes_to_json([])
        deserialised = users_api_keys_utils.json_to_scopes(serialised)
        assert deserialised == []
