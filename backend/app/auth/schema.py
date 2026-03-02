from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
import core.logger as core_logger


class LoginRequest(BaseModel):
    """
    Schema for login requests containing username and password.

    Attributes:
        username (str): The username of the user. Must be between 1 and 250 characters.
        password (str): The user's password. Must be at least 8 characters long.
    """

    username: str = Field(..., min_length=1, max_length=250)
    password: str = Field(..., min_length=8)


class MFALoginRequest(BaseModel):
    """
    Schema for Multi-Factor Authentication (MFA) login request.

    Attributes:
        username: Username of the user attempting to log in.
        mfa_code: Either a 6-digit TOTP code or a backup code
            (XXXX-XXXX format).
    """

    username: str = Field(..., min_length=1, max_length=250)
    mfa_code: str = Field(
        ...,
        pattern=r"^(\d{6}|[A-Z0-9]{4}-[A-Z0-9]{4})$",
    )


class MFARequiredResponse(BaseModel):
    """
    Represents a response indicating that Multi-Factor Authentication (MFA) is required.

    Attributes:
        mfa_required (bool): Indicates whether MFA is required. Defaults to True.
        username (str): The username for which MFA is required.
        message (str): A message describing the requirement. Defaults to "MFA verification required".
    """

    mfa_required: bool = True
    username: str
    message: str = "MFA verification required"


class MobileSessionResponse(BaseModel):
    """
    Response for mobile password login with PKCE exchange flow.

    This response is returned when a mobile client authenticates using the PKCE
    (Proof Key for Exchange) secure pattern. Instead of returning tokens directly,
    a session_id is returned for secure token exchange via POST /session/{session_id}/tokens.

    Attributes:
        session_id (str): Session identifier for token exchange. Client must send this
            with the code_verifier to obtain access and refresh tokens.
        mfa_required (bool): Whether MFA is required. Defaults to False.
        message (str): Instructions for the client on next steps.
    """

    session_id: str
    mfa_required: bool = False
    message: str = (
        "Complete authentication by exchanging tokens at /session/{session_id}/tokens"
    )


class PendingMFALogin:
    """
    A class to manage pending Multi-Factor Authentication (MFA) login sessions.

    This class provides methods to add, retrieve, delete, and check pending login
    entries for users who are in the process of MFA authentication. Each entry
    carries a creation timestamp and automatically expires after
    ``PENDING_MFA_TTL_SECONDS`` (5 minutes). Expired entries are evicted lazily
    on access and eagerly via ``cleanup_expired``.

    Also implements progressive lockout mechanism to prevent TOTP brute-force
    attacks (AuthQuake-style vulnerabilities).

    Attributes:
        PENDING_MFA_TTL_SECONDS: TTL for pending MFA entries (300 s).
        _store: Maps username to ``(user_id, created_at)`` tuples.
        _failed_attempts: Tracks failed MFA attempts and lockout times
            per username.

    Methods:
        add_pending_login(username: str, user_id: int):
            Adds a pending login entry for the specified username and user ID.

        get_pending_login(username: str):
            Retrieves the user ID if the entry exists and has not expired.

        delete_pending_login(username: str):
            Removes the pending login entry for the specified username.

        has_pending_login(username: str):
            Checks if the specified username has a valid, non-expired entry.

        cleanup_expired():
            Evicts all entries whose TTL has elapsed.

        is_locked_out(username: str):
            Checks if user is currently locked out from MFA attempts.

        get_lockout_time(username: str):
            Gets the lockout expiry time for a user.

        record_failed_attempt(username: str):
            Records a failed MFA attempt and applies progressive lockout.

        reset_failed_attempts(username: str):
            Resets failed attempt counter on successful verification.

        clear_all():
            Clears all pending login entries from the internal store.
    """

    # Abandoned MFA flows expire after 5 minutes, preventing
    # indefinite brute-force windows on the second factor.
    PENDING_MFA_TTL_SECONDS: int = 300

    def __init__(self):
        # {username: (user_id, created_at)}
        self._store: dict[str, tuple[int, datetime]] = {}
        # Failed attempts tracking: {username: (failed_count, lockout_until)}
        self._failed_attempts: dict[str, tuple[int, datetime | None]] = {}

    def add_pending_login(self, username: str, user_id: int) -> None:
        """
        Add a pending MFA login entry for a user.

        Stores the username, associated user ID, and creation
        timestamp in the internal store. Any previous entry for
        this username is overwritten (re-initiating the flow
        resets the TTL).

        Args:
            username: The username of the user to add.
            user_id: The unique identifier of the user.
        """
        self._store[username] = (user_id, datetime.now(timezone.utc))

    def get_pending_login(self, username: str) -> int | None:
        """
        Retrieve the user ID for a pending MFA login.

        Returns ``None`` and evicts the entry if it exists but
        has exceeded ``PENDING_MFA_TTL_SECONDS``.

        Args:
            username: The username to look up.

        Returns:
            The user ID if a valid, non-expired entry exists,
            otherwise None.
        """
        entry = self._store.get(username)
        if entry is None:
            return None

        user_id, created_at = entry
        age = (datetime.now(timezone.utc) - created_at).total_seconds()
        if age > self.PENDING_MFA_TTL_SECONDS:
            # Entry has expired — evict it
            del self._store[username]
            core_logger.print_to_log(
                f"Pending MFA entry for '{username}' expired "
                f"after {int(age)}s and was evicted.",
                "info",
            )
            return None

        return user_id

    def delete_pending_login(self, username: str) -> None:
        """
        Remove the pending MFA login entry for the given username.

        Args:
            username: The username whose entry should be deleted.
        """
        if username in self._store:
            del self._store[username]

    def has_pending_login(self, username: str) -> bool:
        """
        Check if the given username has a valid, non-expired pending
        MFA login session.

        Args:
            username: The username to check.

        Returns:
            True if a non-expired entry exists, False otherwise.
        """
        return self.get_pending_login(username) is not None

    def cleanup_expired(self) -> int:
        """
        Evict all pending MFA entries whose TTL has elapsed.

        Intended to be called by a periodic background task to
        prevent unbounded memory growth.

        Returns:
            Number of entries removed.
        """
        now = datetime.now(timezone.utc)
        expired = [
            username
            for username, (_, created_at) in self._store.items()
            if (now - created_at).total_seconds() > self.PENDING_MFA_TTL_SECONDS
        ]
        for username in expired:
            del self._store[username]
        if expired:
            core_logger.print_to_log(
                f"Cleaned up {len(expired)} expired pending MFA " "entries.",
                "info",
            )
        return len(expired)

    def is_locked_out(self, username: str) -> bool:
        """
        Check if user is locked out from MFA attempts.

        Args:
            username: Username to check

        Returns:
            True if user is currently locked out, False otherwise
        """
        if username not in self._failed_attempts:
            return False

        _, lockout_until = self._failed_attempts[username]
        if lockout_until is None:
            return False

        # Check if lockout has expired
        if datetime.now(timezone.utc) > lockout_until:
            # Lockout expired, reset
            del self._failed_attempts[username]
            return False

        return True

    def get_lockout_time(self, username: str) -> datetime | None:
        """
        Get lockout expiry time for user.

        Args:
            username: Username to check

        Returns:
            Lockout expiry datetime if locked out, None otherwise
        """
        if username not in self._failed_attempts:
            return None

        _, lockout_until = self._failed_attempts[username]
        if lockout_until and datetime.now(timezone.utc) <= lockout_until:
            return lockout_until

        return None

    def record_failed_attempt(self, username: str) -> int:
        """
        Record a failed MFA attempt and apply lockout if threshold exceeded.

        Lockout policy:
        - 5 failures: 5 minute lockout
        - 10 failures: 30 minute lockout
        - 15 failures: 2 hour lockout

        Args:
            username: Username that failed MFA verification

        Returns:
            Number of failed attempts
        """
        now = datetime.now(timezone.utc)

        if username in self._failed_attempts:
            failed_count, lockout_until = self._failed_attempts[username]
            # If still locked out, don't increment counter
            if lockout_until and now <= lockout_until:
                return failed_count
            failed_count += 1
        else:
            failed_count = 1

        # Determine lockout duration based on failure count
        lockout_until = None
        if failed_count >= 15:
            lockout_until = now + timedelta(hours=2)
            core_logger.print_to_log(
                f"MFA lockout (2 hours) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )
        elif failed_count >= 10:
            lockout_until = now + timedelta(minutes=30)
            core_logger.print_to_log(
                f"MFA lockout (30 min) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )
        elif failed_count >= 5:
            lockout_until = now + timedelta(minutes=5)
            core_logger.print_to_log(
                f"MFA lockout (5 min) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )

        self._failed_attempts[username] = (failed_count, lockout_until)
        return failed_count

    def reset_failed_attempts(self, username: str) -> None:
        """
        Reset failed attempt counter on successful MFA verification.

        Args:
            username: Username to reset
        """
        if username in self._failed_attempts:
            del self._failed_attempts[username]

    def clear_all(self):
        """
        Removes all items from the internal store, effectively resetting it to an empty state.
        """
        self._store.clear()
        self._failed_attempts.clear()


def get_pending_mfa_store():
    """
    Retrieve the current pending MFA (Multi-Factor Authentication) store.

    Returns:
        dict: The pending MFA store containing MFA-related data.
    """
    return pending_mfa_store


pending_mfa_store = PendingMFALogin()


def cleanup_expired_pending_mfa_logins() -> None:
    """Evict all expired pending MFA login entries.

    Delegates to the singleton's cleanup_expired() method.
    Intended to be called by the background scheduler.

    Returns:
        None
    """
    pending_mfa_store.cleanup_expired()


class FailedLoginAttempts:
    """
    Track failed login attempts and apply progressive lockouts.

    This class prevents brute-force attacks on user accounts by tracking failed
    login attempts per username and applying increasingly strict lockouts.

    Unlike rate limiting (which is per-IP), this tracks per-username to prevent
    distributed attacks targeting a single account from multiple IPs.

    Attributes:
        _attempts (dict): Maps username to (failed_count, lockout_until) tuples

    Lockout Policy:
        - 5 failures: 5 minute lockout
        - 10 failures: 30 minute lockout
        - 20 failures: 24 hour lockout (requires admin intervention)
    """

    def __init__(self):
        # {username: (failed_count, lockout_until)}
        self._attempts: dict[str, tuple[int, datetime | None]] = {}

    def is_locked_out(self, username: str) -> bool:
        """
        Check if username is locked out from failed login attempts.

        Args:
            username: Username to check

        Returns:
            True if username is currently locked out, False otherwise
        """
        if username not in self._attempts:
            return False

        _, lockout_until = self._attempts[username]
        if lockout_until is None:
            return False

        # Check if lockout has expired
        if datetime.now(timezone.utc) > lockout_until:
            # Lockout expired, reset
            del self._attempts[username]
            return False

        return True

    def get_lockout_time(self, username: str) -> datetime | None:
        """
        Get lockout expiry time for username.

        Args:
            username: Username to check

        Returns:
            Lockout expiry datetime if locked out, None otherwise
        """
        if username not in self._attempts:
            return None

        _, lockout_until = self._attempts[username]
        if lockout_until and datetime.now(timezone.utc) <= lockout_until:
            return lockout_until

        return None

    def record_failed_attempt(self, username: str) -> int:
        """
        Record a failed login attempt and apply lockout if threshold exceeded.

        Lockout policy:
        - 5 failures: 5 minute lockout
        - 10 failures: 30 minute lockout
        - 20 failures: 24 hour lockout (severe - requires admin intervention)

        Args:
            username: Username that failed login

        Returns:
            Number of failed attempts
        """
        now = datetime.now(timezone.utc)

        if username in self._attempts:
            failed_count, lockout_until = self._attempts[username]
            # If still locked out, don't increment counter
            if lockout_until and now <= lockout_until:
                return failed_count
            failed_count += 1
        else:
            failed_count = 1

        # Determine lockout duration based on failure count
        lockout_until = None
        if failed_count >= 20:
            lockout_until = now + timedelta(hours=24)
            core_logger.print_to_log(
                f"Login lockout (24 hours) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )
        elif failed_count >= 10:
            lockout_until = now + timedelta(minutes=30)
            core_logger.print_to_log(
                f"Login lockout (30 min) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )
        elif failed_count >= 5:
            lockout_until = now + timedelta(minutes=5)
            core_logger.print_to_log(
                f"Login lockout (5 min) applied to user {username} after {failed_count} failed attempts",
                "warning",
                context={"username": username, "failed_attempts": failed_count},
            )

        self._attempts[username] = (failed_count, lockout_until)
        return failed_count

    def reset_attempts(self, username: str) -> None:
        """
        Clear failed attempts counter on successful login.

        Args:
            username: Username to reset
        """
        if username in self._attempts:
            del self._attempts[username]

    def clear_all(self) -> None:
        """
        Clear all failed attempt records.

        Used for testing or admin operations.
        """
        self._attempts.clear()


# Create singleton instance
failed_login_attempts = FailedLoginAttempts()


def get_failed_login_attempts():
    """
    Dependency injection for FastAPI.

    Returns:
        FailedLoginAttempts: The global failed login attempts tracker
    """
    return failed_login_attempts
