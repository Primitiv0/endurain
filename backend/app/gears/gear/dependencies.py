"""Gear dependency validators."""

import core.dependencies as core_dependencies


def validate_gear_id(gear_id: int) -> None:
    """
    Validate that gear_id is greater than zero.

    Args:
        gear_id: The ID of the gear to validate.

    Raises:
        HTTPException: If gear_id is invalid.
    """
    core_dependencies.validate_id(
        id=gear_id,
        min=0,
        message="Invalid gear ID",
    )


def validate_gear_type(gear_type: int) -> None:
    """
    Validate that gear_type is within 1 and 8.

    Args:
        gear_type: The type of gear to validate.

    Raises:
        HTTPException: If gear_type is invalid.
    """
    core_dependencies.validate_type(
        type=gear_type,
        min=1,
        max=8,
        message="Invalid gear type",
    )