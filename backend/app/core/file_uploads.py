"""Centralized file upload handling with security validation.

All file uploads in the backend MUST go through this module:

- :func:`validate_upload` — content-type-aware validation (no write).
- :func:`save_validated_upload` — validate + persist to disk
  (optionally streamed for large files).
- :data:`file_validator` — single shared :class:`FileValidator` instance.

The unified pipeline gives every upload the same defenses:

- Filename security (Unicode, Windows reserved names, traversal)
  via :mod:`safeuploads`.
- MIME / magic-number / signature validation per content type.
- Configured size and decompression-bomb limits.
- Atomic ``.part``-then-rename writes with cleanup on failure.
- Structured audit logging with a per-request correlation ID.
"""

import asyncio
import glob
import os
from enum import StrEnum
from pathlib import Path
from typing import Awaitable, Callable

import aiofiles
import aiofiles.os
from fastapi import HTTPException, UploadFile, status
from safeuploads import (
    FileSecurityConfig,
    FileValidator,
    SecurityLimits,
)
from safeuploads.audit import SecurityAuditLogger
from safeuploads.exceptions import (
    CompressionSecurityError,
    ExtensionSecurityError,
    FileProcessingError,
    FileSecurityError,
    FileSignatureError,
    FileSizeError,
    FileValidationError,
    FilenameSecurityError,
    MimeTypeError,
    UnicodeSecurityError,
    WindowsReservedNameError,
    ZipBombError,
)

import core.logger as core_logger


# ---------------------------------------------------------------------------
# Module-level configuration and shared validator
# ---------------------------------------------------------------------------

# Activity files (.gpx/.tcx/.fit) and gzip-wrapped variants can be
# large multi-day .fit files. 200 MiB matches the historical cap
# enforced by the legacy activity-upload helper.
_MAX_ACTIVITY_BYTES = 200 * 1024 * 1024
_MAX_GZIP_BYTES = 200 * 1024 * 1024

# Profile-import ZIPs can contain thousands of activity files. The
# uncompressed/individual entry counts here mirror the previous
# ``profile/router.py`` configuration so behaviour is preserved.
_MAX_ZIP_BYTES = 500 * 1024 * 1024
_MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
_MAX_FILES_SAME_TYPE = 2000

# Default 20 MiB image cap from safeuploads is kept; explicitly
# stated here so it appears alongside the other ceilings.
_MAX_IMAGE_BYTES = 20 * 1024 * 1024


def _build_security_config() -> FileSecurityConfig:
    """Build the application-wide :class:`FileSecurityConfig`.

    Returns:
        Configured instance with Endurain-specific limits applied.
    """
    limits = SecurityLimits(
        max_image_size=_MAX_IMAGE_BYTES,
        max_zip_size=_MAX_ZIP_BYTES,
        max_activity_file_size=_MAX_ACTIVITY_BYTES,
        max_gzip_size=_MAX_GZIP_BYTES,
        max_uncompressed_size=_MAX_UNCOMPRESSED_BYTES,
        max_number_files_same_type=_MAX_FILES_SAME_TYPE,
        enable_audit_logging=True,
    )
    config = FileSecurityConfig()
    config.limits = limits
    return config


#: Application-wide :class:`FileValidator`. Stateless w.r.t. uploads;
#: safe to share. Do **not** instantiate ``FileValidator`` elsewhere.
file_validator: FileValidator = FileValidator(config=_build_security_config())

#: Structured audit logger backing the ``safeuploads.audit`` Python
#: logger. Records validation start/success/failure events with a
#: per-request correlation ID.
audit_logger: SecurityAuditLogger = SecurityAuditLogger(enabled=True)


# ---------------------------------------------------------------------------
# Upload kinds and per-kind dispatch
# ---------------------------------------------------------------------------


class UploadKind(StrEnum):
    """Logical content-type of an upload."""

    IMAGE = "image"
    ZIP = "zip"
    ACTIVITY = "activity"
    GZIP = "gzip"


def _validator_for(
    kind: UploadKind,
) -> Callable[[UploadFile], Awaitable[None]]:
    """Return the safeuploads validator coroutine for a kind."""
    if kind is UploadKind.IMAGE:
        return file_validator.validate_image_file
    if kind is UploadKind.ZIP:
        return file_validator.validate_zip_file
    if kind is UploadKind.ACTIVITY:
        return file_validator.validate_activity_file
    if kind is UploadKind.GZIP:
        return file_validator.validate_gzip_file
    raise ValueError(f"Unsupported UploadKind: {kind!r}")


def _max_bytes_for(kind: UploadKind) -> int:
    """Return the configured byte cap for a kind."""
    limits = file_validator.config.limits
    if kind is UploadKind.IMAGE:
        return limits.max_image_size
    if kind is UploadKind.ZIP:
        return limits.max_zip_size
    if kind is UploadKind.ACTIVITY:
        return limits.max_activity_file_size
    if kind is UploadKind.GZIP:
        return limits.max_gzip_size
    raise ValueError(f"Unsupported UploadKind: {kind!r}")


# ---------------------------------------------------------------------------
# Exception mapping
# ---------------------------------------------------------------------------


def _to_http_exception(err: FileSecurityError) -> HTTPException:
    """Translate a safeuploads exception into an HTTPException.

    The error code from :mod:`safeuploads.exceptions` is preserved in
    the ``detail`` payload so clients can react programmatically.

    Args:
        err: Safeuploads exception raised during validation.

    Returns:
        HTTPException with the appropriate status code and a
        machine-readable detail body.
    """
    if isinstance(err, FileSizeError):
        status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    elif isinstance(
        err,
        (
            MimeTypeError,
            FileSignatureError,
            ExtensionSecurityError,
            FilenameSecurityError,
            WindowsReservedNameError,
            UnicodeSecurityError,
            ZipBombError,
            CompressionSecurityError,
            FileValidationError,
        ),
    ):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(err, FileProcessingError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    detail: dict[str, str] = {"message": str(err)}
    error_code = getattr(err, "error_code", None)
    if error_code is not None:
        detail["code"] = str(error_code)
    return HTTPException(status_code=status_code, detail=detail)


# ---------------------------------------------------------------------------
# Validation-only entry point
# ---------------------------------------------------------------------------


async def validate_upload(file: UploadFile, *, kind: UploadKind) -> None:
    """Validate an upload's content without persisting it to disk.

    Use this when the caller wants to consume the file in memory
    (e.g. ZIP profile-import) but still needs the unified safety
    guarantees.

    Args:
        file: Incoming :class:`fastapi.UploadFile`.
        kind: Logical content type to validate against.

    Raises:
        HTTPException: 400/413/500 mapped from the underlying
            safeuploads exception (see :func:`_to_http_exception`).
    """
    validator = _validator_for(kind)
    try:
        await validator(file)
    except FileSecurityError as err:
        core_logger.print_to_log(
            "Upload validation failed: "
            f"kind={kind.value} type={type(err).__name__}",
            "warning",
            exc=err,
        )
        raise _to_http_exception(err) from err


async def validate_local_file(
    path: str | os.PathLike,
    *,
    kind: UploadKind,
    filename: str | None = None,
) -> None:
    """Run :func:`validate_upload` against a file already on disk.

    Wraps the on-disk file in an :class:`UploadFile` so the same
    safeuploads validator can be applied (e.g. after decompressing
    a ``.gz`` activity upload).

    Args:
        path: Filesystem path of the file to validate.
        kind: Logical content type to validate against.
        filename: Optional logical filename used for filename and
            extension checks. Defaults to ``os.path.basename(path)``.

    Raises:
        HTTPException: As :func:`validate_upload`.
    """
    actual_filename = filename or os.path.basename(os.fspath(path))
    # Open in binary mode; UploadFile accepts any binary file object.
    with open(path, "rb") as fh:
        wrapped = UploadFile(file=fh, filename=actual_filename)
        try:
            await validate_upload(wrapped, kind=kind)
        finally:
            await wrapped.close()


# ---------------------------------------------------------------------------
# Filename resolver (defense in depth — server-generated names only)
# ---------------------------------------------------------------------------


def _resolve_upload_path(upload_dir: str, filename: str) -> Path:
    """
    Resolve an upload filename inside the target directory.

    Args:
        upload_dir: Trusted upload directory.
        filename: Caller-provided filename.

    Returns:
        Resolved path inside the upload directory.

    Raises:
        HTTPException: If the filename is empty or unsafe.
    """
    candidate_name = Path(filename)
    if not filename or candidate_name.is_absolute():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )
    if candidate_name.name != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        )

    upload_root = Path(upload_dir).resolve()
    file_path = (upload_root / filename).resolve()
    try:
        file_path.relative_to(upload_root)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename",
        ) from err
    return file_path


async def save_file(
    file: UploadFile | bytes,
    upload_dir: str,
    filename: str,
) -> str:
    """
    Save uploaded bytes to a validated destination path.

    Internal write primitive used by :func:`save_validated_upload`.
    Callers that need security validation MUST go through the
    :func:`save_validated_upload` entry point so that filename
    sanitization, magic-number, and size checks are applied.

    Args:
        file: Uploaded FastAPI file or raw bytes.
        upload_dir: Trusted upload directory.
        filename: Filename to write within upload_dir.

    Returns:
        Full filesystem path where the file was saved.

    Raises:
        HTTPException: 400 for unsafe names, 500 for write failures.
    """
    file_path: Path | None = None
    try:
        # Ensure upload directory exists
        await aiofiles.os.makedirs(upload_dir, exist_ok=True)

        file_path = _resolve_upload_path(upload_dir, filename)

        # Save file asynchronously
        if isinstance(file, bytes):
            content = file
        else:
            # Defensive: validators leave the cursor at 0, but a
            # caller may have read the stream. Always rewind.
            try:
                await file.seek(0)
            except Exception:  # pragma: no cover - defensive
                pass
            content = await file.read()
        async with aiofiles.open(file_path, "wb") as save_file:
            await save_file.write(content)

        core_logger.print_to_log(
            f"File saved successfully: {file_path}",
            "debug",
        )

        return str(file_path)
    except HTTPException:
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Error in save_file: {type(err).__name__}",
            "error",
            exc=err,
        )

        # Remove the file if it was created
        if file_path and await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)

        # Raise an HTTPException with a 500 Internal Server Error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file",
        ) from err


# ---------------------------------------------------------------------------
# Streaming writer primitive
# ---------------------------------------------------------------------------

_STREAM_CHUNK_BYTES = 1024 * 1024


def _stream_to_path_sync(
    file: UploadFile, destination: Path, max_bytes: int
) -> None:
    """Stream an UploadFile to ``destination`` in fixed-size chunks.

    Writes to a sibling ``.part`` file first and atomically renames
    on success. Removes the ``.part`` file on any failure path so
    the destination directory never accumulates orphaned bytes.

    Args:
        file: Incoming FastAPI UploadFile (synchronous file object).
        destination: Final path to write to.
        max_bytes: Hard cap on total bytes accepted.

    Raises:
        HTTPException: 413 when the upload exceeds ``max_bytes``.
        OSError: Re-raised after best-effort cleanup of ``.part``.
    """
    part = destination.with_suffix(destination.suffix + ".part")
    bytes_written = 0
    try:
        # The validators leave file.file at offset 0; rewind defensively.
        try:
            file.file.seek(0)
        except Exception:  # pragma: no cover - defensive
            pass
        with open(part, "wb") as out:
            while True:
                chunk = file.file.read(_STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail={
                            "message": (
                                "Uploaded file exceeds maximum"
                                " allowed size"
                            ),
                            "code": "FILE_SIZE_EXCEEDED",
                        },
                    )
                out.write(chunk)
        os.replace(part, destination)
    except BaseException:
        try:
            if part.exists():
                part.unlink()
        except OSError:
            pass
        raise


async def _stream_to_path(
    file: UploadFile, destination: Path, max_bytes: int
) -> None:
    """Async wrapper around :func:`_stream_to_path_sync`.

    Runs the blocking I/O in a worker thread to avoid stalling the
    event loop on large uploads.
    """
    await asyncio.to_thread(
        _stream_to_path_sync, file, destination, max_bytes
    )


# ---------------------------------------------------------------------------
# Unified validated-write entry point
# ---------------------------------------------------------------------------


async def save_validated_upload(
    file: UploadFile,
    *,
    kind: UploadKind,
    upload_dir: str,
    filename: str,
    stream: bool = False,
) -> str:
    """Validate an upload then persist it to ``upload_dir/filename``.

    This is the single sanctioned entry point for any router that
    needs to write an :class:`UploadFile` to disk.

    Args:
        file: Incoming FastAPI UploadFile.
        kind: Logical content type, drives validator + size cap.
        upload_dir: Trusted destination directory.
        filename: **Server-generated** filename within ``upload_dir``.
            Must not contain path separators; verified by
            :func:`_resolve_upload_path` as defense in depth.
        stream: When True, persist via the streaming writer (used
            for large activity files). When False, the validated
            content is written via :func:`save_file`.

    Returns:
        Absolute filesystem path of the saved file.

    Raises:
        HTTPException: 400/413/500 depending on the failure mode.
    """
    # Validate first; safeuploads rewinds the stream on success.
    await validate_upload(file, kind=kind)

    try:
        await aiofiles.os.makedirs(upload_dir, exist_ok=True)
        destination = _resolve_upload_path(upload_dir, filename)

        if stream:
            await _stream_to_path(
                file, destination, _max_bytes_for(kind)
            )
            saved_path = str(destination)
        else:
            saved_path = await save_file(file, upload_dir, filename)

        return saved_path
    except HTTPException:
        raise
    except Exception as err:
        core_logger.print_to_log(
            f"Error in save_validated_upload: {type(err).__name__}",
            "error",
            exc=err,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Failed to save file",
                "code": "FILE_SAVE_FAILED",
            },
        ) from err


# ---------------------------------------------------------------------------
# Filesystem cleanup helpers
# ---------------------------------------------------------------------------


async def delete_files_by_pattern(directory: str, pattern: str) -> None:
    """
    Delete files from filesystem matching a glob pattern asynchronously.

    Searches directory for files matching the pattern and removes
    them asynchronously. Silently skips files that no longer exist.

    Args:
        directory: Directory path to search in.
        pattern: Glob pattern to match (e.g., "user_123.*").

    Returns:
        None

    Raises:
        None - errors logged but not raised for resilience.
    """
    try:
        # Build full pattern path
        full_pattern = os.path.join(directory, pattern)

        # Find all files matching the pattern
        files_to_delete = glob.glob(full_pattern)

        # Remove each file found asynchronously
        for file_path in files_to_delete:
            try:
                if await aiofiles.os.path.exists(file_path):
                    await aiofiles.os.remove(file_path)

                core_logger.print_to_log(
                    f"File deleted successfully: {file_path}", "debug"
                )
            except OSError as err:
                core_logger.print_to_log(
                    f"Failed to delete file {file_path}: {err}",
                    "warning",
                    exc=err,
                )
    except Exception as err:
        core_logger.print_to_log(
            f"Error deleting files matching pattern {pattern}: {err}",
            "error",
            exc=err,
        )
