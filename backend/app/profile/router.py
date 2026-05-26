"""Profile API endpoints for user management and operations.

This module provides FastAPI endpoints for:
- User profile retrieval and updates
- Password and privacy settings management
- MFA (Multi-Factor Authentication) operations
- Profile photo upload and deletion
- Session management
- Identity provider linking and unlinking
- Profile data export and import
"""

from typing import Annotated

from datetime import datetime, timezone
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    Response,
    Request,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import users.users.schema as users_schema
import users.users.crud as users_crud
import users.users.utils as users_utils

import users.users_identity_providers.crud as user_idp_crud
import users.users_identity_providers.schema as user_idp_schema
import users.users_identity_providers.utils as user_idp_utils

import auth.password_hasher as auth_password_hasher
import auth.security_stores as auth_security_stores

import auth.identity_providers.crud as idp_crud
import auth.idp_link_tokens.utils as idp_link_token_utils
import auth.idp_link_tokens.schema as idp_link_token_schema

import users.users_integrations.crud as user_integrations_crud

import users.users_privacy_settings.crud as users_privacy_settings_crud
import users.users_privacy_settings.schema as users_privacy_settings_schema

import profile.utils as profile_utils
import profile.schema as profile_schema
import profile.export_service as profile_export_service
import profile.import_service as profile_import_service
import profile.exceptions as profile_exceptions
import profile.mfa_store as profile_mfa_store

import auth.security as auth_security

import auth.mfa_backup_codes.schema as mfa_backup_codes_schema
import auth.mfa_backup_codes.crud as mfa_backup_codes_crud

import auth.sessions.crud as users_session_crud
import auth.sessions.schema as users_session_schema

import core.database as core_database
import core.logger as core_logger
import core.rate_limit as core_rate_limit
import core.config as core_config
import core.file_uploads as core_file_uploads

import websocket.manager as websocket_manager

# Define the API router
router = APIRouter()


def _raise_mfa_secret_store_unavailable(
    err: profile_mfa_store.MFASecretStoreUnavailable,
) -> None:
    """
    Return a controlled response when MFA setup storage is down.

    Args:
        err: MFA setup secret storage outage.

    Returns:
        None.

    Raises:
        HTTPException: Always raised with a 503 status.
    """
    core_logger.print_to_log(
        "MFA setup secret storage unavailable",
        "error",
        exc=err,
    )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="MFA setup temporarily unavailable",
    ) from err


@router.get("", status_code=status.HTTP_200_OK, response_model=users_schema.UsersMe)
async def read_users_me(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> users_schema.UsersMe:
    """
    Retrieve authenticated user profile with integrations.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        User object with integration and privacy settings.

    Raises:
        HTTPException: If user or settings not found.
    """
    # Get the user from the database
    user = users_crud.get_user_by_id(token_user_id, db)

    # If the user does not exist raise the exception
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_integrations = user_integrations_crud.get_user_integrations_by_user_id(
        user.id, db
    )

    if user_integrations is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not validate credentials (user integrations not found)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_privacy_settings = (
        users_privacy_settings_crud.get_user_privacy_settings_by_user_id(user.id, db)
    )

    if user_privacy_settings is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not validate credentials (user privacy settings not found)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build UsersMe schema from model using model_validate
    user_me = users_schema.UsersMe.model_validate(user)

    # Update with integration and privacy settings
    return user_me.model_copy(
        update={
            "is_strava_linked": (1 if user_integrations.strava_token else 0),
            "is_garminconnect_linked": (
                1 if user_integrations.garminconnect_token else 0
            ),
            "default_activity_visibility": (
                user_privacy_settings.default_activity_visibility
            ),
            "hide_activity_start_time": (
                user_privacy_settings.hide_activity_start_time
            ),
            "hide_activity_location": (user_privacy_settings.hide_activity_location),
            "hide_activity_map": (user_privacy_settings.hide_activity_map),
            "hide_activity_hr": user_privacy_settings.hide_activity_hr,
            "hide_activity_power": (user_privacy_settings.hide_activity_power),
            "hide_activity_cadence": (user_privacy_settings.hide_activity_cadence),
            "hide_activity_elevation": (user_privacy_settings.hide_activity_elevation),
            "hide_activity_speed": (user_privacy_settings.hide_activity_speed),
            "hide_activity_pace": (user_privacy_settings.hide_activity_pace),
            "hide_activity_laps": (user_privacy_settings.hide_activity_laps),
            "hide_activity_workout_sets_steps": (
                user_privacy_settings.hide_activity_workout_sets_steps
            ),
            "hide_activity_gear": (user_privacy_settings.hide_activity_gear),
            # Derived flag for the frontend: distinguishes
            # SSO-only accounts from accounts with a local
            # password so step-up modals can hide the password
            # field. The hash itself is never exposed.
            "has_local_password": bool(user.password),
        }
    )


@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    response_model=list[users_session_schema.UsersSessionsRead],
)
async def read_sessions_me(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> list[users_session_schema.UsersSessionsRead]:
    """
    Retrieve all sessions for authenticated user.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        List of session objects for the user.
    """
    # Get the sessions from the database
    if core_config.settings.ENVIRONMENT != "demo":
        return users_session_crud.get_user_sessions(token_user_id, db)
    else:
        core_logger.print_to_log(
            "Session retrieval attempted in demo environment - returning empty list",
            "info",
        )
        return []


@core_rate_limit.limiter.limit(core_rate_limit.SENSITIVE)
@router.post(
    "/idp/{idp_id}/link/token",
    status_code=status.HTTP_201_CREATED,
    response_model=idp_link_token_schema.IdpLinkTokenResponse,
)
async def generate_link_token(
    idp_id: int,
    link_request: idp_link_token_schema.IdpLinkTokenRequest,
    request: Request,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> idp_link_token_schema.IdpLinkTokenResponse:
    """
    Generate a one-time token for linking an identity provider.

    This endpoint creates a short-lived (60 seconds), single-use token
    that can be used to securely initiate the OAuth flow for linking
    an identity provider to the authenticated user's account.

    Linking an identity provider is a sensitive operation that enables
    persistent authentication. Step-up verification is required: the
    caller MUST supply ``current_password``, and an MFA code when MFA
    is enabled on the account.

    This approach is more secure than passing access tokens in query
    parameters, as the link token:
    - Expires in 60 seconds
    - Can only be used once
    - Is scoped specifically for IdP linking
    - Limits exposure in server logs and browser history

    Args:
        idp_id (int): The ID of the identity provider to link.
        link_request (IdpLinkTokenRequest): Request with step-up credentials.
        request (Request): The FastAPI request object.
        token_user_id (int): The authenticated user's ID extracted from the access token.
        password_hasher (PasswordHasher): Password hasher dependency.
        db (Session): The database session.

    Returns:
        IdpLinkTokenResponse: Contains the one-time token and expiration time.

    Raises:
        HTTPException:
            - 401 UNAUTHORIZED: If step-up verification fails.
            - 404 NOT_FOUND: If the identity provider doesn't exist or is disabled.
            - 409 CONFLICT: If the identity provider is already linked.
            - 500 INTERNAL_SERVER_ERROR: If token generation fails.
    """
    # Step-up verification is required before issuing a link token.
    # Linking an IdP is a sensitive, persistent grant of account access.
    users_utils.verify_step_up_credentials(
        token_user_id,
        link_request.current_password,
        link_request.mfa_code,
        password_hasher,
        db,
    )

    # Validate IDP exists and is enabled
    idp = idp_crud.get_identity_provider(idp_id, db)
    if not idp or not idp.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Identity provider not found or disabled",
        )

    # Check if already linked
    existing_link = user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id(
        token_user_id, idp_id, db
    )
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Identity provider {idp.name} is already linked to your account",
        )

    # Get client IP address
    ip_address = request.client.host if request.client else None

    # Generate one-time link token
    link_token = idp_link_token_utils.generate_idp_link_token(
        user_id=token_user_id, idp_id=idp_id, ip_address=ip_address, db=db
    )

    core_logger.print_to_log(
        f"Generated link token for user {token_user_id}, idp_id={idp_id} ({idp.name})",
        "debug",
    )

    return link_token


@router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
    response_model=str,
)
async def upload_profile_image(
    file: UploadFile,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> str:
    """
    Upload user profile image with security validation.

    Args:
        file: Image file to upload.
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Result of save operation.

    Raises:
        HTTPException: If validation or save fails.
    """
    return await users_utils.save_user_image_file(token_user_id, file, db)


@router.put("", status_code=status.HTTP_200_OK, response_model=dict)
async def edit_user(
    user_attributtes: users_schema.ProfileUpdate,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> dict:
    """
    Edit self-service profile fields for the authenticated user.

    Uses an explicit allow-list (:class:`users_schema.ProfileUpdate`)
    so administrative attributes such as ``access_type``,
    ``active``, ``mfa_enabled``, ``mfa_secret``, ``email_verified``,
    and ``pending_admin_approval`` cannot be modified through this
    endpoint, even if a malicious client submits them.

    Args:
        user_attributtes: Allow-listed profile updates.
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Success message with user ID.
    """
    await users_crud.edit_profile_user(token_user_id, user_attributtes, db)

    return {"message": f"User ID {token_user_id} updated successfully"}


@router.put("/privacy", status_code=status.HTTP_200_OK, response_model=dict)
async def edit_profile_privacy_settings(
    user_privacy_settings: users_privacy_settings_schema.UsersPrivacySettingsUpdate,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> dict:
    """
    Edit privacy settings for authenticated user.

    Args:
        user_privacy_settings: New privacy settings.
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Success message.
    """
    # Edit the user privacy settings in the database
    users_privacy_settings_crud.edit_user_privacy_settings(
        token_user_id, user_privacy_settings, db
    )

    # Return success message
    return {"message": f"User ID {token_user_id} privacy settings updated successfully"}


@router.put("/password", status_code=status.HTTP_200_OK, response_model=dict)
async def edit_profile_password(
    user_attributtes: users_schema.UsersEditPassword,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> dict:
    """
    Update user password after step-up verification.

    Requires the caller to re-prove identity with the current
    password — and an MFA code when MFA is enabled — before the
    new password is accepted. This prevents a stolen access
    token alone from being parlayed into permanent account
    takeover.

    Args:
        user_attributtes: Schema with current password, new
            password, and optional MFA code.
        token_user_id: ID of the user extracted from the access
            token.
        password_hasher: Password hasher dependency.
        db: Database session dependency.

    Returns:
        dict: A success message indicating the user's password
        was updated.

    Raises:
        HTTPException: 401 if step-up verification fails.
    """
    users_utils.verify_step_up_credentials(
        token_user_id,
        user_attributtes.current_password,
        user_attributtes.mfa_code,
        password_hasher,
        db,
    )

    users_crud.edit_user_password(
        token_user_id, user_attributtes.password, password_hasher, db
    )

    auth_security_stores.clear_pending_mfa_for_user(token_user_id)

    core_logger.print_to_log(
        f"User {token_user_id} changed password (step-up verified)", "info"
    )

    return {"message": f"User ID {token_user_id} password updated successfully"}


@router.put("/photo", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_profile_photo(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete authenticated user's profile photo.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Success message.
    """
    # Update the user photo_path in the database
    await users_crud.update_user_photo(token_user_id, db)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_profile_session(
    session_id: str,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete user session from database.

    Args:
        session_id: Session identifier to delete.
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        None.
    """
    # Delete the session from the database
    users_session_crud.delete_session(session_id, token_user_id, db)


# Import/export logic


@router.get("/export", status_code=status.HTTP_200_OK, response_class=StreamingResponse)
async def export_profile_data(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> StreamingResponse:
    """
    Export all profile data as ZIP archive.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Streaming response with ZIP archive.

    Raises:
        HTTPException: If user not found or export fails.
    """
    # Get the user from the database
    user = users_crud.get_user_by_id(token_user_id, db)

    # If the user does not exist raise the exception
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Prepare user data — strip every server-managed secret /
    # privileged attribute before it crosses the trust boundary.
    user_dict = profile_utils.sqlalchemy_obj_to_dict(user)
    for sensitive_field in (
        "password",
        "mfa_secret",
        "access_type",
        "active",
        "mfa_enabled",
        "email_verified",
        "pending_admin_approval",
    ):
        user_dict.pop(sensitive_field, None)

    # Create export service and generate archive
    export_service = profile_export_service.ExportService(token_user_id, db)

    headers = {
        "Content-Disposition": f"attachment; filename=user_{token_user_id}_export.zip",
        # Content-Length is omitted for streaming
    }

    try:
        return StreamingResponse(
            export_service.generate_export_archive(user_dict),
            media_type="application/zip",
            headers=headers,
        )
    except (
        profile_exceptions.DatabaseConnectionError,
        profile_exceptions.FileSystemError,
        profile_exceptions.ZipCreationError,
        profile_exceptions.MemoryAllocationError,
        profile_exceptions.DataCollectionError,
        profile_exceptions.ExportTimeoutError,
    ) as err:
        # Handle specific export errors with appropriate HTTP responses
        http_exception = profile_exceptions.handle_import_export_exception(
            err, "profile data export"
        )
        core_logger.print_to_log(
            f"Export error for user {token_user_id}: {err}",
            "error",
            exc=err,
        )
        raise http_exception
    except Exception as err:
        # Log the exception
        core_logger.print_to_log(
            f"Unexpected error in export_profile_data for user {token_user_id}: {err}",
            "error",
            exc=err,
        )
        # Raise an HTTPException with a 500 Internal Server Error status code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from err


@router.post("/import", status_code=status.HTTP_201_CREATED, response_model=dict)
async def import_profile_data(
    file: UploadFile,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
    websocket_manager: Annotated[
        websocket_manager.WebSocketManager,
        Depends(websocket_manager.get_websocket_manager),
    ],
) -> dict:
    """
    Import profile data from ZIP with security validation.

    Args:
        file: ZIP file containing profile data.
        token_user_id: User ID from access token.
        db: Database session.
        websocket_manager: WebSocket manager for updates.

    Returns:
        Import results with counts of imported items.

    Raises:
        HTTPException: If validation or import fails.
    """
    # Comprehensive security validation via the unified pipeline.
    await core_file_uploads.validate_upload(
        file, kind=core_file_uploads.UploadKind.ZIP
    )

    try:
        # Read the ZIP file data
        zip_data = await file.read()

        # Create import service and process the data
        import_service = profile_import_service.ImportService(
            token_user_id, db, websocket_manager
        )
        result = await import_service.import_from_zip_data(zip_data)

        core_logger.print_to_log(
            f"Successfully imported profile data for user {token_user_id}: {result['imported']}",
            "info",
        )

        return result

    except (
        profile_exceptions.ImportValidationError,
        profile_exceptions.FileFormatError,
        profile_exceptions.FileSizeError,
        profile_exceptions.ActivityLimitError,
        profile_exceptions.ZipStructureError,
        profile_exceptions.JSONParseError,
        profile_exceptions.SchemaValidationError,
    ) as err:
        # Handle import validation and format errors
        http_exception = profile_exceptions.handle_import_export_exception(
            err, "profile data import"
        )
        core_logger.print_to_log(
            f"Import validation error for user {token_user_id}: {err}",
            "warning",
        )
        raise http_exception
    except (
        profile_exceptions.DataIntegrityError,
        profile_exceptions.ImportTimeoutError,
        profile_exceptions.DiskSpaceError,
    ) as err:
        # Handle import operation errors
        http_exception = profile_exceptions.handle_import_export_exception(
            err, "profile data import"
        )
        core_logger.print_to_log(
            f"Import operation error for user {token_user_id}: {err}",
            "error",
            exc=err,
        )
        raise http_exception
    except ValueError as err:
        # Handle remaining validation errors for backward compatibility
        core_logger.print_to_log(
            f"Validation error in import_profile_data for user {token_user_id}: {err}",
            "warning",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    except (profile_exceptions.MemoryAllocationError, MemoryError) as err:
        # Handle memory-related errors
        http_exception = profile_exceptions.handle_import_export_exception(
            err, "profile data import"
        )
        core_logger.print_to_log(
            f"Memory error for user {token_user_id}: {err}",
            "error",
        )
        raise http_exception
    except (
        profile_exceptions.DatabaseConnectionError,
        profile_exceptions.FileSystemError,
        profile_exceptions.ZipCreationError,
        profile_exceptions.DataCollectionError,
        profile_exceptions.ExportTimeoutError,
    ) as err:
        # Handle specific import/export errors with appropriate HTTP responses
        http_exception = profile_exceptions.handle_import_export_exception(
            err, "profile data import"
        )
        core_logger.print_to_log(
            f"Import system error for user {token_user_id}: {err}",
            "error",
            exc=err,
        )
        raise http_exception
    except Exception as err:
        # Handle unexpected errors
        core_logger.print_to_log(
            f"Unexpected error in import_profile_data for user {token_user_id}: {err}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Import failed due to an internal error. Please try again or contact support.",
        ) from err


# MFA logic
@router.get(
    "/mfa/status",
    status_code=status.HTTP_200_OK,
    response_model=profile_schema.MFAStatusResponse,
)
async def get_mfa_status(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> profile_schema.MFAStatusResponse:
    """
    Return MFA enabled status for authenticated user.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        MFA status response with enabled flag.
    """
    is_enabled = profile_utils.is_mfa_enabled_for_user(token_user_id, db)
    return profile_schema.MFAStatusResponse(mfa_enabled=is_enabled)


@router.get(
    "/mfa/backup-codes/status",
    status_code=status.HTTP_200_OK,
    response_model=mfa_backup_codes_schema.MFABackupCodeStatus,
)
async def get_backup_code_status(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> mfa_backup_codes_schema.MFABackupCodeStatus:
    """
    Retrieve MFA backup code status for authenticated user.

    Args:
        token_user_id: User ID from access token.
        db: Database session.

    Returns:
        Backup code status with counts and creation date.
    """
    codes = mfa_backup_codes_crud.get_user_backup_codes(token_user_id, db)

    if not codes:
        return mfa_backup_codes_schema.MFABackupCodeStatus(
            has_codes=False,
            total=0,
            unused=0,
            used=0,
            created_at=None,
        )

    unused = sum(1 for code in codes if not code.used)
    used = sum(1 for code in codes if code.used)
    created_at = codes[0].created_at if codes else None

    return mfa_backup_codes_schema.MFABackupCodeStatus(
        has_codes=True,
        total=len(codes),
        unused=unused,
        used=used,
        created_at=created_at,
    )


@router.post(
    "/mfa/setup",
    status_code=status.HTTP_201_CREATED,
    response_model=profile_schema.MFASetupResponse,
)
async def setup_mfa(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
    mfa_secret_store: Annotated[
        profile_mfa_store.MFASecretStoreBackend,
        Depends(profile_mfa_store.get_mfa_secret_store),
    ],
) -> profile_schema.MFASetupResponse:
    """
    Initiate MFA setup for authenticated user.

    Args:
        token_user_id: User ID from access token.
        db: Database session.
        mfa_secret_store: Temporary secret storage.

    Returns:
        MFA setup response with secret and QR code.
    """
    response = profile_utils.setup_user_mfa(token_user_id, db)

    # Store the secret temporarily for the enable step
    try:
        mfa_secret_store.add_secret(token_user_id, response.secret)
    except profile_mfa_store.MFASecretStoreUnavailable as err:
        _raise_mfa_secret_store_unavailable(err)

    return response


@router.put("/mfa/enable", status_code=status.HTTP_200_OK, response_model=dict)
async def enable_mfa(
    request: profile_schema.MFASetupRequest,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
    mfa_secret_store: Annotated[
        profile_mfa_store.MFASecretStoreBackend,
        Depends(profile_mfa_store.get_mfa_secret_store),
    ],
) -> dict:
    """
    Enable MFA for authenticated user after step-up verification.

    A stolen access token alone must not be sufficient to enrol a
    new TOTP secret on a victim's account (which would lock the
    legitimate user out and hand the attacker the backup codes).
    The caller therefore has to re-prove identity with their
    current password before the binding is committed. The TOTP
    code in the request body is the fresh enrolment code from the
    user's authenticator app and is verified separately by
    :func:`profile_utils.enable_user_mfa` against the secret
    issued by ``POST /profile/mfa/setup``. SSO-only accounts may
    omit ``current_password`` (see
    :func:`users.users.utils.verify_step_up_credentials`).

    Args:
        request: MFA setup request with TOTP code and (when the
            account has a local password) current password.
        token_user_id: User ID from access token.
        password_hasher: Password hasher instance for backup code
            generation and step-up verification.
        db: Database session.
        mfa_secret_store: Temporary secret storage.

    Returns:
        Success message and the freshly issued backup codes.

    Raises:
        HTTPException: 400 if no setup is in progress or the TOTP
            code is invalid; 401 if step-up verification fails.
    """
    # Step-up first: if the password is wrong we must not
    # consume / clear the pending MFA secret.
    users_utils.verify_step_up_credentials(
        token_user_id,
        request.current_password,
        # MFA is not yet enabled here, so the MFA branch of
        # step-up is a no-op; pass None to make that explicit.
        None,
        password_hasher,
        db,
    )

    # Get the secret from temporary storage
    try:
        secret = mfa_secret_store.get_secret(token_user_id)
    except profile_mfa_store.MFASecretStoreUnavailable as err:
        _raise_mfa_secret_store_unavailable(err)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No MFA setup in progress. Please run setup first.",
        )

    try:
        backup_codes = profile_utils.enable_user_mfa(
            token_user_id, secret, request.mfa_code, password_hasher, db
        )
        # Clean up the temporary secret
        mfa_secret_store.delete_secret(token_user_id)
        core_logger.print_to_log(
            f"User {token_user_id} enabled MFA (step-up verified)", "info"
        )
        return {
            "message": "MFA enabled successfully",
            "backup_codes": backup_codes,
        }
    except HTTPException as exc:
        # A wrong TOTP at enrolment is a UX-typical retry scenario:
        # the user fat-fingered a digit or the authenticator clock
        # drifted. Burning the pending secret on every wrong code
        # forces a full restart from ``POST /profile/mfa/setup``
        # (new QR, new secret), which is hostile to legitimate users
        # and offers no security benefit — the secret has not yet
        # been bound to the account, ``MFASecretStore`` already
        # enforces a 5-minute TTL on the pending entry, and the
        # caller has already passed step-up password verification
        # above.
        #
        # On any OTHER HTTPException (user vanished, MFA already
        # enabled by a concurrent request, encryption pipeline
        # failure, etc.) we still burn the secret to avoid leaving
        # stale state behind. The status_code + detail check is
        # tightly coupled to ``profile_utils.enable_user_mfa``'s
        # wrong-code branch by design — both must change together.
        if not (
            exc.status_code == status.HTTP_400_BAD_REQUEST
            and exc.detail == "Invalid MFA code"
        ):
            mfa_secret_store.delete_secret(token_user_id)
        raise


@router.put("/mfa/disable", status_code=status.HTTP_200_OK, response_model=dict)
async def disable_mfa(
    request: profile_schema.MFADisableRequest,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> dict:
    """
    Disable MFA for authenticated user after step-up verification.

    Disabling MFA materially weakens the account's security
    posture, so a valid access token alone is not sufficient: the
    caller must re-prove identity with both their current
    password and a fresh MFA code. The MFA code may be either a
    6-digit TOTP or an unused ``XXXX-XXXX`` backup code — the
    same set of factors accepted at login. Step-up verification
    is the single source of truth for the MFA check;
    :func:`profile_utils.disable_user_mfa` only clears state.

    Args:
        request: MFA disable request with current password and
            MFA code.
        token_user_id: User ID from access token.
        password_hasher: Password hasher dependency.
        db: Database session.

    Returns:
        Success message.

    Raises:
        HTTPException: 401 if the current password is wrong or
            the MFA code is invalid; 400 if MFA is not currently
            enabled.
    """
    users_utils.verify_step_up_credentials(
        token_user_id,
        request.current_password,
        request.mfa_code,
        password_hasher,
        db,
    )
    profile_utils.disable_user_mfa(token_user_id, db)
    core_logger.print_to_log(
        f"User {token_user_id} disabled MFA (step-up verified)", "info"
    )
    return {"message": "MFA disabled successfully"}


@router.post("/mfa/verify", status_code=status.HTTP_200_OK, response_model=dict)
async def verify_mfa(
    request: profile_schema.MFARequest,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> dict:
    """
    Verify MFA code for authenticated user.

    Args:
        request: MFA request with code to verify.
        token_user_id: User ID from access token.
        password_hasher: Password hasher instance for backup code verification.
        db: Database session.

    Returns:
        Success message.

    Raises:
        HTTPException: If MFA code is invalid.
    """
    is_valid = profile_utils.verify_user_mfa(
        token_user_id, request.mfa_code, password_hasher, db
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code"
        )
    return {"message": "MFA code verified successfully"}


@router.post(
    "/mfa/backup-codes",
    status_code=status.HTTP_201_CREATED,
    response_model=mfa_backup_codes_schema.MFABackupCodesResponse,
)
@core_rate_limit.limiter.limit(core_rate_limit.SENSITIVE)
async def generate_mfa_backup_codes(
    response: Response,
    request: Request,
    step_up: users_schema.StepUpVerification,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> mfa_backup_codes_schema.MFABackupCodesResponse:
    """
    Generate new MFA backup codes for authenticated user.

    Requires step-up verification (current password + MFA code,
    when MFA is enabled). Issuing new backup codes invalidates
    the previous set, so an attacker holding only an access
    token must not be able to lock the legitimate user out of
    their second factor.

    Args:
        response: FastAPI response object.
        request: FastAPI request object for rate limiting.
        step_up: Step-up verification payload.
        token_user_id: User ID from access token.
        password_hasher: Password hasher for code generation.
        db: Database session.

    Returns:
        Response with generated backup codes and timestamp.

    Raises:
        HTTPException: 401 if step-up verification fails, 404 if
            user not found, 400 if MFA is not enabled.
    """
    user = users_crud.get_user_by_id(token_user_id, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA must be enabled to generate backup codes",
        )

    users_utils.verify_step_up_credentials(
        token_user_id,
        step_up.current_password,
        step_up.mfa_code,
        password_hasher,
        db,
    )

    # Generate codes (invalidates old codes)
    codes = mfa_backup_codes_crud.create_backup_codes(
        token_user_id, password_hasher, db
    )

    # Log event
    core_logger.print_to_log(
        f"User {user.id} generated MFA backup codes (step-up verified)",
        "info",
    )

    return mfa_backup_codes_schema.MFABackupCodesResponse(
        codes=codes,
        created_at=datetime.now(timezone.utc),
    )


# Identity Provider Management Endpoints
@router.get(
    "/idp",
    status_code=status.HTTP_200_OK,
    response_model=list[user_idp_schema.UsersIdentityProviderResponse],
)
async def get_my_identity_providers(
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> list[user_idp_schema.UsersIdentityProviderResponse]:
    """
    Retrieve all identity provider links for the authenticated user.
    This endpoint fetches all external identity provider (IdP) connections associated
    with the current user's account. Each link includes connection metadata and enriched
    details about the identity provider (name, slug, icon, and provider type).
    Args:
        token_user_id (int): The authenticated user's ID extracted from the JWT access token.
            Injected automatically via dependency injection.
        db (Session): Database session for executing queries.
            Injected automatically via dependency injection.
    Returns:
        list[dict]: A list of dictionaries representing the user's IdP links. Each dictionary contains:
            - id (int): Unique identifier for the user-IdP link
            - user_id (int): ID of the user
            - idp_id (int): ID of the identity provider
            - idp_subject (str): User's unique identifier at the IdP
            - linked_at (datetime): Timestamp when the link was created
            - last_login (datetime): Timestamp of the last login via this IdP
            - idp_access_token_expires_at (datetime): Expiration time of the IdP access token
            - idp_refresh_token_updated_at (datetime): Last update time of the refresh token
            - idp_name (str): Display name of the identity provider (if available)
            - idp_slug (str): URL-safe identifier for the IdP (if available)
            - idp_icon (str): Icon/logo URL for the IdP (if available)
            - idp_provider_type (str): Type of provider (e.g., "oauth2", "oidc") (if available)
    Raises:
        HTTPException: May raise authentication/authorization errors via the dependency injection.
    """
    # Get user's IdP links
    idp_links = user_idp_crud.get_user_identity_providers_by_user_id(
        token_user_id,
        db,
    )

    # Enrich with IDP details (batch fetch to avoid N+1 queries)
    return user_idp_utils.enrich_user_identity_providers(
        idp_links,
        token_user_id,
        db,
    )


@core_rate_limit.limiter.limit(core_rate_limit.SENSITIVE)
@router.post(
    "/idp/{idp_id}/unlink",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_my_identity_provider(
    idp_id: int,
    step_up: users_schema.StepUpVerification,
    request: Request,
    token_user_id: Annotated[
        int,
        Depends(auth_security.get_sub_from_access_token),
    ],
    password_hasher: Annotated[
        auth_password_hasher.PasswordHasher,
        Depends(auth_password_hasher.get_password_hasher),
    ],
    db: Annotated[
        Session,
        Depends(core_database.get_db),
    ],
) -> None:
    """
    Delete (unlink) an identity provider from the authenticated user's account.

    This endpoint allows users to remove the association between their
    account and a specific identity provider. It requires step-up
    verification (current password and MFA when enabled) and includes
    safety checks to prevent account lockout by ensuring users maintain
    at least one authentication method (either a password or another
    IdP link).

    Args:
        idp_id (int): The ID of the identity provider to unlink.
        step_up (StepUpVerification): Step-up verification payload.
        request (Request): The FastAPI request object.
        token_user_id (int): User ID extracted from the access token.
        password_hasher (PasswordHasher): Password hasher dependency.
        db (Session): Database session dependency.

    Returns:
        None: Returns 204 No Content on successful deletion.

    Raises:
        HTTPException (401): If step-up verification fails.
        HTTPException (404): If the identity provider doesn't exist or
            is not linked to the user's account.
        HTTPException (400): If attempting to unlink the last authentication method
            without having a password set (prevents account lockout).
        HTTPException (500): If the deletion operation fails at the database level.

    Notes:
        - Enforces step-up verification before unlinking.
        - Prevents account lockout by ensuring users have at least one
          authentication method (password or remaining IdP link).
        - Logs the unlinking action for audit purposes.
        - Uses token-based authentication to ensure users can only
          unlink their own IdPs.
    """
    users_utils.verify_step_up_credentials(
        token_user_id,
        step_up.current_password,
        step_up.mfa_code,
        password_hasher,
        db,
    )

    # Validate IDP exists
    idp = idp_crud.get_identity_provider(idp_id, db)
    if idp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity provider with id {idp_id} not found",
        )

    # Check if link exists for this user
    link = user_idp_crud.get_user_identity_provider_by_user_id_and_idp_id(
        token_user_id, idp_id, db
    )
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Identity provider {idp.name} is not linked to your account",
        )

    # CRITICAL: Prevent account lockout
    # Get user details to check if they have a password
    user = users_crud.get_user_by_id(token_user_id, db)

    # Count remaining IdP links after deletion
    all_idp_links = user_idp_crud.get_user_identity_providers_by_user_id(
        token_user_id, db
    )
    remaining_idp_count = len(all_idp_links) - 1

    # User must have either:
    # - A password set, OR
    # - At least one remaining IdP link
    has_password = user.password is not None and user.password != ""

    if not has_password and remaining_idp_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unlink last authentication method. Please set a password first.",
        )

    # Proceed with deletion
    success = user_idp_crud.delete_user_identity_provider(token_user_id, idp_id, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink identity provider",
        )

    # Audit logging
    core_logger.print_to_log(
        f"User {token_user_id} unlinked IdP: idp_id={idp_id} ({idp.name})"
    )

    # Return 204 No Content (successful deletion)
    return None
