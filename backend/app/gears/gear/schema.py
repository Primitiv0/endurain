from pydantic import BaseModel, StrictInt, Field, ConfigDict

class Gear(BaseModel):
    id: int | None = None
    brand: str | None = None
    model: str | None = None
    nickname: str
    gear_type: int
    user_id: int | None = None
    created_at: str | None = None
    active: bool | None = None
    initial_kms: float | None = None
    purchase_value: float | None = None
    strava_gear_id: str | None = None
    garminconnect_gear_id: str | None = None

    model_config = {
        "from_attributes": True
    }

class GearsListResponse(BaseModel):
    """
    Response model for paginated gear listing.

    Attributes:
        total: Total number of gear records.
        num_records: Number of records in this response.
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
        description="Number of records in this response",
    )
    page_number: StrictInt | None = Field(
        default=None,
        ge=1,
        description="Current page number",
    )
    records: list[Gear] = Field(
        ...,
        description="List of gear records",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
    )