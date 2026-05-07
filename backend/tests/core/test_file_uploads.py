"""Tests for the unified file-upload pipeline in ``core.file_uploads``."""

from __future__ import annotations

import gzip
import io
import logging
import struct
import zipfile
import zlib
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

import core.file_uploads as core_file_uploads
from core.file_uploads import (
    UploadKind,
    _resolve_upload_path,
    _stream_to_path,
    _to_http_exception,
    save_validated_upload,
    validate_upload,
)
from safeuploads.exceptions import (
    CompressionSecurityError,
    ExtensionSecurityError,
    FileProcessingError,
    FileSignatureError,
    FileSizeError,
    FileValidationError,
    FilenameSecurityError,
    MimeTypeError,
    UnicodeSecurityError,
    WindowsReservedNameError,
    ZipBombError,
)


# ---------------------------------------------------------------------------
# Fixtures: minimal valid payloads per UploadKind
# ---------------------------------------------------------------------------


def _make_png_bytes() -> bytes:
    """Return a minimal valid 1x1 PNG image."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = (
        struct.pack(">I", len(ihdr_data))
        + b"IHDR"
        + ihdr_data
        + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    )
    raw = b"\x00\xff\xff\xff"  # filter byte + 1 RGB pixel
    compressed = zlib.compress(raw)
    idat = (
        struct.pack(">I", len(compressed))
        + b"IDAT"
        + compressed
        + struct.pack(
            ">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
        )
    )
    iend = (
        struct.pack(">I", 0)
        + b"IEND"
        + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    )
    return sig + ihdr + idat + iend


def _make_zip_bytes() -> bytes:
    """Return a minimal valid ZIP archive with one entry."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("hello.txt", b"hello world")
    return buf.getvalue()


def _make_gpx_bytes() -> bytes:
    """Return a minimal valid GPX 1.1 document."""
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<gpx version="1.1" creator="endurain-tests"'
        b' xmlns="http://www.topografix.com/GPX/1/1">\n'
        b"  <trk><name>t</name><trkseg>"
        b"<trkpt lat=\"0\" lon=\"0\"></trkpt>"
        b"</trkseg></trk>\n"
        b"</gpx>\n"
    )


def _make_gzip_bytes() -> bytes:
    """Return a minimal valid gzip-wrapped GPX payload."""
    return gzip.compress(_make_gpx_bytes())


def _upload(filename: str, content: bytes) -> UploadFile:
    """Build an UploadFile around in-memory content."""
    return UploadFile(file=io.BytesIO(content), filename=filename)


_KIND_CASES = [
    (UploadKind.IMAGE, "ok.png", _make_png_bytes),
    (UploadKind.ZIP, "ok.zip", _make_zip_bytes),
    (UploadKind.ACTIVITY, "ok.gpx", _make_gpx_bytes),
    (UploadKind.GZIP, "ok.gpx.gz", _make_gzip_bytes),
]


# ---------------------------------------------------------------------------
# _to_http_exception: one branch per mapped exception class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "err,expected_status",
    [
        (FileSizeError("too big"), 413),
        (MimeTypeError("bad mime"), 400),
        (FileSignatureError("bad sig"), 400),
        (ExtensionSecurityError("bad ext"), 400),
        (FilenameSecurityError("bad name"), 400),
        (WindowsReservedNameError("CON"), 400),
        (UnicodeSecurityError("rtl"), 400),
        (ZipBombError("bomb"), 400),
        (CompressionSecurityError("bad zip"), 400),
        (FileValidationError("generic"), 400),
        (FileProcessingError("oops"), 500),
    ],
)
def test_to_http_exception_mapping(err, expected_status):
    """Each safeuploads exception maps to the documented status."""
    http_err = _to_http_exception(err)
    assert isinstance(http_err, HTTPException)
    assert http_err.status_code == expected_status
    assert isinstance(http_err.detail, dict)
    assert "message" in http_err.detail


# ---------------------------------------------------------------------------
# _resolve_upload_path: filename hardening
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_name",
    [
        "",
        "../escape.txt",
        "subdir/inside.txt",
        "/abs/path.txt",
    ],
)
def test_resolve_upload_path_rejects_unsafe(tmp_path: Path, bad_name: str):
    """Traversal, absolute, and nested names are rejected with 400."""
    with pytest.raises(HTTPException) as exc:
        _resolve_upload_path(str(tmp_path), bad_name)
    assert exc.value.status_code == 400


def test_resolve_upload_path_accepts_safe(tmp_path: Path):
    """A bare filename resolves under the upload directory."""
    resolved = _resolve_upload_path(str(tmp_path), "ok.png")
    assert resolved.parent == tmp_path.resolve()


# ---------------------------------------------------------------------------
# validate_upload: happy + sad paths per kind
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,filename,builder", _KIND_CASES)
async def test_validate_upload_accepts_valid_payload(
    kind: UploadKind, filename: str, builder
):
    """Each kind validates without raising on a well-formed payload."""
    upload = _upload(filename, builder())
    try:
        await validate_upload(upload, kind=kind)
    finally:
        await upload.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,filename,_b", _KIND_CASES)
async def test_validate_upload_rejects_garbage(
    kind: UploadKind, filename: str, _b
):
    """Garbage bytes with a valid extension are rejected."""
    upload = _upload(filename, b"not a real payload")
    with pytest.raises(HTTPException) as exc:
        try:
            await validate_upload(upload, kind=kind)
        finally:
            await upload.close()
    # 400 for signature/MIME mismatch, 413 if size cap would
    # somehow trigger first; both are acceptable rejections.
    assert exc.value.status_code in {400, 413}


# ---------------------------------------------------------------------------
# _stream_to_path: success / oversize / cleanup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_to_path_writes_and_cleans_part_file(
    tmp_path: Path,
):
    """Successful streaming leaves the destination, no .part."""
    payload = b"x" * (3 * 1024 * 1024)  # 3 MiB across multiple chunks
    upload = _upload("blob.bin", payload)
    destination = tmp_path / "blob.bin"
    try:
        await _stream_to_path(upload, destination, max_bytes=10 * 1024 * 1024)
    finally:
        await upload.close()
    assert destination.read_bytes() == payload
    assert not (tmp_path / "blob.bin.part").exists()


@pytest.mark.asyncio
async def test_stream_to_path_aborts_on_oversize(tmp_path: Path):
    """Exceeding max_bytes raises 413 and removes the .part file."""
    payload = b"y" * (2 * 1024 * 1024)
    upload = _upload("over.bin", payload)
    destination = tmp_path / "over.bin"
    with pytest.raises(HTTPException) as exc:
        try:
            await _stream_to_path(upload, destination, max_bytes=1024)
        finally:
            await upload.close()
    assert exc.value.status_code == 413
    assert not destination.exists()
    assert not (tmp_path / "over.bin.part").exists()


# ---------------------------------------------------------------------------
# save_validated_upload: end-to-end per kind + traversal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_validated_upload_image_happy_path(tmp_path: Path):
    """A valid image is validated then persisted to disk."""
    upload = _upload("avatar.png", _make_png_bytes())
    try:
        path = await save_validated_upload(
            upload,
            kind=UploadKind.IMAGE,
            upload_dir=str(tmp_path),
            filename="avatar.png",
        )
    finally:
        await upload.close()
    assert Path(path).exists()
    assert Path(path).read_bytes() == _make_png_bytes()
    assert not (tmp_path / "avatar.png.part").exists()


@pytest.mark.asyncio
async def test_save_validated_upload_streamed_activity(tmp_path: Path):
    """Streaming mode writes the validated bytes atomically."""
    upload = _upload("ride.gpx", _make_gpx_bytes())
    try:
        path = await save_validated_upload(
            upload,
            kind=UploadKind.ACTIVITY,
            upload_dir=str(tmp_path),
            filename="ride.gpx",
            stream=True,
        )
    finally:
        await upload.close()
    assert Path(path).exists()
    assert Path(path).read_bytes() == _make_gpx_bytes()


@pytest.mark.asyncio
async def test_save_validated_upload_traversal_rejected(tmp_path: Path):
    """A traversal filename never produces a file on disk."""
    upload = _upload("ride.gpx", _make_gpx_bytes())
    with pytest.raises(HTTPException) as exc:
        try:
            await save_validated_upload(
                upload,
                kind=UploadKind.ACTIVITY,
                upload_dir=str(tmp_path),
                filename="../escape.gpx",
            )
        finally:
            await upload.close()
    assert exc.value.status_code == 400
    # Nothing under tmp_path, and no parent escape either.
    assert list(tmp_path.iterdir()) == []
    assert not (tmp_path.parent / "escape.gpx").exists()


@pytest.mark.asyncio
async def test_save_validated_upload_signature_mismatch_no_partial(
    tmp_path: Path,
):
    """Failed validation must not leave any file behind."""
    upload = _upload("evil.png", b"this is not a png")
    with pytest.raises(HTTPException):
        try:
            await save_validated_upload(
                upload,
                kind=UploadKind.IMAGE,
                upload_dir=str(tmp_path),
                filename="evil.png",
            )
        finally:
            await upload.close()
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# Module-level wiring
# ---------------------------------------------------------------------------


def test_module_exposes_singleton_validator():
    """The application uses one shared FileValidator instance."""
    assert core_file_uploads.file_validator is not None
    # Limits configured per the unification plan.
    limits = core_file_uploads.file_validator.config.limits
    assert limits.max_activity_file_size == 200 * 1024 * 1024
    assert limits.max_gzip_size == 200 * 1024 * 1024
    assert limits.max_uncompressed_size == 2 * 1024 * 1024 * 1024
    assert limits.enable_audit_logging is True


@pytest.mark.asyncio
async def test_failed_validation_emits_audit_record(caplog):
    """Rejected uploads emit a structured audit failure record."""
    upload = _upload("evil.png", b"this is not a png")
    caplog.set_level(logging.WARNING, logger="safeuploads.audit")

    with pytest.raises(HTTPException):
        try:
            await validate_upload(upload, kind=UploadKind.IMAGE)
        finally:
            await upload.close()

    failure_records = [
        record
        for record in caplog.records
        if getattr(record, "audit_event_type", "") == "validation_failure"
    ]
    assert len(failure_records) == 1
    assert getattr(failure_records[0], "audit_correlation_id")
