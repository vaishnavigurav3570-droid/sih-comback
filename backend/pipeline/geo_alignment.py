"""
StormFusion AI — Geospatial Alignment Module

PURPOSE:
    Ensures all data is on the same coordinate reference system (CRS)
    and handles any necessary reprojection.

THE PROBLEM:
    Different data sources may use different map projections:
    - Satellite: geostationary projection (centered on satellite)
    - Radar: polar stereographic or local projections
    - NWP: regular lat/lon or Lambert conformal
    - Lightning: usually lat/lon (WGS84)

    We need everything in one consistent projection before we can
    overlay and fuse the data.

OUR APPROACH (PROTOTYPE):
    For the prototype, we assume all data is already on a regular
    lat/lon (WGS84) grid — which is true for our synthetic data.

    The module is structured so that real reprojection (using pyproj
    and rasterio) can be added later when we integrate real radar
    and satellite data that comes in non-standard projections.

TARGET CRS:
    EPSG:4326 (WGS84 lat/lon) — the standard for geographic data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import xarray as xr
from backend.app.models.data_types import DataSourceType
from backend.app.models.payload import DataPayload
from backend.pipeline.time_sync import TimeSyncResult

logger = logging.getLogger(__name__)

# Target CRS for all data
TARGET_CRS = "EPSG:4326"  # WGS84 lat/lon


@dataclass
class GeoAlignInfo:
    """Information about how a payload was geospatially aligned."""

    variable_name: str
    source_type: DataSourceType
    original_crs: str
    target_crs: str
    was_reprojected: bool
    lat_range: tuple[float, float]  # (min, max)
    lon_range: tuple[float, float]  # (min, max)

    @property
    def summary(self) -> str:
        reproj = "reprojected" if self.was_reprojected else "already aligned"
        return (
            f"{self.variable_name}: {reproj} to {self.target_crs}, "
            f"lat=[{self.lat_range[0]:.1f}, {self.lat_range[1]:.1f}], "
            f"lon=[{self.lon_range[0]:.1f}, {self.lon_range[1]:.1f}]"
        )


@dataclass
class GeoAlignResult:
    """Result of geospatial alignment for the full batch."""

    target_crs: str = TARGET_CRS
    aligned_payloads: list[DataPayload] = field(default_factory=list)
    align_info: list[GeoAlignInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class GeoAligner:
    """
    Ensures all data is on the target coordinate reference system.

    For the prototype, this mainly validates that data is on WGS84
    and records coordinate ranges. Real reprojection will be added
    in Phase 7 when we integrate real radar/satellite data.

    Usage:
        aligner = GeoAligner()
        geo_result = aligner.run(time_sync_result)
    """

    def __init__(self, target_crs: str = TARGET_CRS) -> None:
        self._target_crs = target_crs

    def run(self, sync_result: TimeSyncResult) -> GeoAlignResult:
        """
        Align all synced payloads to the target CRS.

        Args:
            sync_result: Output from the time synchronization stage.

        Returns:
            GeoAlignResult with aligned payloads.
        """
        logger.info(
            "Starting geospatial alignment to %s with %d payloads",
            self._target_crs,
            len(sync_result.synced_payloads),
        )

        result = GeoAlignResult(target_crs=self._target_crs)

        for payload in sync_result.synced_payloads:
            try:
                aligned_payload, info = self._align_payload(payload)
                result.aligned_payloads.append(aligned_payload)
                result.align_info.append(info)
                logger.debug("Aligned: %s", info.summary)
            except Exception as exc:
                warning = (
                    f"Geo alignment failed for "
                    f"{payload.metadata.variable_name}: {exc}"
                )
                logger.warning(warning)
                result.warnings.append(warning)
                # Pass through unaligned
                result.aligned_payloads.append(payload)

        logger.info(
            "Geospatial alignment complete: %d payloads aligned",
            len(result.aligned_payloads),
        )

        return result

    def _align_payload(
        self,
        payload: DataPayload,
    ) -> tuple[DataPayload, GeoAlignInfo]:
        """Align a single payload to the target CRS."""

        source_type = payload.metadata.source_type
        var_name = payload.metadata.variable_name

        if isinstance(payload.data, xr.DataArray):
            data = payload.data

            # Get coordinate ranges
            lats = data.coords["latitude"].values
            lons = data.coords["longitude"].values

            lat_range = (float(np.min(lats)), float(np.max(lats)))
            lon_range = (float(np.min(lons)), float(np.max(lons)))

            # Check if data has a CRS attribute
            original_crs = data.attrs.get("crs", TARGET_CRS)

            needs_reprojection = original_crs != self._target_crs

            if needs_reprojection:
                # TODO Phase 7: Use rasterio/pyproj for real reprojection
                # For now, log a warning
                logger.warning(
                    "Reprojection from %s to %s not yet implemented. "
                    "Assuming data is already on target CRS.",
                    original_crs,
                    self._target_crs,
                )

            # Add CRS metadata to the data
            aligned = data.copy()
            aligned.attrs["crs"] = self._target_crs
            aligned.attrs["geo_aligned"] = True

            # Ensure latitude is south-to-north (ascending)
            if len(lats) > 1 and lats[0] > lats[-1]:
                aligned = aligned.sortby("latitude")
                logger.debug("Sorted latitude to ascending order")

            # Ensure longitude is west-to-east (ascending)
            if len(lons) > 1 and lons[0] > lons[-1]:
                aligned = aligned.sortby("longitude")
                logger.debug("Sorted longitude to ascending order")

            info = GeoAlignInfo(
                variable_name=var_name,
                source_type=source_type,
                original_crs=original_crs,
                target_crs=self._target_crs,
                was_reprojected=needs_reprojection,
                lat_range=lat_range,
                lon_range=lon_range,
            )

            return DataPayload(metadata=payload.metadata, data=aligned), info

        else:
            # Non-gridded data (lightning) — assume already on WGS84
            info = GeoAlignInfo(
                variable_name=var_name,
                source_type=source_type,
                original_crs=TARGET_CRS,
                target_crs=self._target_crs,
                was_reprojected=False,
                lat_range=(0.0, 0.0),
                lon_range=(0.0, 0.0),
            )
            return payload, info
