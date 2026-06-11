"""Core decorators project wide."""

from collections.abc import Callable
from functools import wraps
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import core.logger as core_logger


def handle_db_errors[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to handle SQLAlchemy database errors consistently.

    Catches SQLAlchemyError exceptions, logs them, and converts to
    HTTPException with 500 status. Allows HTTPException and
    IntegrityError to pass through for function-specific handling.

    Automatically calls rollback on the database session if found
    in function parameters.

    Args:
        func: The CRUD function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except (SQLAlchemyError, IntegrityError) as db_err:
            # Find any Session instance
            db_session = None

            for value in list(args) + list(kwargs.values()):
                if isinstance(value, Session):
                    db_session = value
                    break

            if db_session is not None:
                try:
                    cast(Session, db_session).rollback()
                except Exception as rollback_err:
                    # Surface rollback failures: a silent
                    # failure here means the session may
                    # leak partial state into subsequent
                    # operations on the same connection.
                    core_logger.print_to_log(
                        f"Rollback failed in {func.__name__}: {type(rollback_err).__name__}",
                        "error",
                        exc=rollback_err,
                    )

            # Log only the exception class name — SQLAlchemy
            # error strings frequently embed the offending
            # SQL statement and parameter values, which can
            # leak PII / credentials into logs (OWASP A09).
            core_logger.print_to_log(
                f"Database error in {func.__name__}: {type(db_err).__name__}",
                "error",
                exc=db_err,
            )

            # Let IntegrityError bubble if you want custom handling upstream
            if isinstance(db_err, IntegrityError):
                raise

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            ) from db_err

    return wrapper
