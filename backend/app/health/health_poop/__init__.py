"""
Health poop module for managing user bowel movement data.

This module provides CRUD operations and data models for user
bowel movement tracking including daily records, Bristol stool
scale type, and optional notes.

Exports:
    - CRUD: get_health_poop_number_by_user_id,
      get_health_poop_by_id_and_user_id,
      get_health_poop_by_user_id,
      get_health_poop_by_date_and_user_id,
      create_health_poop, edit_health_poop, delete_health_poop
    - Schemas: HealthPoopBase, HealthPoopCreate,
      HealthPoopUpdate, HealthPoopRead,
      HealthPoopListResponse
    - Enums: Source, BristolType
    - Models: HealthPoop (ORM model)
"""

from .crud import (
    get_health_poop_number_by_user_id,
    get_health_poop_by_id_and_user_id,
    get_health_poop_by_user_id,
    get_health_poop_by_date_and_user_id,
    create_health_poop,
    edit_health_poop,
    delete_health_poop,
)
from .models import HealthPoop as HealthPoopModel
from .schema import (
    HealthPoopBase,
    HealthPoopCreate,
    HealthPoopUpdate,
    HealthPoopRead,
    HealthPoopListResponse,
    Source,
    BristolType,
)

__all__ = [
    # CRUD operations
    "get_health_poop_number_by_user_id",
    "get_health_poop_by_id_and_user_id",
    "get_health_poop_by_user_id",
    "get_health_poop_by_date_and_user_id",
    "create_health_poop",
    "edit_health_poop",
    "delete_health_poop",
    # Database model
    "HealthPoopModel",
    # Pydantic schemas
    "HealthPoopBase",
    "HealthPoopCreate",
    "HealthPoopUpdate",
    "HealthPoopRead",
    "HealthPoopListResponse",
    # Enums
    "Source",
    "BristolType",
]
