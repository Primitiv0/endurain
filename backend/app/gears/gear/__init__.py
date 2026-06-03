"""
Gear module for managing user equipment.

This module provides CRUD operations and data models
for user gear tracking including bikes, shoes, wetsuits,
racquets, skis, snowboards, windsurf, and water sports
equipment.

Exports:
    - CRUD: get_gear_user_by_id, get_gears_number,
      get_gear_users_with_pagination, get_gear_user,
      get_gear_user_contains_nickname,
      get_gear_user_by_nickname,
      get_gear_by_type_and_user,
      get_gear_by_strava_id_from_user_id,
      get_gear_by_garminconnect_id_from_user_id,
      create_multiple_gears, create_gear,
      edit_gear, delete_gear,
      delete_all_strava_gear_for_user,
      delete_all_garminconnect_gear_for_user
    - Schemas: GearBase, GearCreate, GearRead,
      GearUpdate, GearsListResponse
    - Models: Gear (ORM model)
    - Utils: transform_schema_gear_to_model_gear,
      GEAR_ID_TO_NAME, GEAR_NAME_TO_ID
"""

from .crud import (
    create_gear,
    create_multiple_gears,
    delete_all_garminconnect_gear_for_user,
    delete_all_strava_gear_for_user,
    delete_gear,
    edit_gear,
    get_gear_by_garminconnect_id_from_user_id,
    get_gear_by_strava_id_from_user_id,
    get_gear_by_type_and_user,
    get_gear_user,
    get_gear_user_by_id,
    get_gear_user_by_nickname,
    get_gear_user_contains_nickname,
    get_gear_users_with_pagination,
    get_gears_number,
)
from .models import Gear as GearModel
from .schema import (
    GearBase,
    GearCreate,
    GearRead,
    GearsListResponse,
    GearUpdate,
)
from .utils import (
    GEAR_ID_TO_NAME,
    GEAR_NAME_TO_ID,
    transform_schema_gear_to_model_gear,
)

__all__ = [
    "GEAR_ID_TO_NAME",
    "GEAR_NAME_TO_ID",
    # Pydantic schemas
    "GearBase",
    "GearCreate",
    # Database model
    "GearModel",
    "GearRead",
    "GearUpdate",
    "GearsListResponse",
    "create_gear",
    "create_multiple_gears",
    "delete_all_garminconnect_gear_for_user",
    "delete_all_strava_gear_for_user",
    "delete_gear",
    "edit_gear",
    "get_gear_by_garminconnect_id_from_user_id",
    "get_gear_by_strava_id_from_user_id",
    "get_gear_by_type_and_user",
    "get_gear_user",
    # CRUD operations
    "get_gear_user_by_id",
    "get_gear_user_by_nickname",
    "get_gear_user_contains_nickname",
    "get_gear_users_with_pagination",
    "get_gears_number",
    # Utilities
    "transform_schema_gear_to_model_gear",
]
