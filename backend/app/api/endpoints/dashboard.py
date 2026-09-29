"""
StormFusion AI — Dashboard Endpoints for UI
"""
import xarray as xr
import numpy as np
import glob
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter()

NOWCAST_DIR = Path("nowcast_output")
RADAR_FILE = Path("polar_MUM190720194254.nc")

def _nan_to_null(val):
    if np.isnan(val):
        return None
    return float(val)

def _get_2d_array(da, downsample=1):
    # Fill NaN with a sentinel or None, JSON doesn't support NaN well
    # We will just replace NaN with None in python lists
    arr = da[::downsample, ::downsample].values
    # Convert to python nested lists with None for NaN
    return [[None if np.isnan(x) else round(float(x), 2) for x in row] for row in arr]

@router.get("/nowcast/timeline")
async def get_nowcast_timeline() -> List[str]:
    files = sorted(glob.glob(str(NOWCAST_DIR / "nowcast_*.nc")))
    timestamps = []
    for f in files:
        name = Path(f).stem # e.g. nowcast_20250529T1230
        ts_str = name.split("_")[1] # 20250529T1230
        formatted = f"{ts_str[:4]}-{ts_str[4:6]}-{ts_str[6:8]}T{ts_str[9:11]}:{ts_str[11:13]}:00Z"
        timestamps.append(formatted)
    return timestamps

@router.get("/nowcast/latest")
async def get_nowcast_latest() -> Dict[str, Any]:
    timeline = await get_nowcast_timeline()
    if not timeline:
        raise HTTPException(status_code=404, detail="DATA UNAVAILABLE")
    return await get_nowcast_by_timestamp(timeline[-1])

@router.get("/nowcast/{timestamp}")
async def get_nowcast_by_timestamp(timestamp: str) -> Dict[str, Any]:
    # timestamp format: 2025-05-29T12:30:00Z -> 20250529T1230
    ts_str = timestamp.replace("-", "").replace(":", "").replace("Z", "").replace("T", "T")[:13]
    file_path = NOWCAST_DIR / f"nowcast_{ts_str}.nc"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="DATA UNAVAILABLE")
        
    try:
        ds = xr.open_dataset(file_path)
        lat = ds.latitude.values.tolist()
        lon = ds.longitude.values.tolist()
        
        response = {
            "timestamp": timestamp,
            "bounds": [
                [float(np.min(lat)), float(np.min(lon))], # SW
                [float(np.max(lat)), float(np.max(lon))]  # NE
            ],
            "variables": {},
            "metrics": {
                "coverage_percent": None,
                "missing_percent": None,
                "qc_flags": "NOMINAL"
            }
        }
        
        # Calculate coverage from ctp_component if available
        if "ctp_component" in ds:
            valid = np.sum(~np.isnan(ds["ctp_component"].values))
            total = ds["ctp_component"].size
            response["metrics"]["coverage_percent"] = round((valid / total) * 100, 2)
            response["metrics"]["missing_percent"] = round((1 - valid/total) * 100, 2)
            
        for var in ds.data_vars:
            # For UI performance, downsample large grids or just send them if they are 59x58
            # The common grid is 59x58 which is very small, so we send it raw
            response["variables"][var] = _get_2d_array(ds[var])
            
        ds.close()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/radar/metadata")
async def get_radar_metadata() -> Dict[str, Any]:
    if not RADAR_FILE.exists():
        raise HTTPException(status_code=404, detail="DATA UNAVAILABLE")
        
    # We can just return the metadata from our radar parser
    from backend.app.ingestion.radar import RadarParser
    try:
        parsed = RadarParser.parse_radar_file(RADAR_FILE)
        meta = parsed["metadata"]
        return {
            "radar_id": meta.radar_id,
            "latitude": meta.latitude,
            "longitude": meta.longitude,
            "start_time": meta.start_time.isoformat(),
            "end_time": meta.end_time.isoformat(),
            "sweep_count": meta.sweep_count,
            "target_threshold": 35.0,
            "status": "TEMPORALLY COMPATIBLE",
            "satellite_offset_seconds": 774,
            "nearest_satellite": "2019-07-20T19:30:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/radar/latest")
async def get_radar_latest() -> Dict[str, Any]:
    if not RADAR_FILE.exists():
        raise HTTPException(status_code=404, detail="DATA UNAVAILABLE")
        
    from backend.app.ingestion.radar import RadarParser
    try:
        parsed = RadarParser.parse_radar_file(RADAR_FILE)
        data = parsed["data"]
        coords = parsed["coordinates"]
        
        lat = coords["latitude"]
        lon = coords["longitude"]
        
        # We previously subsampled heavily (stride=10) to prevent the browser's GeoJSON layer from crashing.
        # Now that the frontend uses a highly optimized Canvas rasterizer, we can pass high-resolution data!
        stride = 2
        lat_sub = lat[::stride, ::stride]
        lon_sub = lon[::stride, ::stride]
        
        # Radar is originally polar. To make it easy for MapLibre, we can send Points
        # Or we send the 2D arrays and the frontend uses Deck.GL or Canvas.
        # Sending as nested arrays
        response = {
            "bounds": [
                [float(np.nanmin(lat)), float(np.nanmin(lon))],
                [float(np.nanmax(lat)), float(np.nanmax(lon))]
            ],
            "latitude": [[None if np.isnan(x) else round(float(x), 4) for x in row] for row in lat_sub],
            "longitude": [[None if np.isnan(x) else round(float(x), 4) for x in row] for row in lon_sub],
            "variables": {}
        }
        
        for var in ["REF", "VEL", "WIDTH", "TARGET"]:
            if var in data:
                arr = data[var][::stride, ::stride]
                response["variables"][var] = [[None if np.isnan(x) else round(float(x), 2) for x in row] for row in arr]
                
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
