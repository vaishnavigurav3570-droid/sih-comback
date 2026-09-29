import pytest
from datetime import datetime, timezone, timedelta
import torch
import numpy as np

from backend.app.models.dataset import SlidingWindowConfig, DatasetSplitConfig
from backend.pipeline.ml_dataset import StormFusionDataset, TargetBuilder, create_dataloader
from backend.pipeline.feature_extraction import FeatureExtractor
from backend.app.models.multimodal import MultimodalSample
import xarray as xr

# --- Mocks ---

def _mock_load_sample(ts: datetime) -> MultimodalSample:
    # Minimal mock dataset
    ds = xr.Dataset(
        data_vars={
            "synthetic_radar_reflectivity": (("latitude", "longitude"), np.array([[40.0, 20.0], [10.0, 5.0]])),
            "synthetic_lightning_flash_density": (("latitude", "longitude"), np.array([[5.0, 0.0], [0.0, 0.0]])),
            "IMG_TIR1": (("latitude", "longitude"), np.array([[250.0, 260.0], [270.0, 280.0]])),
            "IMG_TIR2": (("latitude", "longitude"), np.array([[250.0, 260.0], [270.0, 280.0]])),
        },
        coords={
            "latitude": [20.0, 21.0],
            "longitude": [78.0, 79.0]
        }
    )
    return MultimodalSample(
        target_timestamp=ts,
        dataset=ds,
        provenance="SYNTHETIC",
        is_synthetic=True,
        warnings=[],
        variables_present=["synthetic_radar_reflectivity", "synthetic_lightning_flash_density", "IMG_TIR1", "IMG_TIR2"]
    )

@pytest.fixture
def base_metadata():
    start = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    return [{"timestamp": start + timedelta(minutes=30*i), "provenance": "SYNTHETIC"} for i in range(10)]

@pytest.fixture
def feature_extractor():
    return FeatureExtractor()

# --- Tests ---

def test_sliding_window_construction(base_metadata, feature_extractor):
    config = SlidingWindowConfig(sequence_length=4, forecast_horizon=1, stride=1)
    ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor)
    
    # 10 records, seq=4, hor=1 -> req=5. (10 - 5 + 1) = 6 windows
    assert len(ds) == 6
    
    sample = ds[0]
    assert len(sample.input_timestamps) == 4
    assert len(sample.target_timestamps) == 1
    assert sample.features.shape[0] == 4  # Time dimension
    assert sample.target.shape[0] == 1    # Horizon

def test_irregular_timestamp_rejection(base_metadata, feature_extractor):
    config = SlidingWindowConfig(sequence_length=2, forecast_horizon=1, stride=1)
    
    # Introduce a gap by removing index 2 (13:00)
    gapped_meta = base_metadata.copy()
    gapped_meta.pop(2)
    
    ds = StormFusionDataset(gapped_meta, _mock_load_sample, config, feature_extractor)
    
    # Original length 10 -> req=3 -> 8 valid.
    # We removed idx 2 (was 13:00).
    # Original timestamps: 12:00, 12:30, 13:00, 13:30, 14:00, ...
    # Gapped: 12:00, 12:30, 13:30, 14:00, 14:30, ...
    # Window 0: 12:00, 12:30, 13:30 -> INVALID gap
    # Window 1: 12:30, 13:30, 14:00 -> INVALID gap
    # Window 2: 13:30, 14:00, 14:30 -> VALID
    
    # We expect 9 items now. Total 9 - 3 + 1 = 7 possible windows.
    # Window starting at 12:00 is invalid. Window starting at 12:30 is invalid.
    # Valid windows start at idx 2 (13:30). Remaining are valid.
    assert len(ds) == 5

def test_temporal_split_behavior(base_metadata, feature_extractor):
    config = SlidingWindowConfig(sequence_length=2, forecast_horizon=1, stride=1)
    
    split = DatasetSplitConfig(
        train_end_time=datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc), # 12:00, 12:30, 13:00
        val_end_time=datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)   # 13:30, 14:00, 14:30
    )
    
    train_ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor, partition="TRAIN", split_config=split)
    val_ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor, partition="VALIDATION", split_config=split)
    test_ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor, partition="TEST", split_config=split)
    
    # Train has 3 records. Req=3 -> 1 window
    assert len(train_ds) == 1
    # Val has 3 records. Req=3 -> 1 window
    assert len(val_ds) == 1
    # Test has 4 records. Req=3 -> 2 windows
    assert len(test_ds) == 2

def test_missing_target_masking(base_metadata, feature_extractor):
    config = SlidingWindowConfig(sequence_length=2, forecast_horizon=1, stride=1)
    ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor)
    
    sample = ds[0]
    # In mock, reflectivity is [40, 20], [10, 5].
    # Target 0 is storm (refl > 35).
    assert sample.target[0, 0, 0, 0] == 1.0 # 40 > 35
    assert sample.target[0, 0, 0, 1] == 0.0 # 20 < 35
    
    # Masks should be 1 for all because no NaNs in mock reflectivity
    assert torch.all(sample.target_mask[0, 0])

def test_dataloader_collation(base_metadata, feature_extractor):
    config = SlidingWindowConfig(sequence_length=2, forecast_horizon=1, stride=1)
    ds = StormFusionDataset(base_metadata, _mock_load_sample, config, feature_extractor)
    
    dl = create_dataloader(ds, batch_size=2)
    
    batch = next(iter(dl))
    assert batch.features.shape[0] == 2 # Batch size
    assert batch.features.shape[1] == 2 # Seq length
    assert batch.target.shape[0] == 2
    assert len(batch.provenance) == 2

def test_mixed_provenance(base_metadata, feature_extractor):
    mixed_meta = base_metadata.copy()
    mixed_meta[0] = {"timestamp": mixed_meta[0]["timestamp"], "provenance": "REAL"}
    # Sequence length 3 contains Real and Synthetic
    config = SlidingWindowConfig(sequence_length=2, forecast_horizon=1, stride=1)
    ds = StormFusionDataset(mixed_meta, _mock_load_sample, config, feature_extractor)
    
    # First window contains idx 0 (REAL) and idx 1, 2 (SYNTHETIC) -> MIXED
    assert ds[0].provenance == "MIXED"
    # Second window contains idx 1, 2, 3 (SYNTHETIC) -> SYNTHETIC
    assert ds[1].provenance == "SYNTHETIC"
