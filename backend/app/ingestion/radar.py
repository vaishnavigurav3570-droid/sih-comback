"""
StormFusion AI — Real Radar Data Parser
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import xarray as xr
import pyproj

from backend.app.models.radar import RadarMetadata

logger = logging.getLogger(__name__)

class RadarParserError(Exception):
    pass

class RadarParser:
    """Parser for real CF/Radial radar data."""
    
    @staticmethod
    def _parse_timestamp(time_str: str) -> datetime:
        """Parse ISO-like timestamp."""
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    @staticmethod
    def parse_radar_file(filepath: Path, target_threshold: float = 35.0) -> dict:
        """
        Parse radar NetCDF file and return structured data.
        """
        if not filepath.exists():
            raise RadarParserError(f"File not found: {filepath}")
            
        try:
            ds = xr.open_dataset(filepath, decode_times=False)
            
            # Extract metadata
            radar_id = ds.attrs.get("instrument_name", "UNKNOWN")
            lat = float(ds["latitude"].values)
            lon = float(ds["longitude"].values)
            alt = float(ds["altitude"].values)
            
            # Extract time_coverage_start and time_coverage_end from variables
            if "time_coverage_start" in ds:
                t_start = ds["time_coverage_start"].values.item()
                time_start_raw = t_start.decode("utf-8") if isinstance(t_start, bytes) else str(t_start)
            else:
                time_start_raw = ""
                
            if "time_coverage_end" in ds:
                t_end = ds["time_coverage_end"].values.item()
                time_end_raw = t_end.decode("utf-8") if isinstance(t_end, bytes) else str(t_end)
            else:
                time_end_raw = ""
            
            start_time = RadarParser._parse_timestamp(time_start_raw)
            end_time = RadarParser._parse_timestamp(time_end_raw)
            
            sweep_count = len(ds["sweep"])
            
            # Extract main variables
            vars_to_extract = ["REF", "VEL", "WIDTH"]
            available_fields = [v for v in vars_to_extract if v in ds]
            
            data_vars = {}
            for var in available_fields:
                vals = ds[var].values.astype(np.float32)
                # Fill values are typically > 1e30
                vals[vals > 1e30] = np.nan
                data_vars[var] = vals
                
            units = {v: ds[v].attrs.get("units", "") for v in available_fields}
            
            # Construct metadata
            metadata = RadarMetadata(
                source_name=f"IMD DWR {radar_id}",
                radar_id=radar_id,
                latitude=lat,
                longitude=lon,
                altitude=alt,
                start_time=start_time,
                end_time=end_time,
                sweep_count=sweep_count,
                field_names=available_fields,
                units=units,
                provenance="Real CF/Radial Radar Data",
                is_synthetic=False,
                file_path=str(filepath)
            )
            
            # Reflectivity target (EVENT, NON-EVENT, MISSING)
            # EVENT=1, NON-EVENT=0, MISSING=NaN
            if "REF" in data_vars:
                ref = data_vars["REF"]
                target = np.full_like(ref, np.nan)
                valid_mask = np.isfinite(ref)
                target[valid_mask] = (ref[valid_mask] >= target_threshold).astype(np.float32)
                data_vars["TARGET"] = target
                
            # Geographic coordinates
            range_vals = ds["range"].values
            azimuth_vals = ds["azimuth"].values
            elevation_vals = ds["elevation"].values
            
            # Simple Azimuthal Equidistant projection (spherical approx)
            proj = pyproj.Proj(proj='aeqd', lat_0=lat, lon_0=lon, ellps='WGS84')
            
            az_2d = np.broadcast_to(azimuth_vals[:, np.newaxis], (len(azimuth_vals), len(range_vals)))
            el_2d = np.broadcast_to(elevation_vals[:, np.newaxis], (len(elevation_vals), len(range_vals)))
            r_2d = np.broadcast_to(range_vals[np.newaxis, :], (len(azimuth_vals), len(range_vals)))
            
            r_horiz = r_2d * np.cos(np.radians(el_2d))
            
            x = r_horiz * np.sin(np.radians(az_2d))
            y = r_horiz * np.cos(np.radians(az_2d))
            
            geo_lon, geo_lat = proj(x, y, inverse=True)
            
            geo_coords = {
                "latitude": geo_lat,
                "longitude": geo_lon,
                "range": r_2d,
                "azimuth": az_2d,
                "elevation": el_2d
            }
            
            return {
                "metadata": metadata,
                "data": data_vars,
                "coordinates": geo_coords
            }
            
        except Exception as e:
            raise RadarParserError(f"Failed to parse radar file: {e}")
