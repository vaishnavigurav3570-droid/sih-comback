"""
StormFusion AI — Core Data Types

Enums and basic value objects used across the entire application.
These are the building blocks — other models import from here.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# ============================================================
# Enums
# ============================================================


class DataSourceType(str, Enum):
    """
    All supported data source types.

    Each type corresponds to a different kind of atmospheric observation.
    """

    SATELLITE = "satellite"
    RADAR = "radar"
    LIGHTNING = "lightning"
    NWP = "nwp"
    SURFACE_STATION = "surface_station"
    SYNTHETIC = "synthetic"


class DataSourceStatus(str, Enum):
    """Health status of a data source."""

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    SYNTHETIC_FALLBACK = "synthetic_fallback"


class ForecastLeadTime(str, Enum):
    """
    Supported forecast lead times.

    These are the time horizons for predictions:
    +15 min, +30 min, +60 min, +90 min.
    """

    PLUS_15 = "+15min"
    PLUS_30 = "+30min"
    PLUS_60 = "+60min"
    PLUS_90 = "+90min"

    @property
    def minutes(self) -> int:
        """Get the lead time in minutes as an integer."""
        mapping = {
            "+15min": 15,
            "+30min": 30,
            "+60min": 60,
            "+90min": 90,
        }
        return mapping[self.value]


# ============================================================
# Value Objects
# ============================================================


class BoundingBox(BaseModel):
    """
    Geographic bounding box in decimal degrees (WGS84).

    Think of it as drawing a rectangle on a map:
    - west/east = left/right edges (longitude)
    - south/north = bottom/top edges (latitude)

    Example for India: BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
    """

    west: float = Field(..., description="Western longitude (left edge)")
    south: float = Field(..., description="Southern latitude (bottom edge)")
    east: float = Field(..., description="Eastern longitude (right edge)")
    north: float = Field(..., description="Northern latitude (top edge)")

    @property
    def as_tuple(self) -> tuple[float, float, float, float]:
        """Return as (west, south, east, north) tuple."""
        return (self.west, self.south, self.east, self.north)

    @property
    def center_lat(self) -> float:
        """Latitude of the center of the bounding box."""
        return (self.south + self.north) / 2.0

    @property
    def center_lon(self) -> float:
        """Longitude of the center of the bounding box."""
        return (self.west + self.east) / 2.0

    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if a lat/lon point is inside this bounding box."""
        return self.south <= lat <= self.north and self.west <= lon <= self.east


class StormMovementVector(BaseModel):
    """
    Direction and speed of storm movement.

    Uses meteorological convention:
    - direction_degrees: 0=North, 90=East, 180=South, 270=West
      (the direction the storm is MOVING TOWARD)
    - speed_kmh: speed in km/h
    """

    speed_kmh: float = Field(..., ge=0, description="Storm speed in km/h")
    direction_degrees: float = Field(
        ...,
        ge=0,
        lt=360,
        description="Direction storm is moving toward (meteorological degrees)",
    )


# ============================================================
# Default Constants
# ============================================================

# Default bounding box covering all of India
INDIA_BBOX = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)

# All supported lead times
ALL_LEAD_TIMES = list(ForecastLeadTime)
