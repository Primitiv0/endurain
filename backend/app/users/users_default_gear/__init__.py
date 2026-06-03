"""
User default gear module for activity type gear assignments.

This module provides CRUD operations and data models for managing
user default gear settings per activity type (run, ride, swim, etc.).

Exports:
    - CRUD: get_user_default_gear_by_user_id,
      create_user_default_gear, edit_user_default_gear
    - Schemas: UsersDefaultGearBase, UsersDefaultGearUpdate,
      UsersDefaultGearRead
    - Models: UsersDefaultGear (ORM model)
    - Utils: get_user_default_gear_by_activity_type
    - Constants: ACTIVITY_TYPE_TO_GEAR_ATTR
"""

from .crud import (
    create_user_default_gear,
    edit_user_default_gear,
    get_user_default_gear_by_user_id,
)
from .models import UsersDefaultGear as UsersDefaultGearModel
from .schema import (
    UsersDefaultGearBase,
    UsersDefaultGearRead,
    UsersDefaultGearUpdate,
)
from .utils import (
    ACTIVITY_TYPE_TO_GEAR_ATTR,
    get_user_default_gear_by_activity_type,
)

__all__ = [
    # Constants
    "ACTIVITY_TYPE_TO_GEAR_ATTR",
    # Pydantic schemas
    "UsersDefaultGearBase",
    # Database model
    "UsersDefaultGearModel",
    "UsersDefaultGearRead",
    "UsersDefaultGearUpdate",
    "create_user_default_gear",
    "edit_user_default_gear",
    # Utility functions
    "get_user_default_gear_by_activity_type",
    # CRUD operations
    "get_user_default_gear_by_user_id",
]
