import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.providers.synthetic import SyntheticDataProvider
from backend.app.models.data_types import DataSourceType
from backend.pipeline.ingestion import IngestionResult, IngestionBatch
from backend.pipeline.quality_control import QualityController
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder, GridSpec
from backend.pipeline.multimodal_sync import MultimodalSynchronizer
from backend.app.models.payload import DataPayload

def test_multimodal_pipeline():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    sat_provider = MOSDACSatelliteProvider()
    radar_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.RADAR)
    lightning_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.LIGHTNING)
    nwp_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.NWP)
    
    gridder = CommonGridder()
    synchronizer = MultimodalSynchronizer()
    
    timestamps = [
        "2025-05-29 12:00",
        "2025-05-29 12:30",
        "2025-05-29 13:00",
        "2025-05-29 13:30",
        "2025-05-29 14:00",
        "2025-05-29 14:30"
    ]
    
    for ts_str in timestamps:
        print(f"\n========================================")
        print(f"Testing Timestamp: {ts_str}")
        print(f"========================================")
        
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        # 1. Ingestion
        print("Loading modalities...")
        sat_payload1 = sat_provider.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
        sat_payload2 = sat_provider.download("3SIMG_L2B_CTP", start_time=ts, end_time=ts)
        print("  - Satellite loaded (REAL)")
        
        # Speed up test by dropping huge vars from SAT, keep only a few representative ones
        for var in list(sat_payload1.data.data_vars.keys()):
            if var not in ["IMG_TIR1"]:
                sat_payload1.data = sat_payload1.data.drop_vars(var)
        for var in list(sat_payload2.data.data_vars.keys()):
            if var not in ["CTP"]:
                sat_payload2.data = sat_payload2.data.drop_vars(var)
        
        radar_payload = radar_provider.download("synthetic_radar_reflectivity", reference_time=ts)
        print("  - Radar loaded (SYNTHETIC)")
        
        lightning_payload = lightning_provider.download("synthetic_lightning_flash_density", reference_time=ts)
        print("  - Lightning loaded (SYNTHETIC)")
        
        nwp_payload = nwp_provider.download("synthetic_nwp_cape", reference_time=ts)
        print("  - NWP loaded (SYNTHETIC)")
        
        # 2. QC & Alignment (Simplifying direct alignment for this test harness)
        geo_result = GeoAlignResult(aligned_payloads=[
            sat_payload1, sat_payload2, radar_payload, lightning_payload, nwp_payload
        ])
        
        # 3. Common Grid
        print("Gridding...")
        grid_result = gridder.run(geo_result, analysis_time=ts)
        
        # 4. Multimodal Sync
        print("Synchronizing Multimodal Sample...")
        sample = synchronizer.run(grid_result, target_time=ts)
        
        print("\n--- Multimodal Status ---")
        print(f"Target Timestamp: {sample.target_timestamp}")
        print(f"Final Grid Shape: {sample.dataset.sizes if sample.dataset else 'N/A'}")
        print(f"Number of Variables: {len(sample.dataset.data_vars) if sample.dataset else 0}")
        print(f"Provenance Status: {sample.provenance}")
        
        statuses = [
            ("Satellite", sample.satellite_status),
            ("Radar", sample.radar_status),
            ("Lightning", sample.lightning_status),
            ("NWP", sample.nwp_status),
        ]
        
        for name, status in statuses:
            if status:
                print(f"  {name}: {status.source_name} | Synthetic={status.is_synthetic} | Missing Cells={status.missing_cells_count}/{status.total_cells_count} ({(status.missing_cells_count/status.total_cells_count*100):.1f}%) | Time Offset={status.time_offset_seconds}s")
            else:
                print(f"  {name}: NOT AVAILABLE")

if __name__ == "__main__":
    test_multimodal_pipeline()
