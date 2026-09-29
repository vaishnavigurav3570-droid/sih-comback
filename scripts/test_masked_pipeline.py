import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.pipeline.ingestion import IngestionResult, IngestionBatch
from backend.pipeline.quality_control import QualityController
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder, GridSpec

def test_masked_pipeline():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    provider = MOSDACSatelliteProvider()
    gridder = CommonGridder()
    
    ts_str = "2025-05-29 12:00"
    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    
    payload1 = provider.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
    payload2 = provider.download("3SIMG_L2B_CTP", start_time=ts, end_time=ts)
    
    # Drop most variables to speed up test
    for var in list(payload1.data.data_vars.keys()):
        if var not in ["IMG_TIR1", "IMG_WV"]:
            payload1.data = payload1.data.drop_vars(var)
            
    for var in list(payload2.data.data_vars.keys()):
        if var not in ["CTP", "CTT"]:
            payload2.data = payload2.data.drop_vars(var)
            
    geo_result = GeoAlignResult(aligned_payloads=[payload1, payload2])
    grid_result = gridder.run(geo_result)
    
    print(f"\nTarget Grid Shape: {grid_result.grid_spec.shape}")
    print(f"Lat: {grid_result.grid_spec.bbox.south} to {grid_result.grid_spec.bbox.north}")
    print(f"Lon: {grid_result.grid_spec.bbox.west} to {grid_result.grid_spec.bbox.east}\n")
    
    for v in ["IMG_TIR1", "IMG_WV", "CTP", "CTT"]:
        
        # Native stats
        p = payload1 if v in payload1.data else payload2
        native_da = p.data[v]
        n_vals = native_da.values.ravel()
        n_tot = len(n_vals)
        n_val = int(np.sum(np.isfinite(n_vals)))
        print(f"Native {v}: valid={n_val/n_tot*100:.1f}%, NaN={(n_tot-n_val)/n_tot*100:.1f}%")
        
        # Target stats
        t_da = grid_result.dataset[v]
        t_vals = t_da.values.ravel()
        t_tot = len(t_vals)
        t_val = int(np.sum(np.isfinite(t_vals)))
        
        valid_arr = t_vals[np.isfinite(t_vals)]
        if len(valid_arr) > 0:
            vmin = np.min(valid_arr)
            vmax = np.max(valid_arr)
            vmed = np.median(valid_arr)
            print(f"Target {v}: valid={t_val/t_tot*100:.1f}%, NaN={(t_tot-t_val)/t_tot*100:.1f}% | Min: {vmin:.1f}, Med: {vmed:.1f}, Max: {vmax:.1f}")
        else:
            print(f"Target {v}: valid=0%, NaN=100%")
            
        print(f"Invalidated cells: {t_tot - t_val}\n")

if __name__ == "__main__":
    test_masked_pipeline()
