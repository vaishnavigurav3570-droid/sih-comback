"""
StormFusion AI — Synthetic Data Provider

Generates realistic but CLEARLY FAKE atmospheric data for development
and demonstration. Every value produced by this provider is deterministic
(not random) and labeled as SYNTHETIC.

WHY DETERMINISTIC:
    Using random() would give different results every run, making it
    impossible to debug or demonstrate consistently. Instead, we use
    mathematical functions (sine waves, Gaussian patterns) that always
    produce the same output for the same input. This is more honest
    and more useful for development.

WHAT IT GENERATES:
    - Satellite: Brightness temperature fields (like cloud-top temperatures)
    - Radar: Reflectivity fields (like precipitation intensity)
    - Lightning: Point-based flash observations
    - NWP: Atmospheric instability fields (like CAPE)

ALL outputs are clearly marked:
    - metadata.is_synthetic = True
    - metadata.source_name = "Synthetic"
    - xarray attrs: source = "SYNTHETIC"
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xarray as xr
from backend.app.models.data_types import (
    INDIA_BBOX,
    BoundingBox,
    DataSourceStatus,
    DataSourceType,
)
from backend.app.models.metadata import ConnectionStatus, DatasetMetadata
from backend.app.models.payload import (
    DataPayload,
    LightningDataPayload,
    LightningFlash,
)
from backend.app.providers.base import DataProvider

logger = logging.getLogger(__name__)


# ============================================================
# Synthetic variable definitions
# ============================================================

# Maps source types to the variables they can generate.
# Each variable has: (variable_name, units, long_name)
SYNTHETIC_VARIABLES: dict[DataSourceType, list[tuple[str, str, str]]] = {
    DataSourceType.SATELLITE: [
        ("bt_tir1", "K", "Brightness Temperature 10.8 μm (TIR1)"),
        ("bt_tir2", "K", "Brightness Temperature 12.0 μm (TIR2)"),
        ("bt_wv", "K", "Brightness Temperature 6.7 μm (Water Vapor)"),
        ("bt_mir", "K", "Brightness Temperature 3.9 μm (MIR)"),
    ],
    DataSourceType.RADAR: [
        ("reflectivity", "dBZ", "Radar Reflectivity"),
        ("vil", "kg/m2", "Vertically Integrated Liquid"),
        ("echo_top", "km", "Echo Top Height"),
    ],
    DataSourceType.NWP: [
        ("cape", "J/kg", "Convective Available Potential Energy"),
        ("cin", "J/kg", "Convective Inhibition"),
        ("wind_shear_0_6km", "m/s", "0–6 km Wind Shear"),
        ("lifted_index", "K", "Lifted Index"),
    ],
    DataSourceType.LIGHTNING: [
        ("flash_density", "flashes/km2/hr", "Lightning Flash Density"),
    ],
}

# Default grid dimensions for synthetic data
DEFAULT_NLAT = 64
DEFAULT_NLON = 60


class SyntheticDataProvider(DataProvider):
    """
    Generates deterministic synthetic atmospheric data.

    This provider always works — no credentials, no network, no files needed.
    It produces data that LOOKS like real atmospheric observations but is
    entirely generated from mathematical functions.

    EVERY output is labeled as SYNTHETIC. This is non-negotiable.

    Args:
        emulated_source_type: The type of data source to emulate
            (SATELLITE, RADAR, LIGHTNING, or NWP).
        nlat: Number of latitude grid points (default: 64).
        nlon: Number of longitude grid points (default: 60).
        bbox: Geographic bounding box (default: India).
    """

    def __init__(
        self,
        emulated_source_type: DataSourceType = DataSourceType.SATELLITE,
        nlat: int = DEFAULT_NLAT,
        nlon: int = DEFAULT_NLON,
        bbox: BoundingBox = INDIA_BBOX,
    ) -> None:
        self._emulated_source_type = emulated_source_type
        self._nlat = nlat
        self._nlon = nlon
        self._bbox = bbox

        # Pre-compute the lat/lon grid (used by all generated fields)
        self._latitudes = np.linspace(bbox.south, bbox.north, nlat)
        self._longitudes = np.linspace(bbox.west, bbox.east, nlon)

        logger.info(
            "SyntheticDataProvider initialized for %s (%dx%d grid)",
            emulated_source_type.value,
            nlat,
            nlon,
        )

    # ----------------------------------------------------------
    # DataProvider interface — required properties
    # ----------------------------------------------------------

    @property
    def source_type(self) -> DataSourceType:
        return self._emulated_source_type

    @property
    def source_name(self) -> str:
        return "Synthetic"

    @property
    def is_available(self) -> bool:
        # Synthetic data is ALWAYS available — that's the whole point.
        return True

    # ----------------------------------------------------------
    # DataProvider interface — required methods
    # ----------------------------------------------------------

    def search_datasets(
        self,
        start_time: datetime,
        end_time: datetime,
        bounding_box: BoundingBox,
        variables: list[str] | None = None,
        count: int = 10,
    ) -> list[DatasetMetadata]:
        """
        Return metadata for synthetic datasets that WOULD be available.

        Since synthetic data can be generated for any time/region,
        this always returns results.
        """
        all_vars = SYNTHETIC_VARIABLES.get(self._emulated_source_type, [])

        # Filter by requested variables if specified
        if variables:
            all_vars = [v for v in all_vars if v[0] in variables]

        results: list[DatasetMetadata] = []
        for var_name, units, long_name in all_vars[:count]:
            dataset_id = f"synthetic_{self._emulated_source_type.value}_{var_name}"
            results.append(
                DatasetMetadata(
                    dataset_id=dataset_id,
                    source_type=self._emulated_source_type,
                    source_name="Synthetic",
                    variable_name=var_name,
                    units=units,
                    time_start=start_time,
                    time_end=end_time,
                    bounding_box=bounding_box,
                    spatial_resolution_km=self._estimate_resolution_km(),
                    file_format="in_memory",
                    file_path=None,
                    is_synthetic=True,  # <-- ALWAYS True
                    extra={"long_name": long_name},
                )
            )

        logger.info(
            "Synthetic search returned %d datasets for %s",
            len(results),
            self._emulated_source_type.value,
        )
        return results

    def download(
        self,
        dataset_id: str,
        output_dir: Path | None = None,
        **kwargs,
    ) -> DataPayload:
        """
        Generate synthetic data for the requested dataset.

        The data is generated deterministically from mathematical
        functions — same dataset_id always produces the same data.
        """
        # Parse the dataset_id to figure out what to generate
        # Format: "synthetic_{source_type}_{variable_name}"
        parts = dataset_id.split("_", 2)
        if len(parts) < 3:
            raise ValueError(
                f"Invalid synthetic dataset_id: '{dataset_id}'. "
                f"Expected format: 'synthetic_{{source_type}}_{{variable_name}}'"
            )

        variable_name = parts[2]

        # Look up the variable definition
        all_vars = SYNTHETIC_VARIABLES.get(self._emulated_source_type, [])
        var_def = next((v for v in all_vars if v[0] == variable_name), None)

        if var_def is None:
            raise ValueError(
                f"Unknown variable '{variable_name}' for source type "
                f"'{self._emulated_source_type.value}'. "
                f"Available: {[v[0] for v in all_vars]}"
            )

        var_name, units, long_name = var_def

        # Generate the actual data
        reference_time = kwargs.get(
            "reference_time",
            datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        )

        if self._emulated_source_type == DataSourceType.LIGHTNING:
            return self._generate_lightning_payload(
                dataset_id, var_name, units, long_name, reference_time
            )
        else:
            data_array = self._generate_gridded_field(
                var_name, units, long_name, reference_time
            )

            metadata = DatasetMetadata(
                dataset_id=dataset_id,
                source_type=self._emulated_source_type,
                source_name="Synthetic",
                variable_name=var_name,
                units=units,
                time_start=reference_time,
                time_end=reference_time,
                bounding_box=self._bbox,
                spatial_resolution_km=self._estimate_resolution_km(),
                file_format="in_memory",
                is_synthetic=True,  # <-- ALWAYS True
                extra={"long_name": long_name},
            )

            return DataPayload(metadata=metadata, data=data_array)

    def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get metadata for a synthetic dataset (without generating data)."""
        parts = dataset_id.split("_", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid synthetic dataset_id: '{dataset_id}'")

        variable_name = parts[2]
        all_vars = SYNTHETIC_VARIABLES.get(self._emulated_source_type, [])
        var_def = next((v for v in all_vars if v[0] == variable_name), None)

        if var_def is None:
            raise ValueError(f"Unknown variable '{variable_name}'")

        var_name, units, long_name = var_def
        now = datetime.now(timezone.utc)

        return DatasetMetadata(
            dataset_id=dataset_id,
            source_type=self._emulated_source_type,
            source_name="Synthetic",
            variable_name=var_name,
            units=units,
            time_start=now,
            time_end=now,
            bounding_box=self._bbox,
            spatial_resolution_km=self._estimate_resolution_km(),
            file_format="in_memory",
            is_synthetic=True,  # <-- ALWAYS True
            extra={"long_name": long_name},
        )

    def validate_connection(self) -> ConnectionStatus:
        """Synthetic provider is always healthy."""
        return ConnectionStatus(
            source_type=self._emulated_source_type,
            status=DataSourceStatus.OK,
            is_connected=True,
            message=(
                f"SyntheticDataProvider for {self._emulated_source_type.value} "
                f"is ready (SIMULATED data only)"
            ),
            latency_ms=0.0,
            checked_at=datetime.now(timezone.utc),
        )

    # ----------------------------------------------------------
    # Private: Synthetic data generation functions
    # ----------------------------------------------------------

    def _generate_gridded_field(
        self,
        var_name: str,
        units: str,
        long_name: str,
        reference_time: datetime,
    ) -> xr.DataArray:
        """
        Generate a 2D gridded field using deterministic math functions.

        The pattern combines:
        1. A smooth base field (Gaussian hot spots simulating storm cells)
        2. A latitudinal gradient (storms are more common in certain regions)
        3. A time-varying component (makes the pattern shift with time)

        This is NOT random — same inputs always give the same outputs.
        """
        # Create 2D meshgrid of lat/lon
        lon_grid, lat_grid = np.meshgrid(self._longitudes, self._latitudes)

        # Derive a deterministic "time seed" from the reference time
        # This makes the pattern vary with time but remain reproducible
        time_seed = (
            reference_time.hour * 3600
            + reference_time.minute * 60
            + reference_time.second
        ) / 86400.0  # normalized to [0, 1]

        # Generate the field based on variable type
        if var_name.startswith("bt_"):
            values = self._generate_brightness_temperature(
                lat_grid, lon_grid, time_seed, var_name
            )
        elif var_name == "reflectivity":
            values = self._generate_reflectivity(lat_grid, lon_grid, time_seed)
        elif var_name == "vil":
            values = self._generate_vil(lat_grid, lon_grid, time_seed)
        elif var_name == "echo_top":
            values = self._generate_echo_top(lat_grid, lon_grid, time_seed)
        elif var_name == "cape":
            values = self._generate_cape(lat_grid, lon_grid, time_seed)
        elif var_name == "cin":
            values = self._generate_cin(lat_grid, lon_grid, time_seed)
        elif var_name == "wind_shear_0_6km":
            values = self._generate_wind_shear(lat_grid, lon_grid, time_seed)
        elif var_name == "lifted_index":
            values = self._generate_lifted_index(lat_grid, lon_grid, time_seed)
        else:
            # Fallback: gentle Gaussian pattern
            values = self._generate_generic_field(lat_grid, lon_grid, time_seed)

        # Wrap in xarray with proper metadata
        data_array = xr.DataArray(
            data=values,
            dims=["latitude", "longitude"],
            coords={
                "latitude": self._latitudes,
                "longitude": self._longitudes,
                "time": np.datetime64(reference_time.replace(tzinfo=None), "ns"),
            },
            attrs={
                "units": units,
                "long_name": long_name,
                "source": "SYNTHETIC",  # <-- ALWAYS marked
                "variable_id": var_name,
                "is_synthetic": True,
                "generation_method": "deterministic_mathematical_function",
            },
        )

        return data_array

    def _generate_brightness_temperature(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
        var_name: str,
    ) -> np.ndarray:
        """
        Simulate satellite brightness temperature.

        Real BT fields show:
        - Warm values (~290-300 K) for clear sky
        - Cold values (~200-220 K) for deep convective cloud tops
        - The colder the cloud top, the taller (and more dangerous) the storm

        We simulate this with a warm base field and cold Gaussian "storm" spots.
        """
        # Warm base (clear sky background)
        base = 290.0 + 5.0 * np.sin(np.radians(lat_grid) * 2.0)

        # Simulate 3 storm cells as cold Gaussian spots
        storms = np.zeros_like(lat_grid)
        storm_centers = [
            (
                22.0 + 2.0 * math.sin(time_seed * 2 * math.pi),
                80.0 + 3.0 * math.cos(time_seed * 2 * math.pi),
            ),
            (26.0, 85.0 + 2.0 * math.sin(time_seed * 3 * math.pi)),
            (18.0 + math.cos(time_seed * math.pi), 75.0),
        ]
        storm_intensities = [70.0, 50.0, 40.0]  # How cold (deep) each storm is

        for (clat, clon), intensity in zip(storm_centers, storm_intensities):
            distance_sq = (lat_grid - clat) ** 2 + (lon_grid - clon) ** 2
            sigma_sq = 6.0  # Controls storm "size" in degrees
            storms += intensity * np.exp(-distance_sq / (2 * sigma_sq))

        values = base - storms

        # Different channels have slightly different characteristics
        if var_name == "bt_tir2":
            values = values + 2.0  # TIR2 is slightly warmer
        elif var_name == "bt_wv":
            values = values - 30.0  # Water vapor channel is cooler overall
        elif var_name == "bt_mir":
            values = values + 10.0  # MIR channel

        return values.astype(np.float32)

    def _generate_reflectivity(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """
        Simulate radar reflectivity (dBZ).

        Real radar shows:
        - 0-20 dBZ: light rain or drizzle
        - 20-40 dBZ: moderate rain
        - 40-55 dBZ: heavy rain / hail
        - 55+ dBZ: severe thunderstorm

        We simulate with Gaussian storm cells on a near-zero background.
        """
        # Low background (no rain)
        base = 5.0 * np.ones_like(lat_grid)

        # Storm cells
        storm_centers = [
            (22.0 + 2.0 * math.sin(time_seed * 2 * math.pi), 80.0),
            (26.0 + math.cos(time_seed * math.pi), 85.0),
        ]

        for clat, clon in storm_centers:
            distance_sq = (lat_grid - clat) ** 2 + (lon_grid - clon) ** 2
            sigma_sq = 4.0
            base += 50.0 * np.exp(-distance_sq / (2 * sigma_sq))

        # Clamp to physically reasonable range
        values = np.clip(base, 0.0, 70.0)
        return values.astype(np.float32)

    def _generate_vil(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """Simulate Vertically Integrated Liquid (kg/m²). Correlates with reflectivity."""
        reflectivity = self._generate_reflectivity(lat_grid, lon_grid, time_seed)
        # VIL roughly correlates with reflectivity (simplified)
        vil = 0.5 * np.maximum(reflectivity - 10.0, 0.0)
        return vil.astype(np.float32)

    def _generate_echo_top(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """Simulate Echo Top height (km). Higher = stronger storm."""
        reflectivity = self._generate_reflectivity(lat_grid, lon_grid, time_seed)
        # Echo tops increase with reflectivity (simplified)
        echo_top = 2.0 + 0.2 * np.maximum(reflectivity - 15.0, 0.0)
        echo_top = np.clip(echo_top, 0.0, 18.0)
        return echo_top.astype(np.float32)

    def _generate_cape(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """
        Simulate CAPE (Convective Available Potential Energy, J/kg).

        Real values:
        - 0-500: Weak instability
        - 500-1500: Moderate (isolated storms possible)
        - 1500-3000: Strong (severe storms likely)
        - 3000+: Extreme (violent storms possible)

        We simulate a latitudinal gradient (more unstable in tropics)
        with localized maxima.
        """
        # Latitudinal gradient: more CAPE near the tropics
        base = 1500.0 - 40.0 * np.abs(lat_grid - 20.0)

        # Time-varying enhancement
        enhancement_center_lat = 22.0 + 4.0 * math.sin(time_seed * 2 * math.pi)
        enhancement_center_lon = 80.0 + 5.0 * math.cos(time_seed * 2 * math.pi)
        distance_sq = (lat_grid - enhancement_center_lat) ** 2 + (
            lon_grid - enhancement_center_lon
        ) ** 2
        base += 1500.0 * np.exp(-distance_sq / (2 * 15.0))

        values = np.clip(base, 0.0, 5000.0)
        return values.astype(np.float32)

    def _generate_cin(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """
        Simulate CIN (Convective Inhibition, J/kg).

        CIN is the "cap" that prevents storms from forming.
        Lower CIN = easier for storms to break through.
        Typically 0–200 J/kg. We use negative convention (more negative = stronger cap).
        """
        # Base CIN with latitude dependence
        base = -50.0 - 30.0 * np.cos(np.radians(lat_grid) * 3.0)

        # Time variation
        time_factor = math.sin(time_seed * math.pi)
        base += 20.0 * time_factor

        values = np.clip(base, -300.0, 0.0)
        return values.astype(np.float32)

    def _generate_wind_shear(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """
        Simulate 0–6 km wind shear (m/s).

        Wind shear controls storm type:
        - < 10 m/s: Single cell storms (short-lived)
        - 10-20 m/s: Multicell storms
        - 20-30 m/s: Supercells possible
        - 30+ m/s: Tornadic supercells possible
        """
        base = 10.0 + 5.0 * np.sin(np.radians(lat_grid) * 4.0)
        base += 8.0 * np.cos(np.radians(lon_grid - 80.0) * 2.0)

        # Time modulation
        base += 5.0 * math.sin(time_seed * 2 * math.pi)

        values = np.clip(base, 0.0, 40.0)
        return values.astype(np.float32)

    def _generate_lifted_index(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """
        Simulate Lifted Index (K).

        Negative values indicate instability:
        - 0 to -3: Marginally unstable
        - -3 to -6: Moderately unstable
        - -6 to -9: Very unstable
        - < -9: Extremely unstable
        """
        # Inverse of CAPE pattern (where CAPE is high, LI is negative)
        cape = self._generate_cape(lat_grid, lon_grid, time_seed)
        li = 3.0 - (cape / 500.0)
        values = np.clip(li, -12.0, 8.0)
        return values.astype(np.float32)

    def _generate_generic_field(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        time_seed: float,
    ) -> np.ndarray:
        """Fallback: a simple smooth Gaussian pattern."""
        center_lat = 22.0 + 3.0 * math.sin(time_seed * math.pi)
        center_lon = 80.0
        distance_sq = (lat_grid - center_lat) ** 2 + (lon_grid - center_lon) ** 2
        values = np.exp(-distance_sq / 50.0)
        return values.astype(np.float32)

    def _generate_lightning_payload(
        self,
        dataset_id: str,
        var_name: str,
        units: str,
        long_name: str,
        reference_time: datetime,
    ) -> DataPayload:
        """
        Generate synthetic lightning flash observations.

        Instead of a grid, lightning data is a collection of point events.
        We place flashes near the simulated storm centers.
        """
        # Derive a deterministic time seed
        time_seed = (
            reference_time.hour * 3600
            + reference_time.minute * 60
            + reference_time.second
        ) / 86400.0

        # Storm cell centers (same as used for other fields)
        storm_centers = [
            (
                22.0 + 2.0 * math.sin(time_seed * 2 * math.pi),
                80.0 + 3.0 * math.cos(time_seed * 2 * math.pi),
            ),
            (26.0, 85.0 + 2.0 * math.sin(time_seed * 3 * math.pi)),
        ]

        flashes: list[LightningFlash] = []
        flash_count = 0

        for storm_idx, (clat, clon) in enumerate(storm_centers):
            # Generate deterministic flash positions around each storm center
            n_flashes = 15 + storm_idx * 5  # 15 and 20 flashes per storm

            for i in range(n_flashes):
                # Deterministic position using golden angle spiral
                angle = i * 2.399963  # golden angle in radians
                radius = 0.3 * math.sqrt(i + 1)  # increasing radius

                flash_lat = clat + radius * math.cos(angle)
                flash_lon = clon + radius * math.sin(angle)

                # Only include flashes inside the bounding box
                if not self._bbox.contains_point(flash_lat, flash_lon):
                    continue

                # Deterministic flash properties
                flash_second = (i * 17 + storm_idx * 31) % 60
                flash_time = reference_time.replace(second=flash_second, microsecond=0)

                flashes.append(
                    LightningFlash(
                        flash_id=f"SYN_FLASH_{flash_count:04d}",
                        latitude=round(flash_lat, 4),
                        longitude=round(flash_lon, 4),
                        timestamp=flash_time,
                        flash_type="CG" if i % 3 != 0 else "IC",
                        polarity="negative" if i % 5 != 0 else "positive",
                        peak_current_kA=round(20.0 + i * 2.5, 1),
                        is_synthetic=True,  # <-- ALWAYS True
                    )
                )
                flash_count += 1

        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            source_type=DataSourceType.LIGHTNING,
            source_name="Synthetic",
            variable_name=var_name,
            units=units,
            time_start=reference_time,
            time_end=reference_time,
            bounding_box=self._bbox,
            is_synthetic=True,  # <-- ALWAYS True
            extra={"long_name": long_name, "flash_count": len(flashes)},
        )

        lightning_payload = LightningDataPayload(
            metadata=metadata,
            flashes=flashes,
        )

        # Wrap in DataPayload for interface compatibility
        # The pipeline will check isinstance for LightningDataPayload specifics
        return DataPayload(metadata=metadata, data=lightning_payload)

    # ----------------------------------------------------------
    # Private: Utility methods
    # ----------------------------------------------------------

    def _estimate_resolution_km(self) -> float:
        """Estimate the approximate grid resolution in km."""
        # Rough conversion: 1 degree latitude ≈ 111 km
        lat_range = self._bbox.north - self._bbox.south
        return round((lat_range / self._nlat) * 111.0, 1)
