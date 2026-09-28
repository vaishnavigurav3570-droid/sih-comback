"""
StormFusion AI — Dataset Metadata & Connection Status

Metadata that describes a dataset (file, observation set, etc.)
and the health status of connections to data sources.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.app.models.data_types import BoundingBox, DataSourceStatus, DataSourceType
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """
    Metadata describing a single dataset.

    Every piece of data in StormFusion carries this metadata so we always know:
    - Where it came from (source_type, source_name)
    - What it contains (variable_name, units)
    - When and where it covers (time_start, time_end, bounding_box)
    - Whether it's real or synthetic (is_synthetic)
    """

    dataset_id: str = Field(..., description="Unique identifier for this dataset")
    source_type: DataSourceType = Field(
        ..., description="Type of data source (satellite, radar, etc.)"
    )
    source_name: str = Field(
        ...,
        description="Human-readable name of the source (e.g., 'MOSDAC', 'Synthetic')",
    )
    variable_name: str = Field(
        ...,
        description="Name of the physical variable (e.g., 'brightness_temperature_10.8')",
    )
    units: str = Field(..., description="Physical units (e.g., 'K', 'dBZ')")
    time_start: datetime = Field(..., description="Observation start time (UTC)")
    time_end: datetime = Field(..., description="Observation end time (UTC)")
    bounding_box: BoundingBox = Field(..., description="Geographic coverage")
    spatial_resolution_km: float | None = Field(
        default=None, description="Approximate spatial resolution in km"
    )
    file_format: str | None = Field(
        default=None, description="File format (HDF5, NetCDF, GRIB2, etc.)"
    )
    file_path: Path | None = Field(
        default=None, description="Local file path (if downloaded)"
    )
    is_synthetic: bool = Field(
        default=False,
        description="True if this is generated/simulated data, NOT real observations",
    )
    quality_flags: dict | None = Field(
        default=None, description="Quality control metadata"
    )
    extra: dict | None = Field(default=None, description="Any additional metadata")

    model_config = {"arbitrary_types_allowed": True}


class ConnectionStatus(BaseModel):
    """
    Result of checking whether a data provider is reachable and working.

    Returned by DataProvider.validate_connection().
    """

    source_type: DataSourceType = Field(
        ..., description="Which type of source was checked"
    )
    status: DataSourceStatus = Field(..., description="Current health status")
    is_connected: bool = Field(..., description="Whether the connection is working")
    message: str = Field(..., description="Human-readable status message")
    latency_ms: float | None = Field(
        default=None, description="Connection latency in milliseconds"
    )
    checked_at: datetime = Field(..., description="When this check was performed (UTC)")
