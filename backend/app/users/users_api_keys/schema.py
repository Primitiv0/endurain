"""User API key schemas."""

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    StrictStr,
    StrictBool,
    field_validator,
)
from datetime import datetime

import auth.constants as auth_constants


class UsersApiKeyCreate(BaseModel):
    """
    Schema for creating a new API key.

    Attributes:
        name: User-friendly label for the key.
        scopes: List of scope strings to grant.
        expires_at: Optional expiration datetime.
            None means the key never expires.
    """

    name: StrictStr = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User-friendly label for the key",
    )
    scopes: list[StrictStr] = Field(
        ...,
        min_length=1,
        description="List of scope strings to grant",
    )
    expires_at: datetime | None = Field(
        None,
        description=(
            "Optional expiration datetime. " "None means the key never expires."
        ),
    )

    @field_validator("scopes")
    @classmethod
    def scopes_must_be_valid(cls, v: list[str]) -> list[str]:
        """
        Validate all scopes exist in the known scope dict.

        Args:
            v: List of scope strings to validate.

        Returns:
            Validated list of scope strings.

        Raises:
            ValueError: If any scope is not recognised.
        """
        known = set(auth_constants.SCOPE_DICT.keys())
        unknown = set(v) - known
        if unknown:
            raise ValueError(f"Unknown scopes: {unknown}. " f"Valid scopes: {known}")
        return v

    model_config = ConfigDict(from_attributes=True)


class UsersApiKeyRead(BaseModel):
    """
    API key read schema for list/detail responses.

    Never exposes the raw key or its hash. Safe to
    return in all authenticated GET responses.

    Attributes:
        id: Unique key identifier (UUID).
        user_id: Owner's user ID.
        name: User-friendly label.
        key_prefix: First 8 chars of the random part.
        scopes: JSON-encoded list of granted scopes.
        expires_at: Optional expiration timestamp.
        last_used_at: Last successful use timestamp.
        created_at: Key creation timestamp.
        is_active: Whether the key is currently active.
    """

    id: StrictStr = Field(..., description="Unique key identifier (UUID)")
    user_id: int = Field(..., ge=1, description="Owner's user ID")
    name: StrictStr = Field(..., description="User-friendly label")
    key_prefix: StrictStr = Field(..., description="First 8 chars of the random part")
    scopes: StrictStr = Field(..., description="JSON-encoded list of granted scopes")
    expires_at: datetime | None = Field(
        None, description="Optional expiration timestamp"
    )
    last_used_at: datetime | None = Field(
        None, description="Last successful use timestamp"
    )
    created_at: datetime = Field(..., description="Key creation timestamp")
    is_active: StrictBool = Field(
        ..., description="Whether the key is currently active"
    )

    model_config = ConfigDict(from_attributes=True)


class UsersApiKeyCreated(UsersApiKeyRead):
    """
    API key creation response schema.

    Extends UsersApiKeyRead with the raw key, returned
    only once at creation time. The raw key is never
    stored and cannot be retrieved again.

    Attributes:
        key: The full raw API key. Show to the user
            once and discard.
    """

    key: StrictStr = Field(
        ...,
        description=(
            "Full raw API key. Shown once at creation " "only — store it securely."
        ),
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )
