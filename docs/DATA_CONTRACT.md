# StormFusion AI — Data Contract

> Defines the exact data structures, schemas, and interfaces that all components agree to use.

---

## 1. Why a Data Contract?

Every part of StormFusion AI needs to agree on:
- What shape data has
- What units are used
- What "missing" looks like
- What metadata travels with the data

This contract is the agreement. If a data provider returns data, it must match these schemas. If the pipeline expects input, it expects these schemas.

---

## 2. Core Data Types

### 2.1 BoundingBox

Defines a geographic rectangle.

```python
from pydantic import BaseModel

class BoundingBox(BaseModel):
    """Geographic bounding box in decimal degrees (WGS84)."""
    west: float    # Western longitude  (e.g., 68.0 for India)
    south: float   # Southern latitude  (e.g., 6.0 for India)
    east: float    # Eastern longitude  (e.g., 98.0 for India)
    north: float   # Northern latitude  (e.g., 38.0 for India)
```

### 2.2 DataSourceType

Enum for all supported data source types.

```python
from enum import Enum

class DataSourceType(str, Enum):
    SATELLITE = "satellite"
    RADAR = "radar"
    LIGHTNING = "lightning"
    NWP = "nwp"
    SURFACE_STATION = "surface_station"
    SYNTHETIC = "synthetic"
```

### 2.3 DataSourceStatus

```python
class DataSourceStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    SYNTHETIC_FALLBACK = "synthetic_fallback"
```

### 2.4 ConnectionStatus

```python
class ConnectionStatus(BaseModel):
    """Result of a validate_connection() call."""
    source_type: DataSourceType
    is_connected: bool
    message: str
    latency_ms: float | None = None
    checked_at: datetime
```

---

## 3. Dataset Metadata

Every piece of data in the system carries metadata:

```python
class DatasetMetadata(BaseModel):
    """Metadata describing a single dataset (file, observation set, etc.)."""
    dataset_id: str                      # Unique identifier
    source_type: DataSourceType          # satellite, radar, etc.
    source_name: str                     # "MOSDAC", "Synthetic", etc.
    variable_name: str                   # "brightness_temperature_10.8", etc.
    units: str                           # "K", "dBZ", "counts/km2", etc.
    time_start: datetime                 # Observation start time (UTC)
    time_end: datetime                   # Observation end time (UTC)
    bounding_box: BoundingBox            # Geographic coverage
    spatial_resolution_km: float | None  # Approximate resolution in km
    file_format: str | None              # "HDF5", "NetCDF", "GRIB2", etc.
    file_path: Path | None              # Local file path (if downloaded)
    is_synthetic: bool = False           # True if this is generated data
    quality_flags: dict | None = None    # QC metadata
    extra: dict | None = None            # Any additional metadata
```

---

## 4. Data Payload

The actual data returned by a provider:

```python
import xarray as xr

class DataPayload(BaseModel):
    """Container for actual data plus its metadata."""
    metadata: DatasetMetadata
    data: Any  # In practice: xr.DataArray or xr.Dataset
    # Note: Pydantic can't validate xarray directly.
    # The 'data' field holds the actual gridded/point data.

    class Config:
        arbitrary_types_allowed = True
```

### 4.1 xarray Convention

All gridded data (satellite, radar, NWP) should be represented as `xr.DataArray` or `xr.Dataset` with these coordinate conventions:

```python
# Example: a satellite brightness temperature field
import xarray as xr
import numpy as np

data = xr.DataArray(
    data=np.zeros((100, 200)),      # 2D grid of values
    dims=["latitude", "longitude"],
    coords={
        "latitude": np.linspace(6.0, 38.0, 100),
        "longitude": np.linspace(68.0, 98.0, 200),
        "time": np.datetime64("2026-09-28T12:00:00"),
    },
    attrs={
        "units": "K",
        "long_name": "Brightness Temperature (10.8 μm)",
        "source": "SYNTHETIC",  # or "MOSDAC"
        "variable_id": "bt_tir1",
    },
)
```

**Required coordinate names:**
| Coordinate | Description |
|------------|-------------|
| `latitude` | Decimal degrees, WGS84, south-to-north |
| `longitude` | Decimal degrees, WGS84, west-to-east |
| `time` | numpy datetime64 in UTC |
| `level` | (optional) Vertical level for 3D data |

**Required attributes:**
| Attribute | Description |
|-----------|-------------|
| `units` | CF-convention units string |
| `long_name` | Human-readable variable description |
| `source` | `"SYNTHETIC"`, `"MOSDAC"`, `"RADAR"`, etc. |
| `variable_id` | Machine-readable variable identifier |

---

## 5. Lightning Data (Point-Based)

Lightning data is point-based, not gridded:

```python
class LightningFlash(BaseModel):
    """A single lightning flash observation."""
    flash_id: str
    latitude: float
    longitude: float
    timestamp: datetime               # UTC
    flash_type: str                   # "CG" (cloud-to-ground) or "IC" (intra-cloud)
    polarity: str | None              # "positive" or "negative"
    peak_current_kA: float | None     # Peak current in kiloamperes
    is_synthetic: bool = False

class LightningDataPayload(BaseModel):
    """A collection of lightning flashes."""
    metadata: DatasetMetadata
    flashes: list[LightningFlash]
```

Lightning data is gridded (binned into grid cells) during the "Common Grid" pipeline stage, not before.

---

## 6. DataProvider Interface

The abstract base class that ALL providers must implement:

```python
from abc import ABC, abstractmethod

class DataProvider(ABC):
    """
    Abstract interface for all data sources.
    
    Every data source — real or synthetic — implements this interface.
    The pipeline never knows or cares about the concrete implementation.
    """

    @abstractmethod
    def search_datasets(
        self,
        start_time: datetime,
        end_time: datetime,
        bounding_box: BoundingBox,
        variables: list[str] | None = None,
        count: int = 10,
    ) -> list[DatasetMetadata]:
        """Search for available datasets matching the criteria."""
        ...

    @abstractmethod
    def download(
        self,
        dataset_id: str,
        output_dir: Path | None = None,
        **kwargs,
    ) -> DataPayload:
        """Download/generate a specific dataset."""
        ...

    @abstractmethod
    def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get metadata for a specific dataset without downloading."""
        ...

    @abstractmethod
    def validate_connection(self) -> ConnectionStatus:
        """Check connectivity and authentication."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """The type of data this provider supplies."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can currently serve data."""
        ...
```

### 6.1 DataProviderFactory

```python
class DataProviderFactory:
    """
    Creates the appropriate DataProvider based on configuration.
    
    Usage:
        factory = DataProviderFactory(config)
        satellite = factory.get_provider(DataSourceType.SATELLITE)
        radar = factory.get_provider(DataSourceType.RADAR)
    """

    def get_provider(self, source_type: DataSourceType) -> DataProvider:
        """
        Returns the configured provider for the given source type.
        
        In DEMO mode: always returns SyntheticDataProvider.
        In LIVE mode: returns the real provider, with fallback to synthetic.
        """
        ...

    def get_all_providers(self) -> dict[DataSourceType, DataProvider]:
        """Returns all configured providers."""
        ...

    def get_health(self) -> dict[DataSourceType, ConnectionStatus]:
        """Check health of all providers."""
        ...
```

---

## 7. Forecast Output Schema

What the prediction engine produces:

```python
class ForecastLeadTime(str, Enum):
    PLUS_15 = "+15min"
    PLUS_30 = "+30min"
    PLUS_60 = "+60min"
    PLUS_90 = "+90min"

class StormMovementVector(BaseModel):
    speed_kmh: float
    direction_degrees: float  # Meteorological convention: 0=N, 90=E

class SensorHealth(BaseModel):
    source_type: DataSourceType
    status: DataSourceStatus
    last_data_time: datetime | None
    message: str

class GridCellForecast(BaseModel):
    """Forecast for a single grid cell at a single lead time."""
    latitude: float
    longitude: float
    lead_time: ForecastLeadTime
    thunderstorm_probability: float     # 0.0–1.0
    lightning_probability: float         # 0.0–1.0
    storm_intensity: float              # Scale TBD
    storm_movement: StormMovementVector | None
    confidence: float                    # 0.0–1.0
    is_synthetic: bool                   # True if based on synthetic data
    explanation: str | None             # Human-readable evidence

class ForecastProduct(BaseModel):
    """Complete forecast for a region at all lead times."""
    forecast_id: str
    created_at: datetime
    valid_from: datetime
    region: BoundingBox
    lead_times: list[ForecastLeadTime]
    grid_forecasts: list[GridCellForecast]
    sensor_health: list[SensorHealth]
    data_sources_used: list[str]         # ["MOSDAC", "SYNTHETIC", ...]
    model_version: str
    is_demo_mode: bool
    warnings: list[str]                  # Any caveats or degradation notices
```

---

## 8. API Response Envelope

All API responses use a consistent envelope:

```python
class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: T | None
    error: str | None = None
    warnings: list[str] = []
    metadata: dict = {}
    timestamp: datetime
    is_demo_mode: bool
```

---

## 9. Units Convention

| Variable | Unit | Notes |
|----------|------|-------|
| Temperature / Brightness Temperature | K (Kelvin) | Convert to °C only for display |
| Radar reflectivity | dBZ | |
| Lightning flash density | flashes/km²/hr | |
| Wind speed | m/s | Convert to km/h only for display |
| Wind direction | degrees | Meteorological: 0=N, 90=E, 180=S, 270=W |
| Precipitation | mm/hr | |
| Latitude/Longitude | decimal degrees | WGS84 |
| CAPE | J/kg | |
| Probabilities | 0.0–1.0 | Convert to % only for display |
| Time | UTC | Always store in UTC. Convert for display. |

---

## 10. Versioning

This data contract is version **0.1.0** (Phase 0 — architecture only).

Changes to this contract must be documented and all affected components must be updated together.
