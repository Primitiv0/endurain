"""Utility helpers for gear operations."""

from urllib.parse import unquote

from sqlalchemy import func

import gears.gear.models as gears_models
import gears.gear.schema as gears_schema

# Global gear type integer to gear name mapping (ID to name)
GEAR_ID_TO_NAME = {
    1: "bike",
    2: "shoes",
    3: "wetsuit",
    4: "racquet",
    5: "ski",
    6: "snowboard",
    7: "windsurf",
    8: "water_sports_board",
}

# Reverse gear type mapping, using the ID-to-name
# dictionary to create a name-to-ID dictionary.
GEAR_NAME_TO_ID = {
    name.lower(): id
    for id, name in GEAR_ID_TO_NAME.items()
}

# Additional variations on gear names for importing:
GEAR_NAME_TO_ID.update(
    {
        "bike": 1,
        "bicycle": 1,
        "shoes": 2,
        "racket": 4,
        "racquet": 4,
        "ski": 5,
        "skis": 5,
        "snowboard": 6,
        "windsurf": 7,
        "water_sports_board": 8,
        "surf_board": 8,
        "stand_up_paddling_board": 8,
    }
)


def transform_schema_gear_to_model_gear(
    gear: gears_schema.GearCreate, user_id: int
) -> gears_models.Gear:
    """
    Convert a gear schema to a gear ORM model.

    Args:
        gear: Gear creation schema instance.
        user_id: ID of the owning user.

    Returns:
        New gear ORM model instance.
    """
    # Set the created date to now
    created_date = func.now()

    # If created_at is provided, use it instead
    if gear.created_at is not None:
        created_date = gear.created_at

    # Create a new gear object
    new_gear = gears_models.Gear(
        brand=(
            unquote(gear.brand).replace("+", " ").strip()
            if gear.brand is not None
            else None
        ),
        model=(
            unquote(gear.model).replace("+", " ").strip()
            if gear.model is not None
            else None
        ),
        nickname=(
            unquote(gear.nickname)
            .replace("+", " ")
            .strip()
        ),
        gear_type=gear.gear_type,
        user_id=user_id,
        created_at=created_date,
        active=gear.active,
        initial_kms=gear.initial_kms,
        purchase_value=gear.purchase_value,
        strava_gear_id=gear.strava_gear_id,
        garminconnect_gear_id=(
            gear.garminconnect_gear_id
        ),
    )

    return new_gear
