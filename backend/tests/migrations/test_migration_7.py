from unittest.mock import MagicMock, patch

import pytest

import migrations.migration_7 as migration_7


@pytest.mark.asyncio
async def test_process_migration_7_populates_missing_hr_zone_percentages(mock_db):
    stream = MagicMock(
        id=1,
        activity_id=10,
        stream_type=1,
        zone_percentages=None,
        stream_waypoints=[{"hr": 120}],
    )

    mock_db.scalars.return_value.all.side_effect = [[stream], []]

    with (
        patch(
            "migrations.migration_7.activity_streams_crud.backfill_zone_percentages_for_missing_hr_streams",
            return_value=True,
        ) as mock_backfill,
        patch("migrations.migration_7.migrations_crud.set_migration_as_executed") as mock_set_executed,
    ):
        await migration_7.process_migration_7(mock_db)

    mock_backfill.assert_called_once_with(mock_db)
    mock_set_executed.assert_called_once_with(7, mock_db)


@pytest.mark.asyncio
async def test_process_migration_7_skips_existing_zone_percentages(mock_db):
    existing_payload = {"hr": {"zone_1": {"percent": 50.0}}}
    stream = MagicMock(
        id=2,
        activity_id=20,
        stream_type=1,
        zone_percentages=existing_payload,
        stream_waypoints=[{"hr": 100}],
    )

    mock_db.scalars.return_value.all.side_effect = [[stream], []]

    with (
        patch(
            "migrations.migration_7.activity_streams_crud.backfill_zone_percentages_for_missing_hr_streams",
            return_value=True,
        ) as mock_backfill,
        patch("migrations.migration_7.migrations_crud.set_migration_as_executed") as mock_set_executed,
    ):
        await migration_7.process_migration_7(mock_db)

    mock_backfill.assert_called_once_with(mock_db)
    mock_set_executed.assert_called_once_with(7, mock_db)
