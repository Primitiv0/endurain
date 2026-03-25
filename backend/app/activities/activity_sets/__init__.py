"""
Activity sets module for workout set management.

This module provides CRUD operations and data models
for activity workout sets including duration, repetitions,
weight, and exercise categorization.

Exports:
    - CRUD: get_activity_sets, get_activities_sets,
      get_public_activity_sets, create_activity_sets
    - Schemas: ActivitySetsBase, ActivitySetsCreate,
      ActivitySetsRead
    - Models: ActivitySets (ORM model)
"""

from .crud import (
    get_activity_sets,
    get_activities_sets,
    get_public_activity_sets,
    create_activity_sets,
)
from .models import ActivitySets as ActivitySetsModel
from .schema import (
    ActivitySetsBase,
    ActivitySetsCreate,
    ActivitySetsRead,
)

__all__ = [
    # CRUD operations
    "get_activity_sets",
    "get_activities_sets",
    "get_public_activity_sets",
    "create_activity_sets",
    # Database model
    "ActivitySetsModel",
    # Pydantic schemas
    "ActivitySetsBase",
    "ActivitySetsCreate",
    "ActivitySetsRead",
]
