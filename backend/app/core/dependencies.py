"""Shared validation dependencies for FastAPI routers."""

from typing import Annotated

from fastapi import HTTPException, Query, status


def validate_id(id: int, min: int, message: str) -> None:
    """
    Validate that an integer identifier is above a minimum.

    Args:
        id: Identifier value to validate.
        min: Minimum exclusive value.
        message: Error detail for invalid values.

    Returns:
        None.

    Raises:
        HTTPException: If the value is not above the minimum.
    """
    if not (int(id) > min):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


def validate_type(type: int, min: int, max: int, message: str) -> None:
    """
    Validate that an integer type is inside an inclusive range.

    Args:
        type: Type value to validate.
        min: Minimum inclusive value.
        max: Maximum inclusive value.
        message: Error detail for invalid values.

    Returns:
        None.

    Raises:
        HTTPException: If the value is outside the range.
    """
    if not (min <= int(type) <= max):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


def validate_pagination_values(
    page_number: int,
    num_records: int,
) -> None:
    """
    Validate pagination arguments supplied by callers.

    Args:
        page_number: One-based page number.
        num_records: Number of records per page.

    Returns:
        None.

    Raises:
        HTTPException: If either value is less than one.
    """
    if not (int(page_number) > 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid page number, must be higher than 0",
        )

    if not (int(num_records) > 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid number of records, must be higher than 0",
        )


def validate_pagination_values_on_query(
    page_number: Annotated[
        int | None,
        Query(description="Pagination page number"),
    ] = None,
    num_records: Annotated[
        int | None,
        Query(description="Number of records per page"),
    ] = None,
) -> None:
    """
    Validate optional pagination query parameters.

    Args:
        page_number: One-based page number, when supplied.
        num_records: Number of records per page, when supplied.

    Returns:
        None.

    Raises:
        HTTPException: If either supplied value is less than one.
    """
    if page_number is None or num_records is None:
        return

    if not (int(page_number) > 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid page number, must be higher than 0",
        )

    if not (int(num_records) > 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid number of records, must be higher than 0",
        )
