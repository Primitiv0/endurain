"""
Gear components sub-module.

Provides CRUD operations, schemas, and models
for gear component tracking (e.g., chains, tires,
pedals, strings).

Exports:
    - CRUD: get_gear_component_by_id,
      get_gear_components_user,
      get_gear_components_user_by_gear_id,
      create_gear_component,
      edit_gear_component,
      delete_gear_component
    - Schemas: GearComponentBase,
      GearComponentCreate, GearComponentRead,
      GearComponentUpdate, GearComponentTypesRead
    - Models: GearComponents (ORM model)
"""

from .crud import (
    get_gear_component_by_id,
    get_gear_components_user,
    get_gear_components_user_by_gear_id,
    create_gear_component,
    edit_gear_component,
    delete_gear_component,
)
from .models import GearComponents
from .schema import (
    GearComponentBase,
    GearComponentCreate,
    GearComponentRead,
    GearComponentUpdate,
    GearComponentTypesRead,
)

__all__ = [
    # CRUD operations
    "get_gear_component_by_id",
    "get_gear_components_user",
    "get_gear_components_user_by_gear_id",
    "create_gear_component",
    "edit_gear_component",
    "delete_gear_component",
    # Database model
    "GearComponents",
    # Pydantic schemas
    "GearComponentBase",
    "GearComponentCreate",
    "GearComponentRead",
    "GearComponentUpdate",
    "GearComponentTypesRead",
]
