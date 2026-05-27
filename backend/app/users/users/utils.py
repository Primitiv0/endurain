import os

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session

import auth.passwords as auth_passwords

import users.users.crud as users_crud
import users.users.schema as users_schema
import users.users.models as users_models

import users.users_integrations.crud as user_integrations_crud
import users.users_default_gear.crud as user_default_gear_crud
import users.users_privacy_settings.crud as users_privacy_settings_crud
import health.health_targets.crud as health_targets_crud
import auth.mfa.crud as auth_mfa_crud
import server_settings.models as server_settings_models
import server_settings.schema as server_settings_schema

import core.file_uploads as core_file_uploads
import core.config as core_config


def get_user_by_id_or_404(user_id: int, db: Session) -> users_models.Users:
    """
    Retrieve user by ID or raise 404 error.

    Args:
        user_id: User ID to search for.
        db: SQLAlchemy database session.

    Returns:
        Users model (guaranteed non-None).

    Raises:
        HTTPException: 404 if user not found.
    """
    # Get the user from the database
    db_user = users_crud.get_user_by_id(user_id, db)

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return db_user


def verify_step_up_credentials(
    user_id: int,
    current_password: str | None,
    mfa_code: str | None,
    password_hasher: auth_passwords.PasswordHasher,
    db: Session,
) -> None:
    """
    Enforce step-up verification for sensitive account operations.

    A valid access token alone is not sufficient authorisation for
    operations that grant persistent account access (password
    change, API-key creation, MFA enrolment, MFA backup-code
    regeneration, MFA disable, etc.). This helper requires the
    caller to re-prove possession of the current password and —
    when MFA is enabled — a fresh TOTP or backup code.

    SSO-only accounts have no local password (``db_user.password``
    is ``None`` or empty). For those callers the password factor
    is skipped because there is nothing to verify against; this
    is a known coverage gap that should eventually be closed by
    requiring a fresh IdP re-authentication on the same set of
    sensitive endpoints. Until that flow exists, SSO-only users
    rely on the access-token check plus (when applicable) MFA.

    Args:
        user_id: ID of the authenticated user.
        current_password: The user's current password as supplied
            in the request body. May be ``None`` for SSO-only
            accounts; ignored when the account has no local
            password.
        mfa_code: TOTP or backup code, required when MFA is
            enabled. Ignored when MFA is disabled.
        password_hasher: Password hasher dependency.
        db: SQLAlchemy database session.

    Raises:
        HTTPException: 401 if the current password is wrong, is
            missing for an account that has one, or when MFA is
            enabled and the supplied code is missing or invalid.
            The error message intentionally does not distinguish
            the failure modes.
    """
    # Local import to avoid a circular dependency between
    # users.users.utils and profile.utils (which imports
    # users.users.crud at module load time).
    import profile.utils as profile_utils

    db_user = get_user_by_id_or_404(user_id, db)

    has_local_password = bool(db_user.password)
    if has_local_password:
        if not current_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Step-up verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not password_hasher.verify(current_password, db_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Step-up verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # else: SSO-only account; no password to verify. See docstring
    # for the known coverage gap and planned IdP re-auth flow.

    if profile_utils.is_mfa_enabled_for_user(user_id, db):
        if not mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code required for this operation",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not profile_utils.verify_user_mfa(
            user_id, mfa_code, password_hasher, db
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Step-up verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )


def get_admin_users_or_404(db: Session) -> list[users_models.Users]:
    """
    Retrieve all admin users from database or raise 404 error.

    Args:
        db: SQLAlchemy database session.

    Returns:
        List of all admin User models.

    Raises:
        HTTPException: 404 if no admin users found.
    """
    admins = users_crud.get_users_admin(db)

    if not admins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No admin users found",
        )

    return admins


def check_password_and_hash(
    password: str,
    password_hasher: auth_passwords.PasswordHasher,
    server_settings: (
        server_settings_models.ServerSettings
        | server_settings_schema.ServerSettingsRead
    ),
    user_access_type: str,
) -> str:
    """
    Validates password against the configured policy and hashes it.

    Args:
        password (str): The password to validate and hash.
        password_hasher (PasswordHasher): The password hasher instance.
        server_settings (ServerSettings | ServerSettingsRead): The server settings containing password policies.
        user_access_type (str): The access type of the user (e.g., "regular" or "admin").

    Returns:
        str: The hashed password.

    Raises:
        HTTPException: If password validation fails.
    """
    # Determine minimum length based on user access type
    min_length = (
        server_settings.password_length_admin_users
        if user_access_type == users_schema.UserAccessType.ADMIN.value
        else server_settings.password_length_regular_users
    )
    # Check if password meets requirements
    try:
        password_hasher.validate_password(
            password, min_length, str(server_settings.password_type)
        )
    except auth_passwords.PasswordPolicyError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Hash the password
    hashed_password = password_hasher.hash_password(password)

    # Return the hashed password
    return hashed_password


def check_user_is_active(
    user: users_models.Users | users_schema.UsersRead,
) -> None:
    """
    Check if user is active and raise 403 if inactive.

    Args:
        user: User object to check (User or UsersRead schema).

    Returns:
        None

    Raises:
        HTTPException: 403 if user is not active.
    """
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_user_default_data(user_id: int, db: Session) -> None:
    """
    Create default data for newly created user.

    Args:
        user_id: ID of user to create default data for.
        db: SQLAlchemy database session.

    Returns:
        None
    """
    # Create the user integrations in the database
    user_integrations_crud.create_user_integrations(user_id, db)

    # Create the user privacy settings
    users_privacy_settings_crud.create_user_privacy_settings(user_id, db)

    # Create the user health targets
    health_targets_crud.create_health_targets(user_id, db)

    # Create the user default gear
    user_default_gear_crud.create_user_default_gear(user_id, db)

    # Create the user's MFA row (disabled by default)
    auth_mfa_crud.create_users_mfa_row(user_id, db)


_ALLOWED_USER_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".webp"}
)


async def save_user_image_file(user_id: int, file: UploadFile, db: Session) -> str:
    """
    Save user image file with security validation and update DB.

    Uses centralized file upload handler for validation and async
    I/O, then updates user photo path in database.

    Args:
        user_id: ID of user whose image is being saved.
        file: Uploaded image file (UploadFile).
        db: SQLAlchemy database session.

    Returns:
        Path to saved image file.

    Raises:
        HTTPException: 400 if filename or extension is invalid,
            413 if too large, 500 if upload fails.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Defense-in-depth allow-list on the user-supplied extension.
    # SafeUploads still validates the magic number afterwards, so a
    # mismatched signature is rejected even if the extension passes.
    _, file_extension = os.path.splitext(file.filename)
    file_extension = file_extension.lower()
    if file_extension not in _ALLOWED_USER_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported user image file type",
        )

    filename = f"{user_id}{file_extension}"

    # Save file using centralized file upload handler
    await core_file_uploads.save_validated_upload(
        file,
        kind=core_file_uploads.UploadKind.IMAGE,
        upload_dir=core_config.USER_IMAGES_DIR,
        filename=filename,
    )

    # Update user photo path in database
    return str(
        await users_crud.update_user_photo(
            user_id, db, os.path.join(core_config.USER_IMAGES_DIR, filename)
        )
    )


async def delete_user_photo_filesystem(user_id: int) -> None:
    """
    Delete user photo files from filesystem.

    Args:
        user_id: ID of user whose photo files to delete.

    Returns:
        None
    """
    await core_file_uploads.delete_files_by_pattern(
        core_config.USER_IMAGES_DIR, f"{user_id}.*"
    )
