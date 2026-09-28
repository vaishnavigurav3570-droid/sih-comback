"""
StormFusion AI — Data Payload Models

Containers for the actual data returned by data providers.
DataPayload wraps gridded data (satellite, radar, NWP).
LightningDataPayload wraps point-based lightning observations.
"""

from __future__ import annotations

from typing import Any

from backend.app.models.metadata import DatasetMetadata
from pydantic import BaseModel, Field


class DataPayload(BaseModel):
    """
    Container for gridded data plus its metadata.

    The 'data' field holds the actual values — typically an xarray.DataArray
    or xarray.Dataset. Pydantic can't validate xarray objects directly,
    so we use 'Any' and rely on our provider implementations to return
    the correct type.

    Usage:
        payload = provider.download("some_dataset_id")
        metadata = payload.metadata       # DatasetMetadata
        xr_data = payload.data            # xarray.DataArray
    """

    metadata: DatasetMetadata = Field(
        ..., description="Metadata describing this dataset"
    )
    data: Any = Field(
        ...,
        description=(
            "The actual data. For gridded data: xarray.DataArray or xarray.Dataset. "
            "Must have 'latitude', 'longitude' coordinates and a 'source' attribute."
        ),
    )

    model_config = {"arbitrary_types_allowed": True}


class LightningFlash(BaseModel):
    """
    A single lightning flash observation.

    Each flash is a point event with a location, time, and properties.
    """

    flash_id: str = Field(..., description="Unique identifier for this flash")
    latitude: float = Field(..., description="Flash latitude (WGS84)")
    longitude: float = Field(..., description="Flash longitude (WGS84)")
    timestamp: datetime = Field(..., description="Flash time (UTC)")
    flash_type: str = Field(
        ...,
        description="'CG' (cloud-to-ground) or 'IC' (intra-cloud)",
    )
    polarity: str | None = Field(default=None, description="'positive' or 'negative'")
    peak_current_kA: float | None = Field(
        default=None, description="Peak current in kiloamperes"
    )
    is_synthetic: bool = Field(
        default=False,
        description="True if this flash is simulated, not a real observation",
    )


class LightningDataPayload(BaseModel):
    """
    A collection of lightning flash observations.

    Lightning data is point-based (not gridded). It gets converted to
    gridded format during the "Common Grid" pipeline stage.
    """

    metadata: DatasetMetadata = Field(
        ..., description="Metadata for this lightning dataset"
    )
    flashes: list[LightningFlash] = Field(
        default_factory=list,
        description="List of individual lightning flash observations",
    )


# Needed for the LightningFlash.timestamp type hint
from datetime import datetime  # noqa: E402
