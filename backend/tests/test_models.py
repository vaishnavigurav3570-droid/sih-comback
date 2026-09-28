"""
Tests for StormFusion AI — Core Data Models

Verifies that all Pydantic models work correctly:
- Can be created with valid data
- Reject invalid data
- Serialize/deserialize properly
"""

from datetime import datetime, timezone

import pytest
from backend.app.models.data_types import (
    INDIA_BBOX,
    BoundingBox,
    DataSourceStatus,
    DataSourceType,
    ForecastLeadTime,
    StormMovementVector,
)
from backend.app.models.forecast import (
    GridCellForecast,
)
from backend.app.models.metadata import ConnectionStatus, DatasetMetadata

# ============================================================
# BoundingBox Tests
# ============================================================


class TestBoundingBox:
    """Test the BoundingBox model."""

    def test_create_valid_bbox(self):
        """Can create a bounding box with valid coordinates."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.west == 68.0
        assert bbox.south == 6.0
        assert bbox.east == 98.0
        assert bbox.north == 38.0

    def test_as_tuple(self):
        """The as_tuple property returns (west, south, east, north)."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.as_tuple == (68.0, 6.0, 98.0, 38.0)

    def test_center_coordinates(self):
        """Center lat/lon are computed correctly."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.center_lat == 22.0
        assert bbox.center_lon == 83.0

    def test_contains_point_inside(self):
        """A point inside the box returns True."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.contains_point(22.0, 83.0) is True

    def test_contains_point_outside(self):
        """A point outside the box returns False."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.contains_point(50.0, 83.0) is False

    def test_contains_point_on_edge(self):
        """A point on the edge of the box returns True."""
        bbox = BoundingBox(west=68.0, south=6.0, east=98.0, north=38.0)
        assert bbox.contains_point(6.0, 68.0) is True

    def test_india_bbox_constant(self):
        """The INDIA_BBOX constant has correct values."""
        assert INDIA_BBOX.west == 68.0
        assert INDIA_BBOX.south == 6.0
        assert INDIA_BBOX.east == 98.0
        assert INDIA_BBOX.north == 38.0


# ============================================================
# Enum Tests
# ============================================================


class TestEnums:
    """Test all enum types."""

    def test_data_source_type_values(self):
        """DataSourceType has all expected values."""
        assert DataSourceType.SATELLITE == "satellite"
        assert DataSourceType.RADAR == "radar"
        assert DataSourceType.LIGHTNING == "lightning"
        assert DataSourceType.NWP == "nwp"
        assert DataSourceType.SURFACE_STATION == "surface_station"
        assert DataSourceType.SYNTHETIC == "synthetic"

    def test_data_source_status_values(self):
        """DataSourceStatus has all expected values."""
        assert DataSourceStatus.OK == "ok"
        assert DataSourceStatus.DEGRADED == "degraded"
        assert DataSourceStatus.UNAVAILABLE == "unavailable"
        assert DataSourceStatus.SYNTHETIC_FALLBACK == "synthetic_fallback"

    def test_forecast_lead_time_minutes(self):
        """ForecastLeadTime.minutes property works correctly."""
        assert ForecastLeadTime.PLUS_15.minutes == 15
        assert ForecastLeadTime.PLUS_30.minutes == 30
        assert ForecastLeadTime.PLUS_60.minutes == 60
        assert ForecastLeadTime.PLUS_90.minutes == 90


# ============================================================
# StormMovementVector Tests
# ============================================================


class TestStormMovementVector:
    """Test the StormMovementVector model."""

    def test_valid_vector(self):
        """Can create a valid movement vector."""
        vec = StormMovementVector(speed_kmh=45.0, direction_degrees=270.0)
        assert vec.speed_kmh == 45.0
        assert vec.direction_degrees == 270.0

    def test_negative_speed_rejected(self):
        """Negative speed should be rejected."""
        with pytest.raises(Exception):
            StormMovementVector(speed_kmh=-10.0, direction_degrees=90.0)

    def test_direction_out_of_range_rejected(self):
        """Direction >= 360 should be rejected."""
        with pytest.raises(Exception):
            StormMovementVector(speed_kmh=10.0, direction_degrees=360.0)


# ============================================================
# DatasetMetadata Tests
# ============================================================


class TestDatasetMetadata:
    """Test the DatasetMetadata model."""

    def test_create_valid_metadata(self):
        """Can create valid dataset metadata."""
        now = datetime.now(timezone.utc)
        meta = DatasetMetadata(
            dataset_id="test_001",
            source_type=DataSourceType.SATELLITE,
            source_name="TestSource",
            variable_name="bt_tir1",
            units="K",
            time_start=now,
            time_end=now,
            bounding_box=INDIA_BBOX,
            is_synthetic=True,
        )
        assert meta.dataset_id == "test_001"
        assert meta.is_synthetic is True
        assert meta.source_type == DataSourceType.SATELLITE

    def test_synthetic_flag_defaults_false(self):
        """is_synthetic defaults to False (conservative default)."""
        now = datetime.now(timezone.utc)
        meta = DatasetMetadata(
            dataset_id="test_002",
            source_type=DataSourceType.RADAR,
            source_name="RealRadar",
            variable_name="reflectivity",
            units="dBZ",
            time_start=now,
            time_end=now,
            bounding_box=INDIA_BBOX,
        )
        assert meta.is_synthetic is False


# ============================================================
# GridCellForecast Tests
# ============================================================


class TestGridCellForecast:
    """Test the GridCellForecast model."""

    def test_valid_forecast(self):
        """Can create a valid grid cell forecast."""
        fc = GridCellForecast(
            latitude=22.0,
            longitude=80.0,
            lead_time=ForecastLeadTime.PLUS_30,
            thunderstorm_probability=0.75,
            lightning_probability=0.60,
            storm_intensity=3.0,
            confidence=0.80,
            is_synthetic=True,
        )
        assert fc.thunderstorm_probability == 0.75
        assert fc.is_synthetic is True

    def test_probability_bounds(self):
        """Probabilities must be between 0.0 and 1.0."""
        with pytest.raises(Exception):
            GridCellForecast(
                latitude=22.0,
                longitude=80.0,
                lead_time=ForecastLeadTime.PLUS_30,
                thunderstorm_probability=1.5,  # Invalid!
                lightning_probability=0.60,
                storm_intensity=3.0,
                confidence=0.80,
                is_synthetic=True,
            )


# ============================================================
# ConnectionStatus Tests
# ============================================================


class TestConnectionStatus:
    """Test the ConnectionStatus model."""

    def test_healthy_connection(self):
        """Can create a healthy connection status."""
        now = datetime.now(timezone.utc)
        status = ConnectionStatus(
            source_type=DataSourceType.SATELLITE,
            status=DataSourceStatus.OK,
            is_connected=True,
            message="All good",
            latency_ms=42.5,
            checked_at=now,
        )
        assert status.is_connected is True
        assert status.latency_ms == 42.5
