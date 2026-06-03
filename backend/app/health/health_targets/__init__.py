"""
Health targets module for managing user health goals.

This module provides CRUD operations and data models for user
health targets including weight, steps, and sleep goals.

Exports:
    - CRUD: get_health_targets_by_user_id, create_health_targets,
      edit_health_target
    - Schemas: HealthTargetsBase, HealthTargetsUpdate,
      HealthTargetsRead
    - Models: HealthTargets (ORM model)
"""

from .crud import (
    create_health_targets,
    edit_health_target,
    get_health_targets_by_user_id,
)
from .models import HealthTargets as HealthTargetsModel
from .schema import (
    HealthTargetsBase,
    HealthTargetsRead,
    HealthTargetsUpdate,
)

__all__ = [
    # Pydantic schemas
    "HealthTargetsBase",
    # Database model
    "HealthTargetsModel",
    "HealthTargetsRead",
    "HealthTargetsUpdate",
    "create_health_targets",
    "edit_health_target",
    # CRUD operations
    "get_health_targets_by_user_id",
]
