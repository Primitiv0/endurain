"""Migration 7: backfill pre-computed HR zone_percentages for existing streams."""

from sqlalchemy.orm import Session

import activities.activity_streams.crud as activity_streams_crud
import core.logger as core_logger
import migrations.crud as migrations_crud


async def process_migration_7(db: Session) -> None:
    """
    Backfill zone_percentages for existing HR streams.

    Args:
        db: The SQLAlchemy database session.

    Returns:
        None.
    """
    core_logger.print_to_log_and_console("Started migration 7")

    try:
        streams_processed_with_no_errors = activity_streams_crud.backfill_zone_percentages_for_missing_hr_streams(db)
    except Exception as err:
        streams_processed_with_no_errors = False
        core_logger.print_to_log_and_console(
            f"Migration 7 - Error fetching streams: {err}",
            "error",
            exc=err,
        )
        return

    if streams_processed_with_no_errors:
        try:
            migrations_crud.set_migration_as_executed(7, db)
        except Exception as err:
            core_logger.print_to_log_and_console(
                f"Migration 7 - Failed to set migration as executed: {err}",
                "error",
                exc=err,
            )
            return
    else:
        core_logger.print_to_log_and_console(
            "Migration 7 failed to process all streams. Will try again later.",
            "error",
        )

    core_logger.print_to_log_and_console("Finished migration 7")
