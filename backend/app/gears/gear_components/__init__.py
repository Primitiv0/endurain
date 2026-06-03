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
    create_gear_component,
    delete_gear_component,
    edit_gear_component,
    get_gear_component_by_id,
    get_gear_components_user,
    get_gear_components_user_by_gear_id,
)
from .models import GearComponents
from .schema import (
    GearComponentBase,
    GearComponentCreate,
    GearComponentRead,
    GearComponentTypesRead,
    GearComponentUpdate,
)

__all__ = [
    # Pydantic schemas
    "GearComponentBase",
    "GearComponentCreate",
    "GearComponentRead",
    "GearComponentTypesRead",
    "GearComponentUpdate",
    # Database model
    "GearComponents",
    "create_gear_component",
    "delete_gear_component",
    "edit_gear_component",
    # CRUD operations
    "get_gear_component_by_id",
    "get_gear_components_user",
    "get_gear_components_user_by_gear_id",
]
