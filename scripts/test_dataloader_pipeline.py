import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipeline.ml_dataset import StormFusionDataset, create_dataloader
from backend.app.models.dataset import SlidingWindowConfig
from backend.pipeline.feature_extraction import FeatureExtractor
from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.providers.synthetic import SyntheticDataProvider
from backend.app.models.data_types import DataSourceType
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder
from backend.pipeline.multimodal_sync import MultimodalSynchronizer
from backend.app.models.multimodal import MultimodalSample

def load_sample_for_demo(ts: datetime) -> MultimodalSample:
    """
    Lazy loader for demonstration purposes using real pipeline logic.
    For this demo, we do the processing on demand.
    """
    sat = MOSDACSatelliteProvider()
    radar = SyntheticDataProvider(emulated_source_type=DataSourceType.RADAR)
    lightning = SyntheticDataProvider(emulated_source_type=DataSourceType.LIGHTNING)
    nwp = SyntheticDataProvider(emulated_source_type=DataSourceType.NWP)
    
    gridder = CommonGridder()
    sync = MultimodalSynchronizer()
    
    print(f"    [Lazy Loader] Fetching and gridding record for {ts.strftime('%H:%M')}")
    
    sp1 = sat.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
    sp2 = sat.download("3SIMG_L2B_CTP", start_time=ts, end_time=ts)
    
    # Drop vars to keep memory low
    for var in list(sp1.data.data_vars.keys()):
        if var not in ["IMG_TIR1", "IMG_TIR2", "IMG_WV"]:
            sp1.data = sp1.data.drop_vars(var)
    for var in list(sp2.data.data_vars.keys()):
        if var not in ["CTP", "CTT"]:
            sp2.data = sp2.data.drop_vars(var)
            
    rp = radar.download("synthetic_radar_reflectivity", reference_time=ts)
    lp = lightning.download("synthetic_lightning_flash_density", reference_time=ts)
    np_p = nwp.download("synthetic_nwp_cape", reference_time=ts)
    
    aligned = GeoAlignResult([sp1, sp2, rp, lp, np_p])
    gridded = gridder.run(aligned, analysis_time=ts)
    
    return sync.run(gridded, target_time=ts)

def run_dataloader_demo():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    
    print("\n==================================================")
    print("DATALOADER STRUCTURAL DEMONSTRATION")
    print("==================================================")
    print("WARNING: DO NOT train on this. 6 timestamps are insufficient for ML.")
    
    timestamps_str = [
        "2025-05-29 12:00",
        "2025-05-29 12:30",
        "2025-05-29 13:00",
        "2025-05-29 13:30",
        "2025-05-29 14:00",
        "2025-05-29 14:30"
    ]
    
    metadata = []
    for ts in timestamps_str:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        metadata.append({"timestamp": dt, "provenance": "MIXED"})
        
    config = SlidingWindowConfig(
        sequence_length=4,
        forecast_horizon=1,
        stride=1
    )
    
    extractor = FeatureExtractor()
    
    print("\nConfiguring Dataset...")
    dataset = StormFusionDataset(
        metadata_records=metadata,
        load_sample_fn=load_sample_for_demo,
        config=config,
        feature_extractor=extractor
    )
    
    print(f"Total valid sliding windows found: {len(dataset)}")
    
    dataloader = create_dataloader(dataset, batch_size=2)
    
    for b_idx, batch in enumerate(dataloader):
        print(f"\nBatch {b_idx}:")
        print(f"  Features shape:      {batch.features.shape}  [Batch, Time, Channels, Height, Width]")
        print(f"  Validity mask shape: {batch.validity_mask.shape}")
        print(f"  Target shape:        {batch.target.shape}    [Batch, Horizon, Heads, Height, Width]")
        print(f"  Target mask shape:   {batch.target_mask.shape}")
        print(f"  Provenance:          {batch.provenance}")
        print(f"  Memory allocated:    {batch.features.element_size() * batch.features.nelement() / 1024 / 1024:.2f} MB")
        
if __name__ == "__main__":
    run_dataloader_demo()
