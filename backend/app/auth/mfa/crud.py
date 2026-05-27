"""CRUD helpers for the ``users_mfa`` 1:1 companion table."""

from sqlalchemy.orm import Session

import auth.mfa.models as auth_mfa_models
import core.decorators as core_decorators


@core_decorators.handle_db_errors
def create_users_mfa_row(user_id: int, db: Session) -> auth_mfa_models.AuthUserMFA:
    """
    Create the default ``users_mfa`` row for a newly created user.

    MFA is disabled by default; the row exists so that the 1:1
    invariant between ``users`` and ``users_mfa`` holds for every
    user without relying on the defensive create-on-update branch
    in ``users.users.crud.update_user_mfa``.

    Args:
        user_id: ID of the user to create the row for.
        db: SQLAlchemy database session.

    Returns:
        The persisted ``AuthUserMFA`` row.

    Raises:
        HTTPException: 500 if the database operation fails.
    """
    mfa_row = auth_mfa_models.AuthUserMFA(
        user_id=user_id,
        mfa_enabled=False,
        mfa_secret=None,
    )
    db.add(mfa_row)
    db.commit()
    db.refresh(mfa_row)
    return mfa_row
