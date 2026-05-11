"""Redis connection utilities."""

from typing import NoReturn

from redis import Redis, RedisError

import core.logger as core_logger


DEFAULT_REDIS_SOCKET_TIMEOUT_SECONDS: float = 2.0


class RedisStorageUnavailable(RuntimeError):
    """
    Raised when Redis-backed storage cannot be reached.

    Attributes:
        None.
    """


def raise_redis_storage_unavailable(
    purpose: str,
    operation: str,
    err: RedisError,
) -> NoReturn:
    """
    Raise a sanitized Redis storage outage exception.

    Args:
        purpose: Human-readable Redis storage purpose.
        operation: Storage operation that failed.
        err: Redis client exception.

    Raises:
        RedisStorageUnavailable: Always raised.
    """
    core_logger.print_to_log(
        f"Redis operation failed for {purpose}: {operation}",
        "error",
        exc=err,
    )
    raise RedisStorageUnavailable(
        f"Redis storage unavailable for {purpose}"
    ) from err


def is_redis_storage_uri(storage_uri: str) -> bool:
    """
    Check whether a storage URI selects Redis.

    Args:
        storage_uri: Storage URI from configuration.

    Returns:
        True when the URI selects Redis storage.

    Raises:
        None.
    """
    normalized_uri = storage_uri.strip().lower()
    return normalized_uri.startswith(("redis://", "rediss://", "unix://"))


def create_redis_client(
    storage_uri: str,
    purpose: str,
    socket_timeout: float = DEFAULT_REDIS_SOCKET_TIMEOUT_SECONDS,
) -> Redis:
    """
    Create and verify a Redis client.

    Args:
        storage_uri: Redis storage URI.
        purpose: Human-readable use case for error messages.
        socket_timeout: Connection and read timeout in seconds.

    Returns:
        Connected Redis client.

    Raises:
        RuntimeError: When Redis cannot be initialized.
    """
    try:
        redis_client = Redis.from_url(
            storage_uri,
            decode_responses=True,
            socket_connect_timeout=socket_timeout,
            socket_timeout=socket_timeout,
        )
        redis_client.ping()
    except (RedisError, ValueError) as redis_error:
        raise RuntimeError(
            f"Unable to initialize Redis storage for {purpose}."
        ) from redis_error
    return redis_client
