import pytest
import numpy as np
import xarray as xr
from datetime import datetime
from backend.pipeline.common_grid import CommonGridder, GridSpec
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.app.models.payload import DataPayload, DatasetMetadata
from backend.app.models.data_types import DataSourceType, BoundingBox

def create_payload(lats, lons, values, var_name="test_var", is_2d=True):
    if is_2d:
        coords = {"latitude_2d": (["y", "x"], lats), "longitude_2d": (["y", "x"], lons)}
        dims = ["y", "x"]
    else:
        coords = {"latitude": lats, "longitude": lons}
        dims = ["latitude", "longitude"]
        
    da = xr.DataArray(
        data=values,
        dims=dims,
        coords=coords,
        attrs={"source": "SYNTHETIC", "units": "K"}
    )
    
    metadata = DatasetMetadata(
        dataset_id="test_ds",
        source_type=DataSourceType.SATELLITE,
        source_name="Synthetic",
        variable_name=var_name,
        units="K",
        time_start=datetime.utcnow(),
        time_end=datetime.utcnow(),
        bounding_box=BoundingBox(south=10, north=30, west=70, east=90),
        spatial_resolution_km=4.0
    )
    return DataPayload(metadata=metadata, data=da)

def test_internal_nan_region():
    # 1. Synthetic source grid containing a large internal NaN region.
    # Expected: interpolation must NOT fabricate values throughout the missing region.
    y, x = np.mgrid[10:30:1.0, 70:90:1.0]
    vals = np.ones_like(y)
    
    # Create large internal NaN region (from lat 15 to 25, lon 75 to 85)
    mask = (y > 15) & (y < 25) & (x > 75) & (x < 85)
    vals[mask] = np.nan
    
    payload = create_payload(y, x, vals)
    geo_result = GeoAlignResult(aligned_payloads=[payload])
    
    # Create gridder over India
    gridder = CommonGridder(GridSpec(bbox=BoundingBox(south=10, north=30, west=70, east=90), resolution_deg=1.0, max_interpolation_distance_deg=1.5))
    result = gridder.run(geo_result)
    
    ds = result.dataset["test_var"]
    
    # Center of the NaN region should be NaN (e.g. lat 20, lon 80)
    # The nearest valid point is ~5 degrees away, which is > 1.5 deg threshold.
    val_at_center = float(ds.sel(latitude=20, longitude=80, method="nearest"))
    assert np.isnan(val_at_center)
    
def test_distance_thresholds():
    # 2. Target point sufficiently close to valid observations -> remains valid.
    # 3. Target point farther than the configured support threshold -> becomes NaN.
    
    # Single valid point at (20, 80)
    y, x = np.array([[20.0]]), np.array([[80.0]])
    vals = np.array([[100.0]])
    
    payload = create_payload(y, x, vals)
    geo_result = GeoAlignResult(aligned_payloads=[payload])
    
    gridder = CommonGridder(GridSpec(bbox=BoundingBox(south=15, north=25, west=75, east=85), resolution_deg=1.0, max_interpolation_distance_deg=2.5))
    result = gridder.run(geo_result)
    ds = result.dataset["test_var"]
    
    # Point at (20, 80) is 0 distance -> Valid
    assert not np.isnan(float(ds.sel(latitude=20, longitude=80, method="nearest")))
    
    # Point at (20, 82) is 2.0 degrees away -> <= 2.5 -> Valid
    assert not np.isnan(float(ds.sel(latitude=20, longitude=82, method="nearest")))
    
    # Point at (24, 80) is 4.0 degrees away -> > 2.5 -> NaN
    assert np.isnan(float(ds.sel(latitude=24, longitude=80, method="nearest")))

def test_outer_nan_region():
    # 4. Source grid whose outer region is NaN.
    # Expected: off-domain target cells remain invalid.
    y, x = np.mgrid[10:30:1.0, 70:90:1.0]
    vals = np.ones_like(y)
    
    # Outer border is NaN
    mask = (y < 15) | (y > 25) | (x < 75) | (x > 85)
    vals[mask] = np.nan
    
    payload = create_payload(y, x, vals)
    geo_result = GeoAlignResult(aligned_payloads=[payload])
    
    gridder = CommonGridder(GridSpec(bbox=BoundingBox(south=10, north=30, west=70, east=90), resolution_deg=1.0, max_interpolation_distance_deg=1.5))
    result = gridder.run(geo_result)
    ds = result.dataset["test_var"]
    
    # Inside point -> valid
    assert not np.isnan(float(ds.sel(latitude=20, longitude=80, method="nearest")))
    # Outer point (far from valid boundary 15/25/75/85) -> NaN
    assert np.isnan(float(ds.sel(latitude=12, longitude=72, method="nearest")))

def test_sparse_ctp_observations():
    # 5. CTP/CTT-like sparse valid observations.
    # Expected: missing regions remain represented as missing where unsupported.
    y, x = np.mgrid[10:30:1.0, 70:90:1.0]
    vals = np.full_like(y, np.nan)
    
    # Sparse clouds
    vals[10:12, 10:12] = 200 # cloud 1
    vals[18:20, 18:20] = 300 # cloud 2
    
    payload = create_payload(y, x, vals)
    geo_result = GeoAlignResult(aligned_payloads=[payload])
    
    gridder = CommonGridder(GridSpec(bbox=BoundingBox(south=10, north=30, west=70, east=90), resolution_deg=1.0, max_interpolation_distance_deg=1.5))
    result = gridder.run(geo_result)
    ds = result.dataset["test_var"]
    
    # Cloud center valid
    assert not np.isnan(float(ds.sel(latitude=y[11, 11], longitude=x[11, 11], method="nearest")))
    
    # Clear sky invalid (far from clouds)
    assert np.isnan(float(ds.sel(latitude=y[15, 15], longitude=x[15, 15], method="nearest")))
