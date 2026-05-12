"""
Migration schema definitions.

Note: StreamType is defined here for historical reasons and is used by
migration scripts. It describes activity stream data types.
"""

from enum import Enum


class StreamType(Enum):
    """
    Activity data stream type enumeration.

    Attributes:
        HEART_RATE: Heart rate data stream.
        POWER: Power output data stream.
        CADENCE: Cadence data stream.
        ELEVATION: Elevation data stream.
        SPEED: Speed data stream.
        PACE: Pace data stream.
        LATLONG: Latitude/longitude data stream.
    """

    HEART_RATE = 1
    POWER = 2
    CADENCE = 3
    ELEVATION = 4
    SPEED = 5
    PACE = 6
    LATLONG = 7
