import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import torch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.providers.synthetic import SyntheticDataProvider
from backend.app.models.data_types import DataSourceType
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder
from backend.pipeline.multimodal_sync import MultimodalSynchronizer
from backend.pipeline.feature_extraction import FeatureExtractor
from backend.pipeline.spatiotemporal import ModelFactory, SpatiotemporalConfig

def run_forward_pass_demo():
    os.environ["MOSDAC_LOCAL_DATA_ROOT"] = r"C:\Users\Vedant\Documents\mosdac"
    
    # 1. Pipeline Init
    sat = MOSDACSatelliteProvider()
    radar = SyntheticDataProvider(emulated_source_type=DataSourceType.RADAR)
    lightning = SyntheticDataProvider(emulated_source_type=DataSourceType.LIGHTNING)
    nwp = SyntheticDataProvider(emulated_source_type=DataSourceType.NWP)
    
    gridder = CommonGridder()
    sync = MultimodalSynchronizer()
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
    
    print("Ingesting and Gridding Data...")
    for ts_str in timestamps:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        
        sp1 = sat.download("3SIMG_L1B_STD", start_time=ts, end_time=ts)
        sp2 = sat.download("3SIMG_L2B_CTP", start_time=ts, end_time=ts)
        
        # Keep it memory light for the demo
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
        samples.append(sync.run(gridded, target_time=ts))

    print("Extracting ML Features...")
    batch = extractor.extract(samples)
    
    # [T, C, H, W] -> [1, T, C, H, W] (Batch size 1)
    tensor = np.expand_dims(batch.tensor, axis=0)
    mask = np.expand_dims(batch.validity_mask, axis=0)
    
    t_features = torch.from_numpy(tensor).float()
    t_mask = torch.from_numpy(mask).bool()
    
    print("\n==================================================")
    print("FORWARD PASS DEMONSTRATION")
    print("==================================================")
    
    config = SpatiotemporalConfig(
        input_channels=t_features.shape[2],
        sequence_length=t_features.shape[1],
        spatial_height=t_features.shape[3],
        spatial_width=t_features.shape[4],
        hidden_channels=32,
        forecast_horizon=1,
        output_heads=2,
        mask_handling_strategy="concatenate"
    )
    
    model = ModelFactory.create_model("convlstm", config)
    model.eval()
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"Model Type: ConvLSTM (Spatiotemporal)")
    print(f"Input Shape: {t_features.shape}")
    print(f"Mask Shape: {t_mask.shape}")
    print(f"Total Parameters: {total_params:,}")
    print(f"Trainable Parameters: {trainable_params:,}")
    
    inference_start = time.time()
    with torch.no_grad():
        out = model(t_features, t_mask)
        
    inference_time = time.time() - inference_start
    
    print(f"\nInference Time: {inference_time:.4f} seconds")
    print(f"Output Shape (Logits): {out['logits'].shape}")
    print(f"Thunderstorm Head Shape: {out['thunderstorm_logits'].shape}")
    print(f"Lightning Head Shape: {out['lightning_logits'].shape}")
    
    print(f"\nProvenance: {batch.provenance}")
    print("WARNING: These are uncalibrated logits. NO TRAINING HAS BEEN PERFORMED.")

if __name__ == "__main__":
    run_forward_pass_demo()
