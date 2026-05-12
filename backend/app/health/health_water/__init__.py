"""
Health water intake module for managing user hydration data.

This module provides CRUD operations and data models for user
water intake tracking including daily consumption amounts and
data sources.

Exports:
    - CRUD: get_health_water_number_by_user_id,
      get_health_water_by_id_and_user_id,
      get_health_water_by_user_id,
      get_health_water_by_date_and_user_id,
      create_health_water, edit_health_water, delete_health_water
    - Schemas: HealthWaterBase, HealthWaterCreate,
      HealthWaterUpdate, HealthWaterRead,
      HealthWaterListResponse
    - Enums: Source
    - Models: HealthWater (ORM model)
"""

from .crud import (
    get_health_water_number_by_user_id,
    get_health_water_by_id_and_user_id,
    get_health_water_by_user_id,
    get_health_water_by_date_and_user_id,
    create_health_water,
    edit_health_water,
    delete_health_water,
)
from .models import HealthWater as HealthWaterModel
from .schema import (
    HealthWaterBase,
    HealthWaterCreate,
    HealthWaterUpdate,
    HealthWaterRead,
    HealthWaterListResponse,
    Source,
)

__all__ = [
    # CRUD operations
    "get_health_water_number_by_user_id",
    "get_health_water_by_id_and_user_id",
    "get_health_water_by_user_id",
    "get_health_water_by_date_and_user_id",
    "create_health_water",
    "edit_health_water",
    "delete_health_water",
    # Database model
    "HealthWaterModel",
    # Pydantic schemas
    "HealthWaterBase",
    "HealthWaterCreate",
    "HealthWaterUpdate",
    "HealthWaterRead",
    "HealthWaterListResponse",
    # Enums
    "Source",
]
