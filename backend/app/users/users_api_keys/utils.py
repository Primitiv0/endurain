"""User API key utility functions."""

import hashlib
import json
import secrets

import auth.constants as auth_constants


def generate_api_key() -> str:
    """
    Generate a new raw API key.

    Keys have the format ``endurain_<token>`` where
    ``<token>`` is 32 cryptographically random bytes
    encoded as base64url (43 characters). Total entropy
    is 256 bits.

    Returns:
        A new raw API key string.
    """
    return f"endurain_{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """
    Compute the SHA-256 hex digest of a raw API key.

    High-entropy secrets do not require a slow KDF
    (Argon2/bcrypt). SHA-256 is the industry standard
    for hashing tokens of this entropy level.

    Args:
        raw_key: The plain-text API key to hash.

    Returns:
        Lowercase hex-encoded SHA-256 digest (64 chars).
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


def validate_api_key_scopes(
    requested_scopes: list[str],
    user_access_type: str,
) -> None:
    """
    Validate requested scopes against the user's allowed scope.

    Regular users may only grant scopes within
    ``REGULAR_ACCESS_SCOPE``. Admin users may grant scopes
    within ``ADMIN_ACCESS_SCOPE``.

    Args:
        requested_scopes: List of scopes the caller wants
            to assign to the new API key.
        user_access_type: The ``access_type`` field of the
            owning user (e.g. ``"regular"`` or ``"admin"``).

    Raises:
        ValueError: If any requested scope is not permitted
            for the user's access type.
    """
    if user_access_type == "admin":
        allowed = set(auth_constants.ADMIN_ACCESS_SCOPE)
    else:
        allowed = set(auth_constants.REGULAR_ACCESS_SCOPE)

    disallowed = set(requested_scopes) - allowed
    if disallowed:
        raise ValueError(f"Scopes not permitted for this user: " f"{disallowed}")


def scopes_to_json(scopes: list[str]) -> str:
    """
    Serialize a list of scope strings to a JSON string.

    Args:
        scopes: List of scope strings.

    Returns:
        JSON-encoded string representation.
    """
    return json.dumps(scopes)


def json_to_scopes(scopes_json: str) -> list[str]:
    """
    Deserialize a JSON string to a list of scope strings.

    Args:
        scopes_json: JSON-encoded scope list.

    Returns:
        List of scope strings.
    """
    return json.loads(scopes_json)
