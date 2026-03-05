"""Gear schema definitions."""

from datetime import date as datetime_date

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
)


class GearBase(BaseModel):
    """
    Base model for gear data.

    Attributes:
        brand: Gear brand name.
        model: Gear model name.
        nickname: Gear display nickname.
        gear_type: Gear type identifier.
        created_at: Gear creation date.
        active: Whether the gear is active.
        initial_kms: Initial kilometers.
        purchase_value: Purchase value.
        strava_gear_id: Strava gear ID.
        garminconnect_gear_id: Garmin gear ID.
    """

    brand: StrictStr | None = Field(
        default=None,
        max_length=250,
        description="Gear brand name",
    )
    model: StrictStr | None = Field(
        default=None,
        max_length=250,
        description="Gear model name",
    )
    nickname: StrictStr = Field(
        ...,
        max_length=250,
        description="Gear display nickname",
    )
    gear_type: StrictInt = Field(
        ...,
        ge=1,
        le=8,
        description="Gear type identifier",
    )
    created_at: datetime_date | None = Field(
        default=None,
        description="Gear creation date",
    )
    active: StrictBool | None = Field(
        default=None,
        description="Whether the gear is active",
    )
    initial_kms: StrictFloat | None = Field(
        default=None,
        ge=0,
        description="Initial kilometers",
    )
    purchase_value: StrictFloat | None = Field(
        default=None,
        ge=0,
        description="Purchase value",
    )
    strava_gear_id: StrictStr | None = Field(
        default=None,
        max_length=45,
        description="Strava gear ID",
    )
    garminconnect_gear_id: StrictStr | None = Field(
        default=None,
        max_length=45,
        description="Garmin Connect gear ID",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
    )


class GearCreate(GearBase):
    """
    Schema for creating a gear record.

    Attributes:
        user_id: Foreign key to user.
    """

    user_id: StrictInt | None = Field(
        default=None,
        description="Foreign key to user",
    )


class GearRead(GearBase):
    """
    Schema for reading a gear record.

    Attributes:
        id: Unique identifier.
        user_id: Foreign key to user.
    """

    id: StrictInt = Field(
        ...,
        description="Unique identifier",
    )
    user_id: StrictInt = Field(
        ...,
        description="Foreign key to user",
    )


class GearUpdate(GearBase):
    """Schema for updating a gear record."""


class GearsListResponse(BaseModel):
    """
    Response model for paginated gear listing.

    Attributes:
        total: Total number of gear records.
        num_records: Number of records returned.
        page_number: Current page number.
        records: List of gear records.
    """

    total: StrictInt = Field(
        ...,
        ge=0,
        description="Total number of gear records",
    )
    num_records: StrictInt | None = Field(
        default=None,
        ge=0,
        description="Number of records returned",
    )
    page_number: StrictInt | None = Field(
        default=None,
        ge=1,
        description="Current page number",
    )
    records: list[GearRead] = Field(
        ...,
        description="List of gear records",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
    )