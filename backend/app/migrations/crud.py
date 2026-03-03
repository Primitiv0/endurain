"""CRUD operations for migration tracking."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import migrations.models as migrations_models

import core.decorators as core_decorators


@core_decorators.handle_db_errors
def get_migrations_not_executed(
    db: Session,
) -> list[migrations_models.Migration] | None:
    """
    Retrieve all unexecuted migrations.

    Args:
        db: Database session.

    Returns:
        List of unexecuted Migration models, or None if all migrations are
            executed.

    Raises:
        HTTPException: 500 error on database failure.
    """
    stmt = select(migrations_models.Migration).where(
        migrations_models.Migration.executed.is_(False)
    )
    results = db.execute(stmt).scalars().all()
    return results if results else None


@core_decorators.handle_db_errors
def set_migration_as_executed(
    migration_id: int,
    db: Session,
) -> None:
    """
    Mark a migration as executed by its ID.

    Args:
        migration_id: ID of the migration to mark as executed.
        db: Database session.

    Returns:
        None.

    Raises:
        HTTPException: 404 if migration not found.
        HTTPException: 500 error on database failure.
    """
    stmt = select(migrations_models.Migration).where(
        migrations_models.Migration.id == migration_id
    )
    db_migration = db.execute(stmt).scalar_one_or_none()

    if db_migration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migration not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_migration.executed = True
    db.commit()
    db.refresh(db_migration)
