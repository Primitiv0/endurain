"""Tests for Strava bulk-import file handling."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

import strava.bulk_import_utils as bulk_import_utils
from core.file_uploads import UploadKind


@pytest.mark.asyncio
async def test_bulk_media_import_validates_before_move(monkeypatch):
    """Media import validates images before moving them into storage."""
    validate = AsyncMock()
    create_media = Mock()
    moves = []
    media_dir = "/tmp/activity-media"

    monkeypatch.setattr(bulk_import_utils.os.path, "exists", lambda _: True)
    monkeypatch.setattr(bulk_import_utils.os, "makedirs", Mock())
    monkeypatch.setattr(
        bulk_import_utils.core_config.settings,
        "ACTIVITY_MEDIA_DIR",
        media_dir,
        raising=False,
    )
    monkeypatch.setattr(
        bulk_import_utils.file_uploads, "validate_local_file", validate
    )
    monkeypatch.setattr(
        bulk_import_utils.file_uploads,
        "move_within",
        lambda src, dest, *, filename, src_base_dir=None: moves.append(
            (src, dest, filename, src_base_dir)
        ),
    )
    monkeypatch.setattr(
        bulk_import_utils.activity_media_crud,
        "create_activity_media",
        create_media,
    )

    await bulk_import_utils.create_activity_media_from_strava_bulk_import(
        7,
        "photo.jpg",
        "/tmp/strava/photo.jpg",
        Mock(),
    )

    validate.assert_awaited_once_with(
        "/tmp/strava/photo.jpg",
        kind=UploadKind.IMAGE,
        filename="photo.jpg",
    )
    assert moves == [
        (
            "/tmp/strava/photo.jpg",
            media_dir,
            "7_photo.jpg",
            bulk_import_utils.core_config.STRAVA_BULK_IMPORT_MEDIA_DIR,
        )
    ]
    create_media.assert_called_once()
    assert create_media.call_args.args[1] == os.path.join(
        media_dir, "7_photo.jpg"
    )


@pytest.mark.asyncio
async def test_bulk_media_import_rejects_invalid_image(monkeypatch):
    """Invalid media is rejected before move or DB insert."""
    validate = AsyncMock(
        side_effect=HTTPException(status_code=400, detail="bad image")
    )
    move = Mock()
    create_media = Mock()

    monkeypatch.setattr(bulk_import_utils.os.path, "exists", lambda _: True)
    monkeypatch.setattr(bulk_import_utils.os, "makedirs", Mock())
    monkeypatch.setattr(
        bulk_import_utils.file_uploads, "validate_local_file", validate
    )
    monkeypatch.setattr(bulk_import_utils.file_uploads, "move_within", move)
    monkeypatch.setattr(
        bulk_import_utils.activity_media_crud,
        "create_activity_media",
        create_media,
    )

    await bulk_import_utils.create_activity_media_from_strava_bulk_import(
        7,
        "photo.jpg",
        "/tmp/strava/photo.jpg",
        Mock(),
    )

    validate.assert_awaited_once()
    move.assert_not_called()
    create_media.assert_not_called()
