"""
StormFusion AI — Satellite Nowcast Demo (Fast Path)

Demonstrates the deterministic physics-informed nowcast prototype
using real INSAT-3DS HDF5 data, bypassing the slow full-pipeline
griddata/KDTree regridding by using a fast nearest-neighbor lookup.

This is NOT an ML prediction. Outputs are labeled SATELLITE-DERIVED.
"""
import sys
import logging
import os
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ingestion.insat3ds import INSAT3DSParser
from backend.pipeline.satellite_nowcast import SatelliteNowcastPrototype

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables needed for nowcast
NEEDED_VARS = ["IMG_TIR1", "IMG_TIR2", "CTT", "CTP"]

# Target grid
TARGET_LATS = np.arange(6.0, 38.5, 0.5)   # 65 points
TARGET_LONS = np.arange(68.0, 98.5, 0.5)   # 61 points


def fast_regrid_2d(data_values: np.ndarray, src_lats: np.ndarray, src_lons: np.ndarray,
                    target_lats: np.ndarray, target_lons: np.ndarray) -> np.ndarray:
    """
    Fast nearest-neighbor regridding from 2D satellite coords to regular grid.
    
    Instead of building a full KD-tree, we use a direct index-mapping approach:
    for each target grid cell, find the nearest source pixel using vectorized
    operations on the subsampled source grid.
    """
    nlat, nlon = len(target_lats), len(target_lons)
    result = np.full((nlat, nlon), np.nan, dtype=np.float32)
    
    # Subsample source for speed — take every Nth pixel
    step = max(1, min(src_lats.shape[0], src_lats.shape[1]) // 200)
    sub_lats = src_lats[::step, ::step]
    sub_lons = src_lons[::step, ::step]
    sub_vals = data_values[::step, ::step]
    
    # Flatten
    flat_lats = sub_lats.ravel()
    flat_lons = sub_lons.ravel()
    flat_vals = sub_vals.ravel()
    
    # Filter valid
    valid = np.isfinite(flat_lats) & np.isfinite(flat_lons) & np.isfinite(flat_vals)
    flat_lats = flat_lats[valid]
    flat_lons = flat_lons[valid]
    flat_vals = flat_vals[valid]
    
    if len(flat_vals) == 0:
        return result
    
    # For each target cell, find nearest source pixel
    for i, tlat in enumerate(target_lats):
        for j, tlon in enumerate(target_lons):
            dist_sq = (flat_lats - tlat)**2 + (flat_lons - tlon)**2
            idx = np.argmin(dist_sq)
            if dist_sq[idx] < 1.0:  # within ~1 degree
                result[i, j] = flat_vals[idx]
    
    return result


def load_and_regrid_timestamp(mosdac_dir: Path, hhmm: str) -> dict[str, np.ndarray] | None:
    """Load INSAT-3DS L1B + CTP for one timestamp and regrid to common grid."""
    l1b_file = mosdac_dir / f"3SIMG_29MAY2025_{hhmm}_L1B_STD_V01R00.h5"
    ctp_file = mosdac_dir / f"3SIMG_29MAY2025_{hhmm}_L2B_CTP_V01R00.h5"
    
    if not l1b_file.exists():
        logger.warning(f"L1B file not found: {l1b_file}")
        return None
    if not ctp_file.exists():
        logger.warning(f"CTP file not found: {ctp_file}")
        return None
    
    logger.info(f"  Parsing L1B: {l1b_file.name}")
    p_l1b = INSAT3DSParser.parse_l1b_file(l1b_file)
    logger.info(f"  Parsing CTP: {ctp_file.name}")
    p_ctp = INSAT3DSParser.parse_ctp_file(ctp_file)
    
    ds_l1b = p_l1b.data
    ds_ctp = p_ctp.data
    
    result = {}
    
    # Regrid each needed variable
    for var_name in NEEDED_VARS:
        src_ds = ds_l1b if var_name.startswith("IMG_") else ds_ctp
        if var_name not in src_ds.data_vars:
            logger.warning(f"  Variable {var_name} not found in dataset, skipping")
            continue
            
        da = src_ds[var_name]
        values = da.values.astype(np.float32)
        if values.ndim > 2:
            values = np.squeeze(values)
            
        # Get lat/lon for this specific variable
        var_lat_coord = None
        var_lon_coord = None
        for coord_name in da.coords:
            if "lat" in coord_name.lower():
                var_lat_coord = coord_name
            elif "lon" in coord_name.lower():
                var_lon_coord = coord_name
                
        if not var_lat_coord or not var_lon_coord:
            logger.error(f"Could not find lat/lon for {var_name}")
            continue
            
        var_lats = da.coords[var_lat_coord].values
        var_lons = da.coords[var_lon_coord].values
        
        if var_lats.ndim == 1:
            var_lons_2d, var_lats_2d = np.meshgrid(var_lons, var_lats)
        else:
            var_lats_2d = var_lats
            var_lons_2d = var_lons
            
        regridded = fast_regrid_2d(values, var_lats_2d, var_lons_2d, TARGET_LATS, TARGET_LONS)
        
        valid_frac = np.sum(np.isfinite(regridded)) / regridded.size
        logger.info(f"  {var_name}: regridded to {regridded.shape}, valid={valid_frac:.1%}")
        result[var_name] = regridded
    
    return result


def run_demo():
    mosdac_dir = Path(r"C:\Users\Vedant\Documents\mosdac")
    if not mosdac_dir.exists():
        logger.error(f"MOSDAC directory not found: {mosdac_dir}")
        return
    
    timestamps = [
        ("1200", datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)),
        ("1230", datetime(2025, 5, 29, 12, 30, tzinfo=timezone.utc)),
        ("1300", datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)),
        ("1330", datetime(2025, 5, 29, 13, 30, tzinfo=timezone.utc)),
        ("1400", datetime(2025, 5, 29, 14, 0, tzinfo=timezone.utc)),
        ("1430", datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)),
    ]
    
    nowcast = SatelliteNowcastPrototype()
    
    logger.info("=" * 60)
    logger.info("StormFusion AI — Satellite Nowcast Demo (Fast Path)")
    logger.info("=" * 60)
    logger.info(f"Grid: {len(TARGET_LATS)}x{len(TARGET_LONS)} @ 0.5°")
    logger.info(f"Lat: {TARGET_LATS[0]:.1f}°N to {TARGET_LATS[-1]:.1f}°N")
    logger.info(f"Lon: {TARGET_LONS[0]:.1f}°E to {TARGET_LONS[-1]:.1f}°E")
    logger.info(f"Timestamps: {len(timestamps)}")
    logger.info("")
    
    t0 = time.time()
    
    # Load and regrid all timestamps
    frames = []
    for hhmm, ts in timestamps:
        logger.info(f"Loading timestamp: {ts} ({hhmm})")
        data = load_and_regrid_timestamp(mosdac_dir, hhmm)
        if data:
            frames.append((ts, data))
            logger.info(f"  OK: {len(data)} variables loaded")
        else:
            logger.warning(f"  SKIP: Could not load {hhmm}")
    
    load_time = time.time() - t0
    logger.info(f"\nLoaded {len(frames)}/{len(timestamps)} timestamps in {load_time:.1f}s")
    
    if len(frames) < 2:
        logger.error("Need at least 2 frames for temporal analysis. Exiting.")
        return
    
    # Run nowcast on consecutive pairs
    output_dir = Path("nowcast_output")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("Running nowcast analysis...")
    logger.info("=" * 60)
    
    for i in range(1, len(frames)):
        ts_prev, data_prev = frames[i - 1]
        ts_curr, data_curr = frames[i]
        
        logger.info(f"\nNowcast: {ts_prev.strftime('%H:%M')} → {ts_curr.strftime('%H:%M')} UTC")
        
        # Compute indicator components
        result = {}
        
        # 1. Cooling rate (temporal difference in TIR1)
        if "IMG_TIR1" in data_prev and "IMG_TIR1" in data_curr:
            tir1_prev = data_prev["IMG_TIR1"]
            tir1_curr = data_curr["IMG_TIR1"]
            
            # Cooling rate: negative means cloud tops are getting colder (convective growth)
            cooling = tir1_curr - tir1_prev  # negative = cooling
            
            # Normalize: strong cooling (-20K in 30min) → 1.0
            cooling_indicator = np.clip(-cooling / 20.0, 0.0, 1.0)
            cooling_indicator = np.where(
                np.isfinite(cooling_indicator), cooling_indicator, 0.0
            ).astype(np.float32)
            
            result["cooling_rate"] = cooling_indicator
            logger.info(f"  Cooling rate: max={np.nanmax(cooling_indicator):.3f}, mean={np.nanmean(cooling_indicator):.3f}")
        
        # 2. Split-window difference (TIR1 - TIR2)
        if "IMG_TIR1" in data_curr and "IMG_TIR2" in data_curr:
            split = data_curr["IMG_TIR1"] - data_curr["IMG_TIR2"]
            # Large split-window → optically thick cloud
            split_indicator = np.clip(np.abs(split) / 10.0, 0.0, 1.0)
            split_indicator = np.where(
                np.isfinite(split_indicator), split_indicator, 0.0
            ).astype(np.float32)
            
            result["split_window"] = split_indicator
            logger.info(f"  Split-window: max={np.nanmax(split_indicator):.3f}, mean={np.nanmean(split_indicator):.3f}")
        
        # 3. Spatial gradient of TIR1 (cloud boundary sharpness)
        if "IMG_TIR1" in data_curr:
            tir1 = data_curr["IMG_TIR1"].copy()
            tir1[~np.isfinite(tir1)] = np.nanmedian(tir1[np.isfinite(tir1)])
            
            grad_lat = np.gradient(tir1, axis=0)
            grad_lon = np.gradient(tir1, axis=1)
            grad_mag = np.sqrt(grad_lat**2 + grad_lon**2)
            
            # Normalize: strong gradient (>10K per cell) → 1.0
            grad_indicator = np.clip(grad_mag / 10.0, 0.0, 1.0).astype(np.float32)
            
            result["spatial_gradient"] = grad_indicator
            logger.info(f"  Spatial gradient: max={np.nanmax(grad_indicator):.3f}, mean={np.nanmean(grad_indicator):.3f}")
        
        # 4. Cloud-top pressure (low pressure = tall cloud = convective)
        if "CTP" in data_curr:
            ctp = data_curr["CTP"]
            # Low CTP (<300 hPa) → tall convective cloud → indicator 1.0
            # High CTP (>700 hPa) → low cloud → indicator 0.0
            ctp_indicator = np.clip((700.0 - ctp) / 400.0, 0.0, 1.0)
            ctp_indicator = np.where(
                np.isfinite(ctp_indicator), ctp_indicator, 0.0
            ).astype(np.float32)
            
            result["cloud_top_pressure"] = ctp_indicator
            logger.info(f"  CTP indicator: max={np.nanmax(ctp_indicator):.3f}, mean={np.nanmean(ctp_indicator):.3f}")
        
        # Combine into storm development indicator
        indicators = list(result.values())
        if indicators:
            combined = np.mean(indicators, axis=0).astype(np.float32)
        else:
            combined = np.zeros((len(TARGET_LATS), len(TARGET_LONS)), dtype=np.float32)
        
        # Validity mask
        validity = np.ones_like(combined, dtype=bool)
        for ind in indicators:
            validity &= np.isfinite(ind) & (ind >= 0)
        
        # Simple motion estimation using phase correlation on TIR1
        motion_u, motion_v = 0.0, 0.0
        motion_quality = 0.0
        if "IMG_TIR1" in data_prev and "IMG_TIR1" in data_curr:
            try:
                from scipy.fft import fft2, ifft2
                
                a = data_prev["IMG_TIR1"].copy()
                b = data_curr["IMG_TIR1"].copy()
                a[~np.isfinite(a)] = np.nanmedian(a[np.isfinite(a)])
                b[~np.isfinite(b)] = np.nanmedian(b[np.isfinite(b)])
                
                fa = fft2(a)
                fb = fft2(b)
                cross = fa * np.conj(fb)
                cross /= np.abs(cross) + 1e-10
                corr = np.abs(ifft2(cross))
                
                peak = np.unravel_index(np.argmax(corr), corr.shape)
                ny, nx = corr.shape
                dy = peak[0] if peak[0] < ny // 2 else peak[0] - ny
                dx = peak[1] if peak[1] < nx // 2 else peak[1] - nx
                
                motion_v = float(dy) * 0.5  # degrees per 30 min
                motion_u = float(dx) * 0.5
                motion_quality = float(np.max(corr)) / float(np.mean(corr) + 1e-10)
                motion_quality = min(motion_quality / 10.0, 1.0)
                
                logger.info(f"  Motion: u={motion_u:.2f}°, v={motion_v:.2f}°, quality={motion_quality:.3f}")
            except Exception as e:
                logger.warning(f"  Motion estimation failed: {e}")
        
        motion_speed = np.sqrt(motion_u**2 + motion_v**2)
        motion_dir = np.degrees(np.arctan2(motion_u, motion_v)) % 360
        
        # Extrapolate indicator using motion
        extrapolated = combined.copy()
        if abs(motion_u) > 0.01 or abs(motion_v) > 0.01:
            from scipy.ndimage import shift
            shift_y = -motion_v / 0.5  # convert degrees to grid cells
            shift_x = -motion_u / 0.5
            extrapolated = shift(combined, [shift_y, shift_x], mode='constant', cval=0.0).astype(np.float32)
        
        # Save to NetCDF
        ts_str = ts_curr.strftime("%Y%m%dT%H%M")
        ds = xr.Dataset(
            {
                "storm_development_indicator": (["latitude", "longitude"], combined),
                "indicator_validity_mask": (["latitude", "longitude"], validity.astype(np.float32)),
                "extrapolated_indicator": (["latitude", "longitude"], extrapolated),
                "cooling_rate_component": (["latitude", "longitude"], result.get("cooling_rate", np.zeros_like(combined))),
                "split_window_component": (["latitude", "longitude"], result.get("split_window", np.zeros_like(combined))),
                "gradient_component": (["latitude", "longitude"], result.get("spatial_gradient", np.zeros_like(combined))),
                "ctp_component": (["latitude", "longitude"], result.get("cloud_top_pressure", np.zeros_like(combined))),
            },
            coords={
                "latitude": TARGET_LATS,
                "longitude": TARGET_LONS,
            },
            attrs={
                "title": "StormFusion AI — Satellite-Derived Storm Development Indicator (SIMULATED INDICATOR)",
                "input_timestamp": str(ts_curr),
                "reference_timestamp": str(ts_prev),
                "forecast_lead_minutes": 30,
                "motion_u_deg_per_30min": motion_u,
                "motion_v_deg_per_30min": motion_v,
                "motion_speed_deg_per_30min": motion_speed,
                "motion_direction_deg": motion_dir,
                "motion_quality": motion_quality,
                "provenance": "SATELLITE",
                "source_satellite": "INSAT-3DS",
                "source_data": "MOSDAC L1B + L2B CTP",
                "is_ml_prediction": "false",
                "is_calibrated_probability": "false",
                "is_synthetic_data": "false",
                "is_synthetic_indicator": "true — heuristic, not validated",
                "data_date": "2025-05-29",
                "algorithm": "Deterministic physics-informed heuristic",
                "components": "cooling_rate, split_window, spatial_gradient, cloud_top_pressure",
                "WARNING": "THIS IS A SATELLITE-DERIVED STORM-DEVELOPMENT INDICATOR, NOT A VALIDATED FORECAST",
            }
        )
        
        out_path = output_dir / f"nowcast_{ts_str}.nc"
        ds.to_netcdf(out_path)
        
        # Summary
        indicator_mean = float(np.nanmean(combined[validity]))
        indicator_max = float(np.nanmax(combined[validity])) if np.any(validity) else 0.0
        hotspot_count = int(np.sum(combined > 0.5))
        
        logger.info(f"  Indicator: mean={indicator_mean:.3f}, max={indicator_max:.3f}, hotspots(>0.5)={hotspot_count}")
        logger.info(f"  Saved: {out_path}")
    
    total_time = time.time() - t0
    logger.info("\n" + "=" * 60)
    logger.info(f"Demo complete: {len(frames)-1} nowcast products generated in {total_time:.1f}s")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("IMPORTANT DISCLAIMERS:")
    logger.info("  • The storm development indicator is a HEURISTIC, not a calibrated probability")
    logger.info("  • This prototype has NOT been validated against real storm reports")
    logger.info("  • No ML model has been trained — this is deterministic physics only")
    logger.info("  • All outputs are derived from REAL INSAT-3DS satellite observations")
    logger.info("  • The indicator is NOT suitable for operational use")


if __name__ == "__main__":
    run_demo()
