"""
StormFusion AI — INSAT-3DS Real Data Parser

This module provides READ-ONLY ingestion of the raw HDF5 files 
for INSAT-3DS. It extracts data, applies scaling, handles fill values,
and packages the multi-resolution grids into an xarray Dataset.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import xarray as xr

from backend.app.models.data_types import DataSourceType, BoundingBox
from backend.app.models.metadata import DatasetMetadata
from backend.app.models.payload import DataPayload

logger = logging.getLogger(__name__)

class INSAT3DSParserError(Exception):
    """Exception raised for errors during INSAT-3DS parsing."""
    pass

class INSAT3DSParser:
    """
    Parser for real INSAT-3DS HDF5 products.
    """

    @staticmethod
    def _parse_timestamp(time_str: str) -> datetime:
        """Parse '29-MAY-2025T12:00:15.568' into UTC datetime."""
        try:
            dt = datetime.strptime(time_str, "%d-%b-%YT%H:%M:%S.%f")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError as e:
            logger.warning(f"Could not parse timestamp {time_str}, fallback to current time.")
            return datetime.now(timezone.utc)

    @staticmethod
    def _read_dataset(h5_group: h5py.Group, var_name: str) -> tuple[np.ndarray, dict]:
        """
        Safely reads a dataset, handles _FillValue, scale_factor, add_offset,
        and removes singleton leading dimensions.
        """
        if var_name not in h5_group:
            raise INSAT3DSParserError(f"Missing required dataset: {var_name}")
            
        ds = h5_group[var_name]
        data = ds[:]
        
        # Squeeze singleton dimension if it's the first dimension (time/band)
        if len(data.shape) > 2 and data.shape[0] == 1:
            data = data[0]
            
        # Extract attributes
        attrs = ds.attrs
        
        # Convert to float to handle NaN safely, unless it's string
        if np.issubdtype(data.dtype, np.number):
            data = data.astype(np.float32)
            
            fill_value = None
            if "_FillValue" in attrs:
                fill_value = attrs["_FillValue"][0] if hasattr(attrs["_FillValue"], '__iter__') else attrs["_FillValue"]
                
            if fill_value is not None:
                data[data == fill_value] = np.nan
                
            # Apply scaling: data = data * scale_factor + add_offset
            scale = attrs.get("scale_factor", [1.0])[0] if hasattr(attrs.get("scale_factor"), '__iter__') else attrs.get("scale_factor", 1.0)
            offset = attrs.get("add_offset", [0.0])[0] if hasattr(attrs.get("add_offset"), '__iter__') else attrs.get("add_offset", 0.0)
            
            # Explicitly checking against default to avoid unnecessary ops
            if scale != 1.0 or offset != 0.0:
                data = (data * scale) + offset
                
        return data, attrs

    @staticmethod
    def parse_l1b_file(filepath: Path) -> DataPayload:
        """
        Parse an INSAT-3DS L1B Standard file.
        Extracts VIS, SWIR (1km) and MIR, WV, TIR1, TIR2 (4km).
        """
        if not filepath.exists():
            raise INSAT3DSParserError(f"File not found: {filepath}")
            
        try:
            with h5py.File(filepath, 'r') as f:
                # 1. Root Metadata
                root_attrs = {k: v for k, v in f.attrs.items()}
                
                acq_start = root_attrs.get("Acquisition_Start_Time", "")
                if hasattr(acq_start, "tolist"):
                    acq_start = acq_start.tolist()
                if isinstance(acq_start, (list, tuple)) and len(acq_start) > 0:
                    acq_start = acq_start[0]
                if isinstance(acq_start, bytes):
                    acq_start = acq_start.decode("utf-8")
                
                timestamp = INSAT3DSParser._parse_timestamp(str(acq_start))
                
                # 2. Geolocation extraction
                lat_ir, _ = INSAT3DSParser._read_dataset(f, "Latitude")
                lon_ir, _ = INSAT3DSParser._read_dataset(f, "Longitude")
                lat_vis, _ = INSAT3DSParser._read_dataset(f, "Latitude_VIS")
                lon_vis, _ = INSAT3DSParser._read_dataset(f, "Longitude_VIS")
                
                xr_dataset = xr.Dataset()
                
                # Add IR/WV (4km)
                for var in ["IMG_MIR", "IMG_WV", "IMG_TIR1", "IMG_TIR2"]:
                    if var in f:
                        data, attrs = INSAT3DSParser._read_dataset(f, var)
                        da = xr.DataArray(
                            data=data,
                            dims=["y_ir", "x_ir"],
                            coords={
                                "latitude_ir": (["y_ir", "x_ir"], lat_ir),
                                "longitude_ir": (["y_ir", "x_ir"], lon_ir),
                            },
                            attrs={
                                "units": str(attrs.get("radiance_units", b"").decode('utf-8') if isinstance(attrs.get("radiance_units"), bytes) else attrs.get("radiance_units", "")),
                                "long_name": str(attrs.get("long_name", b"").decode('utf-8') if isinstance(attrs.get("long_name"), bytes) else attrs.get("long_name", "")),
                                "source": "MOSDAC",
                                "is_synthetic": False
                            }
                        )
                        xr_dataset[var] = da
                        
                # Add VIS/SWIR (1km)
                for var in ["IMG_VIS", "IMG_SWIR"]:
                    if var in f:
                        data, attrs = INSAT3DSParser._read_dataset(f, var)
                        da = xr.DataArray(
                            data=data,
                            dims=["y_vis", "x_vis"],
                            coords={
                                "latitude_vis": (["y_vis", "x_vis"], lat_vis),
                                "longitude_vis": (["y_vis", "x_vis"], lon_vis),
                            },
                            attrs={
                                "units": str(attrs.get("radiance_units", b"").decode('utf-8') if isinstance(attrs.get("radiance_units"), bytes) else attrs.get("radiance_units", "")),
                                "long_name": str(attrs.get("long_name", b"").decode('utf-8') if isinstance(attrs.get("long_name"), bytes) else attrs.get("long_name", "")),
                                "source": "MOSDAC",
                                "is_synthetic": False
                            }
                        )
                        xr_dataset[var] = da
                        
                xr_dataset.attrs["acquisition_time"] = timestamp.isoformat()
                xr_dataset.attrs["product_type"] = "L1B_STD"
                xr_dataset.attrs["source"] = "MOSDAC"
                
                # Calculate bounding box from IR lat/lon
                # Ignore NaNs
                bbox = BoundingBox(
                    south=float(np.nanmin(lat_ir)),
                    north=float(np.nanmax(lat_ir)),
                    west=float(np.nanmin(lon_ir)),
                    east=float(np.nanmax(lon_ir))
                )
                
                metadata = DatasetMetadata(
                    dataset_id=filepath.stem,
                    source_type=DataSourceType.SATELLITE,
                    source_name="MOSDAC",
                    variable_name="L1B_Radiance",
                    units="mixed",
                    time_start=timestamp,
                    time_end=timestamp,
                    bounding_box=bbox,
                    spatial_resolution_km=4.0, # base resolution
                    file_format="HDF5",
                    file_path=filepath,
                    is_synthetic=False,
                    extra={"product": "INSAT-3DS"}
                )
                
                return DataPayload(metadata=metadata, data=xr_dataset)
                
        except Exception as e:
            raise INSAT3DSParserError(f"Failed to parse L1B file {filepath}: {e}")

    @staticmethod
    def parse_ctp_file(filepath: Path) -> DataPayload:
        """
        Parse an INSAT-3DS L2B CTP file.
        Extracts Cloud Top Properties on the native grid.
        """
        if not filepath.exists():
            raise INSAT3DSParserError(f"File not found: {filepath}")
            
        try:
            with h5py.File(filepath, 'r') as f:
                root_attrs = {k: v for k, v in f.attrs.items()}
                
                acq_start = root_attrs.get("Acquisition_Start_Time", "")
                if hasattr(acq_start, "tolist"):
                    acq_start = acq_start.tolist()
                if isinstance(acq_start, (list, tuple)) and len(acq_start) > 0:
                    acq_start = acq_start[0]
                if isinstance(acq_start, bytes):
                    acq_start = acq_start.decode("utf-8")
                
                timestamp = INSAT3DSParser._parse_timestamp(str(acq_start))
                
                lat, _ = INSAT3DSParser._read_dataset(f, "Latitude")
                lon, _ = INSAT3DSParser._read_dataset(f, "Longitude")
                
                xr_dataset = xr.Dataset()
                
                # Variables of interest in CTP
                vars_to_extract = ["CTP", "CTT", "EFF_EMISS"]
                # Also detect CSBT and CLRFR
                for key in f.keys():
                    if key.startswith("CSBT_") or key.startswith("CLRFR_"):
                        vars_to_extract.append(key)
                        
                for var in vars_to_extract:
                    if var in f:
                        # Some CSBT/CLRFR might have different dimensions (e.g. 325x325 vs 313x312).
                        # Let's check shape explicitly.
                        ds = f[var]
                        data_shape = list(ds.shape)
                        if len(data_shape) > 2 and data_shape[0] == 1:
                            data_shape = data_shape[1:]
                            
                        # Only add if it matches the main latitude/longitude grid (313, 312).
                        # If it is 325x325, we skip it or we would need a secondary lat/lon (like CSBT_Latitude).
                        if tuple(data_shape) == tuple(lat.shape):
                            data, attrs = INSAT3DSParser._read_dataset(f, var)
                            da = xr.DataArray(
                                data=data,
                                dims=["y_ctp", "x_ctp"],
                                coords={
                                    "latitude": (["y_ctp", "x_ctp"], lat),
                                    "longitude": (["y_ctp", "x_ctp"], lon),
                                },
                                attrs={
                                    "units": str(attrs.get("units", b"").decode('utf-8') if isinstance(attrs.get("units"), bytes) else attrs.get("units", "")),
                                    "long_name": str(attrs.get("long_name", b"").decode('utf-8') if isinstance(attrs.get("long_name"), bytes) else attrs.get("long_name", "")),
                                    "source": "MOSDAC",
                                    "is_synthetic": False
                                }
                            )
                            xr_dataset[var] = da
                            
                xr_dataset.attrs["acquisition_time"] = timestamp.isoformat()
                xr_dataset.attrs["product_type"] = "L2B_CTP"
                xr_dataset.attrs["source"] = "MOSDAC"
                
                bbox = BoundingBox(
                    south=float(np.nanmin(lat)),
                    north=float(np.nanmax(lat)),
                    west=float(np.nanmin(lon)),
                    east=float(np.nanmax(lon))
                )
                
                metadata = DatasetMetadata(
                    dataset_id=filepath.stem,
                    source_type=DataSourceType.SATELLITE,
                    source_name="MOSDAC",
                    variable_name="CTP",
                    units="mixed",
                    time_start=timestamp,
                    time_end=timestamp,
                    bounding_box=bbox,
                    spatial_resolution_km=4.0, # roughly
                    file_format="HDF5",
                    file_path=filepath,
                    is_synthetic=False,
                    extra={"product": "INSAT-3DS"}
                )
                
                return DataPayload(metadata=metadata, data=xr_dataset)
                
        except Exception as e:
            raise INSAT3DSParserError(f"Failed to parse CTP file {filepath}: {e}")
