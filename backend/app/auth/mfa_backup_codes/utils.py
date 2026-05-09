"""Utility helpers for MFA backup codes."""

import secrets

from sqlalchemy.orm import Session

import auth.mfa_backup_codes.crud as mfa_backup_codes_crud
import auth.password_hasher as auth_password_hasher

# Backup-code alphabet: uppercase ASCII + digits with visually ambiguous
# characters removed (0, O, 1, I) to reduce user transcription errors.
_BACKUP_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_BACKUP_CODE_LENGTH = 8


def generate_backup_code() -> str:
    """Generate a cryptographically secure 8-character backup code.

    Format: ``XXXX-XXXX`` (uppercase alphanumeric, no ambiguous chars).
    Excludes ``0``, ``O``, ``1``, ``I`` to prevent transcription confusion.
    Provides ~40 bits of entropy per code (8 chars from a 32-char alphabet).

    Returns:
        Formatted backup code, e.g. ``"A3K9-7BDF"``.
    """
    code = "".join(
        secrets.choice(_BACKUP_CODE_ALPHABET)
        for _ in range(_BACKUP_CODE_LENGTH)
    )
    return f"{code[:4]}-{code[4:]}"


def verify_and_consume_backup_code(
    user_id: int,
    code: str,
    password_hasher: auth_password_hasher.PasswordHasher,
    db: Session,
) -> bool:
    """Verify and consume a backup code for MFA authentication.

    Iterates over the user's unused backup codes and verifies the supplied
    code against each stored hash. On the first match the code is marked as
    consumed via ``mark_backup_code_as_used``.

    Args:
        user_id: User ID to verify the backup code for.
        code: Plaintext backup code submitted by the user (``XXXX-XXXX``).
        password_hasher: Hasher used to verify the code against stored hashes.
        db: Database session.

    Returns:
        ``True`` if the code matched an unused backup code and was consumed,
        ``False`` otherwise.
    """
    # Get all unused codes for this user
    unused_codes = mfa_backup_codes_crud.get_user_unused_backup_codes(
        user_id, db
    )

    # Try each unused code (constant-time for each)
    for unused_code in unused_codes:
        if password_hasher.verify(code, unused_code.code_hash):
            # Valid code found - mark as used (by primary key)
            mfa_backup_codes_crud.mark_backup_code_as_used(
                unused_code.id, user_id, db
            )
            return True

    # No matching code found
    return False
