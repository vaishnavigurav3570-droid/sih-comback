import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.providers.synthetic import SyntheticDataProvider
from backend.app.models.data_types import DataSourceType
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder
from backend.pipeline.multimodal_sync import MultimodalSynchronizer
from backend.pipeline.feature_extraction import FeatureExtractor

def test_feature_pipeline():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    sat_provider = MOSDACSatelliteProvider()
    radar_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.RADAR)
    lightning_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.LIGHTNING)
    nwp_provider = SyntheticDataProvider(emulated_source_type=DataSourceType.NWP)
    
    gridder = CommonGridder()
    synchronizer = MultimodalSynchronizer()
    extractor = FeatureExtractor()
    
    timestamps = [
        "2025-05-29 12:00",
        "2025-05-29 12:30",
        "2025-05-29 13:00",
        "2025-05-29 13:30",
        "2025-05-29 14:00",
        "2025-05-29 14:30"
    ]
    
    samples = []
    
    start_time = time.time()
    
    for ts_str in timestamps:
        print(f"\nProcessing {ts_str}...")
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        # 1. Ingestion (Simulated download)
        sat_payload1 = sat_provider.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
        sat_payload2 = sat_provider.download("3SIMG_L2B_CTP", start_time=ts, end_time=ts)
        
        # Subselect channels for performance
        for var in list(sat_payload1.data.data_vars.keys()):
            if var not in ["IMG_TIR1", "IMG_TIR2", "IMG_WV"]:
                sat_payload1.data = sat_payload1.data.drop_vars(var)
        for var in list(sat_payload2.data.data_vars.keys()):
            if var not in ["CTP", "CTT"]:
                sat_payload2.data = sat_payload2.data.drop_vars(var)
        
        radar_payload = radar_provider.download("synthetic_radar_reflectivity", reference_time=ts)
        lightning_payload = lightning_provider.download("synthetic_lightning_flash_density", reference_time=ts)
        nwp_payload = nwp_provider.download("synthetic_nwp_cape", reference_time=ts)
        
        # 2. Alignment & Grid
        geo_result = GeoAlignResult(aligned_payloads=[
            sat_payload1, sat_payload2, radar_payload, lightning_payload, nwp_payload
        ])
        grid_result = gridder.run(geo_result, analysis_time=ts)
        
        # 3. Synchronize
        sample = synchronizer.run(grid_result, target_time=ts)
        samples.append(sample)
        print(f"  Synchronized sample. Provenance: {sample.provenance}")
    
    print("\n========================================")
    print("Running Feature Extraction...")
    print("========================================")
    
    batch = extractor.extract(samples)
    
    exec_time = time.time() - start_time
    
    print(f"\nExtraction completed in {exec_time:.2f} seconds.")
    print(f"Number of Samples: {len(batch.timestamps)}")
    print(f"Number of Features: {len(batch.feature_names)}")
    print(f"Tensor Shape [T, C, H, W]: {batch.tensor.shape}")
    print(f"Spatial Shape: {batch.tensor.shape[2]} x {batch.tensor.shape[3]}")
    print(f"Temporal Shape: {batch.tensor.shape[0]}")
    print(f"Feature Names: {batch.feature_names}")
    
    total_elements = batch.tensor.size
    valid_elements = np.sum(batch.validity_mask)
    missing_elements = total_elements - valid_elements
    print(f"Finite %: {(valid_elements / total_elements)*100:.2f}%")
    print(f"Missing %: {(missing_elements / total_elements)*100:.2f}%")
    print(f"Final Provenance: {batch.provenance}")
    
    print("\nFeatures depending on synthetic data:")
    for name, meta in batch.feature_registry.items():
        if meta.depends_on_synthetic:
            print(f"  - {name}")

if __name__ == "__main__":
    test_feature_pipeline()
