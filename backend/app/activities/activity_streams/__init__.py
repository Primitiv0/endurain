"""
Activity streams module for stream data management.

This module provides activity stream data operations,
including retrieval, creation, and transformation of
heart rate, power, cadence, elevation, speed, pace,
and map streams.

Exports:
    - CRUD: get_activity_streams,
      get_activities_streams,
      get_public_activity_streams,
      get_activity_stream_by_type,
      get_public_activity_stream_by_type,
      create_activity_streams
    - Utils: transform_activity_streams,
      transform_activity_streams_hr,
      is_stream_hidden, filter_visible_streams
    - Schemas: ActivityStreams
    - Models: ActivityStreams (ORM model)
    - Constants: STREAM_TYPE_HR, STREAM_TYPE_POWER,
      STREAM_TYPE_CADENCE, STREAM_TYPE_ELEVATION,
      STREAM_TYPE_SPEED, STREAM_TYPE_PACE,
      STREAM_TYPE_MAP
"""

from .crud import (
    get_activity_streams,
    get_activities_streams,
    get_public_activity_streams,
    get_activity_stream_by_type,
    get_public_activity_stream_by_type,
    create_activity_streams,
)
from .utils import (
    transform_activity_streams,
    transform_activity_streams_hr,
    is_stream_hidden,
    filter_visible_streams,
)
from .models import (
    ActivityStreams as ActivityStreamsModel,
)
from .schema import (
    ActivityStreams,
)
from .constants import (
    STREAM_TYPE_HR,
    STREAM_TYPE_POWER,
    STREAM_TYPE_CADENCE,
    STREAM_TYPE_ELEVATION,
    STREAM_TYPE_SPEED,
    STREAM_TYPE_PACE,
    STREAM_TYPE_MAP,
)

__all__ = [
    # CRUD operations
    "get_activity_streams",
    "get_activities_streams",
    "get_public_activity_streams",
    "get_activity_stream_by_type",
    "get_public_activity_stream_by_type",
    "create_activity_streams",
    # Utility functions
    "transform_activity_streams",
    "transform_activity_streams_hr",
    "is_stream_hidden",
    "filter_visible_streams",
    # Database model
    "ActivityStreamsModel",
    # Pydantic schemas
    "ActivityStreams",
    # Constants
    "STREAM_TYPE_HR",
    "STREAM_TYPE_POWER",
    "STREAM_TYPE_CADENCE",
    "STREAM_TYPE_ELEVATION",
    "STREAM_TYPE_SPEED",
    "STREAM_TYPE_PACE",
    "STREAM_TYPE_MAP",
]
