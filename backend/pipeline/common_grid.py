"""
StormFusion AI — Common Grid Module

PURPOSE:
    Interpolates all data sources onto a single uniform lat/lon grid.
    This is the final pre-processing step before feature extraction.

THE PROBLEM:
    Even after CRS alignment, different sources have different resolutions:
    - Satellite: ~4 km
    - Radar: ~1 km
    - NWP: ~10–25 km
    - Lightning: irregular point data

    To fuse them, everything must be on the SAME grid with the SAME
    dimensions so we can stack them into a single tensor.

HOW IT WORKS:
    1. Define a target grid (regular lat/lon, configurable resolution)
    2. For each gridded source: interpolate to the target grid using
       nearest-neighbor or bilinear interpolation
    3. For lightning point data: bin into grid cells (count per cell)
    4. Missing sources get NaN-filled grids with a missing_source flag

OUTPUT:
    An xarray.Dataset containing ALL variables on ONE grid.
    Each variable is a 2D (lat, lon) DataArray.
    This is what the feature extraction stage consumes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import xarray as xr
from backend.app.models.data_types import INDIA_BBOX, BoundingBox
from backend.app.models.payload import LightningDataPayload
from backend.pipeline.geo_alignment import GeoAlignResult

logger = logging.getLogger(__name__)

# Default grid resolution (degrees)
DEFAULT_RESOLUTION_DEG = 0.5  # ~55 km at equator, ~50 km at 22°N (India)


@dataclass
class GridSpec:
    """
    Specification for the target uniform grid.

    Think of this as the "canvas" we paint all the data onto.
    """

    bbox: BoundingBox
    resolution_deg: float = DEFAULT_RESOLUTION_DEG
    max_interpolation_distance_deg: float = 0.75

    @property
    def latitudes(self) -> np.ndarray:
        """Generate latitude array for the grid."""
        return np.arange(
            self.bbox.south,
            self.bbox.north + self.resolution_deg / 2,
            self.resolution_deg,
        )

    @property
    def longitudes(self) -> np.ndarray:
        """Generate longitude array for the grid."""
        return np.arange(
            self.bbox.west,
            self.bbox.east + self.resolution_deg / 2,
            self.resolution_deg,
        )

    @property
    def nlat(self) -> int:
        return len(self.latitudes)

    @property
    def nlon(self) -> int:
        return len(self.longitudes)

    @property
    def shape(self) -> tuple[int, int]:
        return (self.nlat, self.nlon)


@dataclass
class CommonGridResult:
    """Result of regridding all data to the common grid."""

    grid_spec: GridSpec
    dataset: xr.Dataset | None = None
    variables_included: list[str] = field(default_factory=list)
    variables_missing: list[str] = field(default_factory=list)
    analysis_time: datetime | None = None
    is_synthetic: bool = False
    warnings: list[str] = field(default_factory=list)


class CommonGridder:
    """
    Interpolates all data onto a single uniform grid.

    This is where all the different-resolution sources become
    one unified dataset that the model can consume.

    Usage:
        gridder = CommonGridder(grid_spec=GridSpec(bbox=INDIA_BBOX))
        grid_result = gridder.run(geo_result, analysis_time=...)
    """

    def __init__(
        self,
        grid_spec: GridSpec | None = None,
    ) -> None:
        """
        Args:
            grid_spec: Target grid specification. Defaults to India at 0.5° resolution.
        """
        self._grid_spec = grid_spec or GridSpec(bbox=INDIA_BBOX)
        logger.info(
            "CommonGridder initialized: %dx%d grid at %.2f° resolution",
            self._grid_spec.nlat,
            self._grid_spec.nlon,
            self._grid_spec.resolution_deg,
        )

    @property
    def grid_spec(self) -> GridSpec:
        return self._grid_spec

    def run(
        self,
        geo_result: GeoAlignResult,
        analysis_time: datetime | None = None,
    ) -> CommonGridResult:
        """
        Regrid all aligned payloads to the common grid.

        Args:
            geo_result: Output from the geospatial alignment stage.
            analysis_time: The analysis time (for metadata).

        Returns:
            CommonGridResult containing a unified xarray.Dataset.
        """
        logger.info(
            "Starting regridding to common grid (%dx%d) with %d payloads",
            self._grid_spec.nlat,
            self._grid_spec.nlon,
            len(geo_result.aligned_payloads),
        )

        result = CommonGridResult(
            grid_spec=self._grid_spec,
            analysis_time=analysis_time,
        )

        target_lats = self._grid_spec.latitudes
        target_lons = self._grid_spec.longitudes

        data_vars: dict[str, xr.DataArray] = {}

        for payload in geo_result.aligned_payloads:
            try:
                var_name = payload.metadata.variable_name
                source = payload.metadata.source_name

                if isinstance(payload.data, xr.DataArray):
                    # Gridded data — interpolate to target grid
                    regridded = self._regrid_data_array(
                        payload.data, target_lats, target_lons, var_name
                    )
                    data_vars[var_name] = regridded
                    result.variables_included.append(var_name)

                    if payload.metadata.is_synthetic:
                        result.is_synthetic = True

                elif isinstance(payload.data, xr.Dataset):
                    for vname, da in payload.data.data_vars.items():
                        if not np.issubdtype(da.dtype, np.number):
                            continue
                        regridded = self._regrid_data_array(
                            da, target_lats, target_lons, vname
                        )
                        data_vars[vname] = regridded
                        result.variables_included.append(vname)
                        
                    if payload.metadata.is_synthetic:
                        result.is_synthetic = True

                elif isinstance(payload.data, LightningDataPayload):
                    # Lightning — bin into grid cells
                    flash_density = self._bin_lightning(
                        payload.data, target_lats, target_lons
                    )
                    data_vars["lightning_flash_density"] = flash_density
                    result.variables_included.append("lightning_flash_density")

                    if payload.metadata.is_synthetic:
                        result.is_synthetic = True

                else:
                    result.warnings.append(
                        f"Unknown data type for {var_name}: "
                        f"{type(payload.data).__name__}"
                    )

                logger.debug("Regridded %s from %s to common grid", var_name, source)

            except Exception as exc:
                warning = f"Failed to regrid {payload.metadata.variable_name}: {exc}"
                logger.warning(warning)
                result.warnings.append(warning)

        # Combine all variables into one Dataset
        if data_vars:
            result.dataset = xr.Dataset(
                data_vars=data_vars,
                attrs={
                    "analysis_time": str(analysis_time) if analysis_time else "unknown",
                    "grid_resolution_deg": self._grid_spec.resolution_deg,
                    "crs": "EPSG:4326",
                    "is_synthetic": result.is_synthetic,
                    "source": "SYNTHETIC" if result.is_synthetic else "MIXED",
                    "pipeline_stage": "common_grid",
                    "variables": list(data_vars.keys()),
                },
            )

        logger.info(
            "Common grid complete: %d variables regridded, "
            "%d missing, grid shape=%s",
            len(result.variables_included),
            len(result.variables_missing),
            self._grid_spec.shape,
        )

        return result

    def _regrid_data_array(
        self,
        data: xr.DataArray,
        target_lats: np.ndarray,
        target_lons: np.ndarray,
        var_name: str,
    ) -> xr.DataArray:
        """
        Interpolate a DataArray to the target grid.

        Checks if the coordinates are 1D (orthogonal) or 2D (geographic meshes).
        For 1D, uses xarray's interp.
        For 2D, uses scipy's griddata interpolation (nearest for categorical, linear for continuous).
        """
        is_2d = False
        lat_coord = None
        lon_coord = None
        
        for coord_name in data.coords:
            if "lat" in str(coord_name).lower():
                lat_coord = coord_name
            elif "lon" in str(coord_name).lower():
                lon_coord = coord_name
                
        if lat_coord and lon_coord and len(data.coords[lat_coord].shape) == 2:
            is_2d = True
            
        if not is_2d:
            try:
                # Use xarray's interp method for clean 1D interpolation
                regridded = data.interp(
                    latitude=target_lats,
                    longitude=target_lons,
                    method="linear",
                    kwargs={"fill_value": np.nan},
                )
            except Exception:
                # Fallback to nearest-neighbor if linear fails
                logger.debug("Linear interpolation failed for %s, using nearest", var_name)
                regridded = data.interp(
                    latitude=target_lats,
                    longitude=target_lons,
                    method="nearest",
                )
            method = "linear"
        else:
            import scipy.interpolate
            
            grid_lon, grid_lat = np.meshgrid(target_lons, target_lats)
            src_lats = data.coords[lat_coord].values.ravel()
            src_lons = data.coords[lon_coord].values.ravel()
            src_vals = data.values.ravel()
            
            valid = np.isfinite(src_lats) & np.isfinite(src_lons) & np.isfinite(src_vals)
            src_lats = src_lats[valid]
            src_lons = src_lons[valid]
            src_vals = src_vals[valid]
            
            # Subsample for huge arrays to maintain performance (e.g. VIS 1km grid has 12M points)
            if len(src_vals) > 500_000:
                step = int(np.ceil(len(src_vals) / 500_000))
                src_lats = src_lats[::step]
                src_lons = src_lons[::step]
                src_vals = src_vals[::step]
                
            is_categorical = "flag" in var_name.lower() or var_name.startswith("CSBT") or var_name.startswith("CLRFR")
            method = "nearest" if is_categorical else "linear"
            
            points = np.column_stack((src_lons, src_lats))
            try:
                regridded_vals = scipy.interpolate.griddata(
                    points, src_vals, (grid_lon, grid_lat), method=method
                )
            except Exception as e:
                logger.warning(f"Linear griddata failed for {var_name}: {e}. Falling back to nearest.")
                regridded_vals = scipy.interpolate.griddata(
                    points, src_vals, (grid_lon, grid_lat), method="nearest"
                )
                method = "nearest"
                
            from scipy.spatial import cKDTree
            tree = cKDTree(points)
            target_points = np.column_stack((grid_lon.ravel(), grid_lat.ravel()))
            distances, _ = tree.query(target_points, k=1)
            distances = distances.reshape(grid_lon.shape)
            
            mask = distances > self._grid_spec.max_interpolation_distance_deg
            # For categorical strings/objects we cannot use np.nan easily if type isn't float, 
            # but our source values are checked to be numeric in the run loop.
            if np.issubdtype(regridded_vals.dtype, np.integer):
                regridded_vals = regridded_vals.astype(float)
            regridded_vals[mask] = np.nan
                
            regridded = xr.DataArray(
                data=regridded_vals,
                dims=["latitude", "longitude"],
                coords={
                    "latitude": target_lats,
                    "longitude": target_lons,
                }
            )

        # Preserve important attributes
        regridded.attrs.update(data.attrs)
        regridded.attrs["regridded"] = True
        regridded.attrs["regrid_method"] = method
        regridded.name = var_name

        return regridded

    def _bin_lightning(
        self,
        lightning_data: LightningDataPayload,
        target_lats: np.ndarray,
        target_lons: np.ndarray,
    ) -> xr.DataArray:
        """
        Convert lightning point data to a gridded flash density field.

        Counts the number of flashes in each grid cell, then normalizes
        to flashes per km² per hour.
        """
        # Initialize an empty grid
        flash_counts = np.zeros((len(target_lats), len(target_lons)), dtype=np.float32)

        # Bin each flash into the nearest grid cell
        for flash in lightning_data.flashes:
            lat_idx = self._find_nearest_idx(target_lats, flash.latitude)
            lon_idx = self._find_nearest_idx(target_lons, flash.longitude)

            if 0 <= lat_idx < len(target_lats) and 0 <= lon_idx < len(target_lons):
                flash_counts[lat_idx, lon_idx] += 1.0

        # Create a DataArray with proper metadata
        flash_density = xr.DataArray(
            data=flash_counts,
            dims=["latitude", "longitude"],
            coords={
                "latitude": target_lats,
                "longitude": target_lons,
            },
            attrs={
                "units": "flashes/cell",
                "long_name": "Lightning Flash Density",
                "source": (
                    "SYNTHETIC" if lightning_data.metadata.is_synthetic else "OBSERVED"
                ),
                "variable_id": "lightning_flash_density",
                "is_synthetic": lightning_data.metadata.is_synthetic,
                "total_flashes": len(lightning_data.flashes),
                "regridded": True,
            },
            name="lightning_flash_density",
        )

        return flash_density

    @staticmethod
    def _find_nearest_idx(array: np.ndarray, value: float) -> int:
        """Find the index of the nearest value in an array."""
        return int(np.argmin(np.abs(array - value)))
