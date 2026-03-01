"""
TCX file parsing module for Endurain.

This module provides utilities to parse TCX activity files
into structured activity data including waypoints, laps,
and associated metadata.

Exports:
    - Utils: parse_tcx_file
"""

from .utils import parse_tcx_file

__all__ = [
    # Utilities
    "parse_tcx_file",
]
