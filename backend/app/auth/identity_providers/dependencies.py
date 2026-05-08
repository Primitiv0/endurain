"""Identity provider-specific request validation dependencies."""

import core.dependencies as core_dependencies


def validate_idp_id(idp_id: int) -> None:
    """
    Validate that identity provider ID is positive.

    Args:
        idp_id: Identity provider ID to validate.

    Returns:
        None

    Raises:
        HTTPException: 400 if identity provider ID is invalid (≤ 0).
    """
    core_dependencies.validate_id(
        id=idp_id, min=0, message="Invalid identity provider ID"
    )
