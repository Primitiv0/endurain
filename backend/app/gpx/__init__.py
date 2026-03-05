"""
GPX file parsing module for Endurain.

This module provides utilities to parse GPX activity files into structured
activity data including waypoints, laps, and associated metadata.

Exports:
    - Utils: parse_gpx_file, generate_activity_laps
"""

from .utils import generate_activity_laps, parse_gpx_file

__all__ = [
    # Utilities
    "parse_gpx_file",
    "generate_activity_laps",
]
