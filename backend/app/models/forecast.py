"""
StormFusion AI — Forecast Output Models

Defines the structure of forecast products — what the prediction engine
produces and what the API serves to the dashboard.
"""

from __future__ import annotations

from datetime import datetime

from backend.app.models.data_types import (
    BoundingBox,
    DataSourceStatus,
    DataSourceType,
    ForecastLeadTime,
    StormMovementVector,
)
from pydantic import BaseModel, Field


class SensorHealth(BaseModel):
    """
    Health status of a single data source during a forecast run.

    Tells the user: "Was radar data available? Was satellite data fresh?"
    """

    source_type: DataSourceType = Field(..., description="Which data source")
    status: DataSourceStatus = Field(
        ...,
        description="Current health (ok, degraded, unavailable, synthetic_fallback)",
    )
    last_data_time: datetime | None = Field(
        default=None, description="When the last real data was received (UTC)"
    )
    message: str = Field(
        ..., description="Human-readable status (e.g., 'Radar data is 5 min old')"
    )


class GridCellForecast(BaseModel):
    """
    Forecast for a single grid cell at a single lead time.

    This is the atomic unit of prediction — one location, one time horizon.
    """

    latitude: float = Field(..., description="Grid cell center latitude")
    longitude: float = Field(..., description="Grid cell center longitude")
    lead_time: ForecastLeadTime = Field(
        ..., description="Forecast horizon (e.g., +30min)"
    )
    thunderstorm_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of thunderstorm (0.0–1.0)"
    )
    lightning_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of lightning (0.0–1.0)"
    )
    storm_intensity: float = Field(..., description="Storm intensity (scale TBD)")
    storm_movement: StormMovementVector | None = Field(
        default=None, description="Storm motion vector (speed + direction)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this prediction (0.0–1.0)"
    )
    is_synthetic: bool = Field(
        ...,
        description=(
            "True if this forecast is based on synthetic data. "
            "MUST be True in DEMO mode."
        ),
    )
    explanation: str | None = Field(
        default=None,
        description="Human-readable evidence/reasoning for this forecast",
    )


class ForecastProduct(BaseModel):
    """
    Complete forecast for a region across all lead times.

    This is what the API returns and the dashboard displays.
    """

    model_config = {"protected_namespaces": ()}

    forecast_id: str = Field(..., description="Unique forecast identifier")
    created_at: datetime = Field(
        ..., description="When this forecast was generated (UTC)"
    )
    valid_from: datetime = Field(..., description="Base time of the forecast (UTC)")
    region: BoundingBox = Field(
        ..., description="Geographic region this forecast covers"
    )
    lead_times: list[ForecastLeadTime] = Field(
        ..., description="Lead times included in this forecast"
    )
    grid_forecasts: list[GridCellForecast] = Field(
        default_factory=list,
        description="Individual grid cell forecasts",
    )
    sensor_health: list[SensorHealth] = Field(
        default_factory=list,
        description="Health status of each data source used",
    )
    data_sources_used: list[str] = Field(
        default_factory=list,
        description="Names of data sources used (e.g., ['MOSDAC', 'SYNTHETIC'])",
    )
    model_version: str = Field(..., description="Version of the prediction model used")
    is_demo_mode: bool = Field(
        ...,
        description="True if this forecast was generated in DEMO mode",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any caveats, degradation notices, or warnings",
    )
