import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import scipy.interpolate

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.pipeline.ingestion import IngestionBatch, IngestionResult
from backend.pipeline.quality_control import QualityController
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder, GridSpec
from backend.app.models.data_types import DataSourceType, BoundingBox

def compute_stats(da, is_2d=False):
    vals = da.values.ravel()
    total = len(vals)
    valid_mask = np.isfinite(vals)
    valid_count = int(np.sum(valid_mask))
    valid_pct = valid_count / total * 100
    nan_pct = 100 - valid_pct
    
    valid_vals = vals[valid_mask]
    if len(valid_vals) == 0:
        return total, valid_count, valid_pct, nan_pct, np.nan, np.nan, np.nan
        
    vmin = float(np.min(valid_vals))
    vmax = float(np.max(valid_vals))
    vmed = float(np.median(valid_vals))
    return total, valid_count, valid_pct, nan_pct, vmin, vmax, vmed

def audit_common_grid():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    provider = MOSDACSatelliteProvider()
    gridder = CommonGridder()
    
    timestamps = [
        "2025-05-29 12:00",
        "2025-05-29 12:30",
        "2025-05-29 13:00",
        "2025-05-29 13:30",
        "2025-05-29 14:00",
        "2025-05-29 14:30"
    ]
    
    vars_to_check = ["IMG_TIR1", "IMG_WV", "CTT", "CTP"]
    
    audit_results = {
        "objective": "Verify CommonGridder output integrity",
        "target_grid": {
            "bbox": {"south": 8.4, "north": 37.6, "west": 68.7, "east": 97.2},
            "shape": gridder.grid_spec.shape
        },
        "timestamps": {}
    }
    
    for ts_str in timestamps:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        print(f"\nProcessing timestamp {ts_str}...")
        
        payload = provider.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
        ds = payload.data
        
        ts_results = {}
        
        geo_result = GeoAlignResult(aligned_payloads=[payload])
        grid_result = gridder.run(geo_result, analysis_time=ts)
        target_ds = grid_result.dataset
        
        for var in vars_to_check:
            if var not in ds.data_vars:
                continue
                
            native_da = ds[var]
            target_da = target_ds[var]
            
            # Find native lat/lon arrays for domain check
            lat_coord, lon_coord = None, None
            for coord in native_da.coords:
                if "lat" in coord.lower(): lat_coord = coord
                elif "lon" in coord.lower(): lon_coord = coord
                
            native_lats = native_da.coords[lat_coord].values.ravel()
            native_lons = native_da.coords[lon_coord].values.ravel()
            
            valid_latlons = np.isfinite(native_lats) & np.isfinite(native_lons)
            lat_min, lat_max = float(np.min(native_lats[valid_latlons])), float(np.max(native_lats[valid_latlons]))
            lon_min, lon_max = float(np.min(native_lons[valid_latlons])), float(np.max(native_lons[valid_latlons]))
            
            n_tot, n_val, n_v_pct, n_n_pct, n_min, n_max, n_med = compute_stats(native_da)
            t_tot, t_val, t_v_pct, t_n_pct, t_min, t_max, t_med = compute_stats(target_da)
            
            ts_results[var] = {
                "native": {
                    "total": n_tot,
                    "valid_count": n_val,
                    "valid_pct": n_v_pct,
                    "nan_pct": n_n_pct,
                    "min": n_min,
                    "max": n_max,
                    "median": n_med,
                    "domain": {
                        "lat_min": lat_min, "lat_max": lat_max,
                        "lon_min": lon_min, "lon_max": lon_max
                    }
                },
                "target": {
                    "total": t_tot,
                    "valid_count": t_val,
                    "valid_pct": t_v_pct,
                    "nan_pct": t_n_pct,
                    "min": t_min,
                    "max": t_max,
                    "median": t_med
                }
            }
            
            if ts_str == "2025-05-29 12:00" and var == "IMG_TIR1":
                # Subsampling check
                src_lats = native_lats
                src_lons = native_lons
                src_vals = native_da.values.ravel()
                
                valid = np.isfinite(src_lats) & np.isfinite(src_lons) & np.isfinite(src_vals)
                v_lats, v_lons, v_vals = src_lats[valid], src_lons[valid], src_vals[valid]
                
                # Check how interpolation fills gaps by checking bounds
                # If we drop NaNs, Delaunay connects over them.
                
                # Compare default downsample (500k points) to dense downsample (2M points)
                default_step = int(np.ceil(len(v_vals) / 500_000))
                dense_step = int(np.ceil(len(v_vals) / 2_000_000))
                
                target_lats = gridder.grid_spec.latitudes
                target_lons = gridder.grid_spec.longitudes
                grid_lon, grid_lat = np.meshgrid(target_lons, target_lats)
                
                print(f"Testing subsampling: default step={default_step}, dense step={dense_step}")
                
                d1 = scipy.interpolate.griddata(
                    np.column_stack((v_lons[::default_step], v_lats[::default_step])),
                    v_vals[::default_step],
                    (grid_lon, grid_lat),
                    method="linear"
                )
                
                d2 = scipy.interpolate.griddata(
                    np.column_stack((v_lons[::dense_step], v_lats[::dense_step])),
                    v_vals[::dense_step],
                    (grid_lon, grid_lat),
                    method="linear"
                )
                
                valid_both = np.isfinite(d1) & np.isfinite(d2)
                if np.sum(valid_both) > 0:
                    abs_diff = np.abs(d1[valid_both] - d2[valid_both])
                    audit_results["subsampling_audit"] = {
                        "variable": "IMG_TIR1",
                        "default_sample_size": len(v_vals[::default_step]),
                        "dense_sample_size": len(v_vals[::dense_step]),
                        "max_abs_diff": float(np.max(abs_diff)),
                        "mean_abs_diff": float(np.mean(abs_diff)),
                        "median_abs_diff": float(np.median(abs_diff))
                    }
                
        audit_results["timestamps"][ts_str] = ts_results
        
    with open(r"C:\Users\Vedant\Desktop\sih comeback\docs\common_grid_integrity_audit.json", "w") as f:
        json.dump(audit_results, f, indent=2)
        
    print("\nAudit completed. JSON written.")

if __name__ == "__main__":
    audit_common_grid()
