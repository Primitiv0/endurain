"""Dependencies for activity stream validation."""

import core.dependencies as core_dependencies


def validate_activity_stream_type(
    stream_type: int,
) -> None:
    """
    Validate the activity stream type value.

    Args:
        stream_type: The stream type to validate.

    Raises:
        HTTPException: If stream type is not 1-7.
    """
    core_dependencies.validate_type(
        type=stream_type,
        min=1,
        max=7,
        message=(
            "Invalid activity stream type"
        ),
    )