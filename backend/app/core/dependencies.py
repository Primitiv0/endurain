from typing import Annotated

from fastapi import HTTPException, status, Query


def validate_id(id: int, min: int, message: str):
    # Check if id higher than 0
    if not (int(id) > min):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


def validate_type(type: int, min: int, max: id, message: str):
    # Check if gear_type is between min and max
    if not (min <= int(type) <= max):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        )


def validate_pagination_values(
    page_number: int,
    num_records: int,
):
    # Check if page_number higher than 0
    if not (int(page_number) > 0):
        # Raise an HTTPException with a 422 Unprocessable Entity status code
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid page number, must be higher than 0",
        )

    # Check if num_records higher than 0
    if not (int(num_records) > 0):
        # Raise an HTTPException with a 422 Unprocessable Entity status code
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
):
    if page_number is None or num_records is None:
        return

    # Check if page_number higher than 0
    if not (int(page_number) > 0):
        # Raise an HTTPException with a 422 Unprocessable Entity status code
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid page number, must be higher than 0",
        )

    # Check if num_records higher than 0
    if not (int(num_records) > 0):
        # Raise an HTTPException with a 422 Unprocessable Entity status code
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid number of records, must be higher than 0",
        )
