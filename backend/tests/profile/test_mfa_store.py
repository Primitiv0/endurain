"""Tests for temporary MFA setup secret storage."""

from fnmatch import fnmatch

import pytest
from redis import RedisError

import core.redis as core_redis
import profile.mfa_store as profile_mfa_store


class FakeRedis:
    """Small Redis test double for MFA secret storage."""

    def __init__(self) -> None:
        """
        Initialize fake Redis state.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        """
        Set a fake Redis key.

        Args:
            key: Redis key.
            value: Redis value.
            ex: Optional TTL in seconds.

        Returns:
            None.

        Raises:
            None.
        """
        self.values[key] = value
        if ex is not None:
            self.expirations[key] = ex

    def get(self, key: str) -> str | None:
        """
        Get a fake Redis key.

        Args:
            key: Redis key.

        Returns:
            Stored value, or None.

        Raises:
            None.
        """
        return self.values.get(key)

    def delete(self, *keys: str) -> int:
        """
        Delete fake Redis keys.

        Args:
            keys: Redis keys to delete.

        Returns:
            Number of deleted keys.

        Raises:
            None.
        """
        deleted_count = 0
        for key in keys:
            if key in self.values:
                deleted_count += 1
            self.values.pop(key, None)
            self.expirations.pop(key, None)
        return deleted_count

    def scan_iter(self, match: str | None = None, count: int | None = None):
        """
        Iterate fake Redis keys matching a glob pattern.

        Args:
            match: Optional glob pattern.
            count: Optional scan batch size.

        Returns:
            Iterator of matching keys.

        Raises:
            None.
        """
        del count
        for key in list(self.values):
            if match is None or fnmatch(key, match):
                yield key


class FailingRedis(FakeRedis):
    """Redis test double that raises for one operation."""

    def __init__(self, failing_operation: str) -> None:
        """
        Initialize the failing fake Redis client.

        Args:
            failing_operation: Redis operation that should fail.

        Returns:
            None.

        Raises:
            None.
        """
        super().__init__()
        self.failing_operation = failing_operation

    def _fail_if_needed(self, operation: str) -> None:
        """
        Raise RedisError for the configured operation.

        Args:
            operation: Operation currently being executed.

        Returns:
            None.

        Raises:
            RedisError: When operation matches the configured failure.
        """
        if self.failing_operation == operation:
            raise RedisError("redis unavailable")

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        """
        Set a key or raise RedisError.

        Args:
            key: Redis key.
            value: Redis value.
            ex: Optional TTL in seconds.

        Returns:
            None.

        Raises:
            RedisError: When set is configured to fail.
        """
        self._fail_if_needed("set")
        return super().set(key, value, ex)

    def get(self, key: str) -> str | None:
        """
        Get a key or raise RedisError.

        Args:
            key: Redis key.

        Returns:
            Stored value, or None.

        Raises:
            RedisError: When get is configured to fail.
        """
        self._fail_if_needed("get")
        return super().get(key)

    def delete(self, *keys: str) -> int:
        """
        Delete keys or raise RedisError.

        Args:
            keys: Redis keys to delete.

        Returns:
            Number of deleted keys.

        Raises:
            RedisError: When delete is configured to fail.
        """
        self._fail_if_needed("delete")
        return super().delete(*keys)

    def scan_iter(self, match: str | None = None, count: int | None = None):
        """
        Iterate keys or raise RedisError.

        Args:
            match: Optional glob pattern.
            count: Optional scan batch size.

        Returns:
            Iterator of matching keys.

        Raises:
            RedisError: When scan_iter is configured to fail.
        """
        self._fail_if_needed("scan_iter")
        yield from super().scan_iter(match, count)


class TestMFASecretStore:
    """Tests for the process-local MFA secret store."""

    def test_memory_store_lifecycle(self) -> None:
        """Test memory store add, get, has, and delete."""
        store = profile_mfa_store.MFASecretStore()

        store.add_secret(123, "secret-value")

        assert store.has_secret(123) is True
        assert store.get_secret(123) == "secret-value"

        store.delete_secret(123)

        assert store.has_secret(123) is False
        assert store.get_secret(123) is None

    def test_memory_store_expired_secret_is_evicted(self) -> None:
        """Test memory store evicts expired secrets on read."""
        store = profile_mfa_store.MFASecretStore(ttl_seconds=-1)
        store.add_secret(123, "secret-value")

        assert store.get_secret(123) is None
        assert store.has_secret(123) is False


class TestRedisMFASecretStore:
    """Tests for Redis-backed MFA secret storage."""

    def test_redis_store_lifecycle(self) -> None:
        """Test Redis store add, get, has, and delete."""
        redis_client = FakeRedis()
        store = profile_mfa_store.RedisMFASecretStore(
            redis_client,
            ttl_seconds=42,
        )

        store.add_secret(123, "secret-value")
        redis_key = store._secret_key(123)

        assert redis_client.values[redis_key] != "secret-value"
        assert redis_client.expirations[redis_key] == 42
        assert store.has_secret(123) is True
        assert store.get_secret(123) == "secret-value"

        store.delete_secret(123)

        assert store.has_secret(123) is False
        assert store.get_secret(123) is None

    def test_redis_key_hashes_user_id(self) -> None:
        """Test Redis store does not write raw user IDs in key names."""
        redis_client = FakeRedis()
        store = profile_mfa_store.RedisMFASecretStore(redis_client)

        store.add_secret(42, "secret-value")
        redis_key = next(iter(redis_client.values))

        assert redis_key.startswith("endurain:auth:mfa:setup_secret:")
        assert not redis_key.endswith(":42")

    def test_redis_store_clear_all(self) -> None:
        """Test Redis store clears all setup secret keys."""
        redis_client = FakeRedis()
        store = profile_mfa_store.RedisMFASecretStore(redis_client)
        unrelated_key = "endurain:auth:mfa:pending:other"

        store.add_secret(1, "secret-one")
        store.add_secret(2, "secret-two")
        redis_client.set(unrelated_key, "kept")

        store.clear_all()

        assert redis_client.values == {unrelated_key: "kept"}

    def test_redis_get_failure_is_sanitized(self) -> None:
        """Test Redis get errors become MFA-store outage errors."""
        store = profile_mfa_store.RedisMFASecretStore(FailingRedis("get"))

        with pytest.raises(
            profile_mfa_store.MFASecretStoreUnavailable
        ) as exc_info:
            store.get_secret(123)

        assert isinstance(
            exc_info.value.__cause__,
            core_redis.RedisStorageUnavailable,
        )

    def test_redis_set_failure_is_sanitized(self) -> None:
        """Test Redis set errors become MFA-store outage errors."""
        store = profile_mfa_store.RedisMFASecretStore(FailingRedis("set"))

        with pytest.raises(profile_mfa_store.MFASecretStoreUnavailable):
            store.add_secret(123, "secret-value")


class TestMFASecretStoreFactory:
    """Tests for MFA secret store factory helpers."""

    def test_create_mfa_secret_store_memory_uri(self) -> None:
        """Test memory URI creates memory-backed storage."""
        store = profile_mfa_store.create_mfa_secret_store("memory://")

        assert isinstance(store, profile_mfa_store.MFASecretStore)

    def test_create_mfa_secret_store_blank_uri(self) -> None:
        """Test blank URI creates memory-backed storage."""
        store = profile_mfa_store.create_mfa_secret_store("")

        assert isinstance(store, profile_mfa_store.MFASecretStore)

    def test_create_mfa_secret_store_redis_uri(self, monkeypatch) -> None:
        """Test Redis URI creates Redis-backed storage."""
        monkeypatch.setattr(
            profile_mfa_store.core_redis,
            "create_redis_client",
            lambda storage_uri, purpose: FakeRedis(),
        )

        store = profile_mfa_store.create_mfa_secret_store(
            "redis://localhost:6379/0"
        )

        assert isinstance(store, profile_mfa_store.RedisMFASecretStore)

    def test_create_mfa_secret_store_rejects_unknown_uri(self) -> None:
        """Test unsupported storage URIs are rejected."""
        with pytest.raises(ValueError) as exc_info:
            profile_mfa_store.create_mfa_secret_store(
                "postgresql://localhost/db"
            )

        assert "Unsupported MFA secret storage URI" in str(exc_info.value)

    def test_mfa_secret_uri_falls_back_to_rate_limit(
        self,
        monkeypatch,
    ) -> None:
        """Test MFA secret URI falls back to rate limit URI."""
        monkeypatch.setattr(
            profile_mfa_store.core_config.settings,
            "AUTH_SECURITY_STORAGE_URI",
            None,
        )
        monkeypatch.setattr(
            profile_mfa_store.core_config.settings,
            "RATE_LIMIT_STORAGE_URI",
            "redis://localhost:6379/0",
        )

        assert (
            profile_mfa_store.get_mfa_secret_storage_uri()
            == "redis://localhost:6379/0"
        )

    def test_mfa_secret_uri_prefers_auth_specific_uri(
        self,
        monkeypatch,
    ) -> None:
        """Test auth-specific URI overrides the rate limit URI."""
        monkeypatch.setattr(
            profile_mfa_store.core_config.settings,
            "AUTH_SECURITY_STORAGE_URI",
            "memory://",
        )
        monkeypatch.setattr(
            profile_mfa_store.core_config.settings,
            "RATE_LIMIT_STORAGE_URI",
            "redis://localhost:6379/0",
        )

        assert profile_mfa_store.get_mfa_secret_storage_uri() == "memory://"