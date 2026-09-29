import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import logging

# Ensure project root is in PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import get_settings
from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.pipeline.ingestion import IngestionBatch, IngestionResult
from backend.pipeline.quality_control import QualityController
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder, GridSpec
from backend.app.models.data_types import DataSourceType, BoundingBox

logging.basicConfig(level=logging.WARNING, format="%(message)s")

def test_pipeline(mosdac_dir, timestamps):
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = mosdac_dir
    provider = MOSDACSatelliteProvider()
    qc = QualityController()
    
    # Target grid bounds based on existing project limits (India bounds)
    grid_spec = GridSpec(bbox=BoundingBox(south=8.4, north=37.6, west=68.7, east=97.2), resolution_deg=0.5)
    gridder = CommonGridder(grid_spec)

    for ts_str in timestamps:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        print(f"\n========================================")
        print(f"Testing Timestamp: {ts_str}")
        print(f"========================================")
        
        # 1. Provide
        try:
            payload = provider.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
        except Exception as e:
            print(f"Provider failed: {e}")
            continue
            
        ds = payload.data
        
        print("Input Datasets:")
        for v in ds.data_vars:
            print(f"  {v}: {ds[v].shape}")
            
        print(f"Provenance: Source={payload.metadata.source_name}, is_synthetic={payload.metadata.is_synthetic}")
        
        # 2. QC
        batch = IngestionBatch(
            analysis_time=ts,
            region=BoundingBox(south=8.4, north=37.6, west=68.7, east=97.2),
            results={DataSourceType.SATELLITE: IngestionResult(
                source_type=DataSourceType.SATELLITE,
                source_name="MOSDAC",
                success=True,
                payloads=[payload]
            )}
        )
        qc_result = qc.run(batch)
        print(f"\nQC Result: {qc_result.overall_quality}")
        for stat in qc_result.stats:
            print(f"  {stat.summary}")
            
        # 3. Grid
        geo_result = GeoAlignResult(aligned_payloads=qc_result.qc_payloads)
        grid_result = gridder.run(geo_result, analysis_time=ts)
        
        print(f"\nTarget Grid: {grid_result.grid_spec.shape} "
              f"({grid_result.grid_spec.bbox.south} to {grid_result.grid_spec.bbox.north} Lat, "
              f"{grid_result.grid_spec.bbox.west} to {grid_result.grid_spec.bbox.east} Lon)")
              
        import numpy as np
        if grid_result.dataset:
            for v in grid_result.dataset.data_vars:
                da = grid_result.dataset[v]
                valid = int((~da.isnull()).sum())
                total = da.size
                nan_pct = (total - valid) / total * 100
                method = da.attrs.get("regrid_method", "unknown")
                if valid > 0:
                    vals = da.values[~np.isnan(da.values)]
                    vmin = np.min(vals)
                    vmax = np.max(vals)
                    vmed = np.median(vals)
                    print(f"  Output {v}: {valid}/{total} valid ({nan_pct:.1f}% NaN), Method: {method}, Min: {vmin:.1f}, Median: {vmed:.1f}, Max: {vmax:.1f}")
                else:
                    print(f"  Output {v}: {valid}/{total} valid ({nan_pct:.1f}% NaN), Method: {method}")
        else:
            print("  Grid output dataset is missing!")
            
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        mosdac_dir = sys.argv[1]
    else:
        mosdac_dir = r"C:\Users\Vedant\Documents\mosdac"
        
    print("Running 12:00 end-to-end first...")
    test_pipeline(mosdac_dir, ["2025-05-29 12:00"])
    
    print("\nRunning remaining 5 timestamps...")
    test_pipeline(mosdac_dir, [
        "2025-05-29 12:30",
        "2025-05-29 13:00",
        "2025-05-29 13:30",
        "2025-05-29 14:00",
        "2025-05-29 14:30"
    ])
