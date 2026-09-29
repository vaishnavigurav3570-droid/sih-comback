import pytest
import numpy as np
import xarray as xr
from datetime import datetime, timezone

from backend.app.models.features import MLFeatureBatch
from backend.app.models.multimodal import MultimodalSample, ModalityStatus
from backend.pipeline.feature_extraction import FeatureExtractor

@pytest.fixture
def feature_extractor():
    return FeatureExtractor()

def _create_mock_sample(time: datetime, tir1_val: float, tir2_val: float, ctp_val: float) -> MultimodalSample:
    sample = MultimodalSample(target_timestamp=time, provenance="MIXED")
    
    # 2x2 grid
    coords = {
        "latitude": [10.0, 11.0],
        "longitude": [80.0, 81.0]
    }
    
    data_vars = {
        "IMG_TIR1": xr.DataArray(np.full((2, 2), tir1_val), coords=coords, dims=["latitude", "longitude"]),
        "IMG_TIR2": xr.DataArray(np.full((2, 2), tir2_val), coords=coords, dims=["latitude", "longitude"]),
        "CTP": xr.DataArray(np.full((2, 2), ctp_val), coords=coords, dims=["latitude", "longitude"]),
        "synthetic_radar_reflectivity": xr.DataArray(np.zeros((2, 2)), coords=coords, dims=["latitude", "longitude"])
    }
    
    # Add a NaN value to test missingness propagation
    data_vars["IMG_TIR1"].values[0, 0] = np.nan
    
    sample.dataset = xr.Dataset(data_vars=data_vars)
    return sample

def test_feature_registry_completeness(feature_extractor):
    assert len(feature_extractor.registry) > 0
    assert "IMG_TIR1" in feature_extractor.registry
    assert "synthetic_radar_reflectivity" in feature_extractor.registry

def test_deterministic_feature_ordering(feature_extractor):
    assert feature_extractor.feature_names == list(feature_extractor.registry.keys())

def test_raw_and_derived_features(feature_extractor):
    t1 = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2025, 5, 29, 12, 30, tzinfo=timezone.utc)
    
    s1 = _create_mock_sample(t1, tir1_val=250.0, tir2_val=260.0, ctp_val=300.0)
    s2 = _create_mock_sample(t2, tir1_val=240.0, tir2_val=255.0, ctp_val=200.0)
    
    batch = feature_extractor.extract([s1, s2])
    
    # Tensor shape: (2 timestamps, C channels, 2 lat, 2 lon)
    assert batch.tensor.shape == (2, len(feature_extractor.feature_names), 2, 2)
    
    tir1_idx = feature_extractor.feature_names.index("IMG_TIR1")
    tir2_idx = feature_extractor.feature_names.index("IMG_TIR2")
    diff_idx = feature_extractor.feature_names.index("TIR1_TIR2_DIFF")
    tdiff_idx = feature_extractor.feature_names.index("TIR1_TEMPORAL_DIFF")
    
    # Check RAW feature assignment
    assert batch.tensor[0, tir1_idx, 1, 1] == 250.0
    
    # Check Missingness Propagation (0, 0 was NaN)
    assert np.isnan(batch.tensor[0, tir1_idx, 0, 0])
    assert not batch.validity_mask[0, tir1_idx, 0, 0]
    
    # Check DERIVED (Spatial Diff)
    # 250.0 - 260.0 = -10.0
    assert batch.tensor[0, diff_idx, 1, 1] == -10.0
    
    # Check TEMPORAL
    # First frame has no prev, so NaN
    assert np.isnan(batch.tensor[0, tdiff_idx, 1, 1])
    # Second frame: 240.0 - 250.0 = -10.0
    assert batch.tensor[1, tdiff_idx, 1, 1] == -10.0

def test_missing_modality_behavior(feature_extractor):
    t1 = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    s1 = _create_mock_sample(t1, tir1_val=250.0, tir2_val=260.0, ctp_val=300.0)
    
    # Remove radar from the dataset completely
    s1.dataset = s1.dataset.drop_vars("synthetic_radar_reflectivity")
    
    batch = feature_extractor.extract([s1])
    
    radar_idx = feature_extractor.feature_names.index("synthetic_radar_reflectivity")
    # All radar values should be NaN
    assert np.all(np.isnan(batch.tensor[0, radar_idx]))
    assert np.all(~batch.validity_mask[0, radar_idx])

def test_provenance_propagation(feature_extractor):
    t1 = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    s1 = _create_mock_sample(t1, tir1_val=250.0, tir2_val=260.0, ctp_val=300.0)
    # The mock creates a sample with "MIXED"
    batch = feature_extractor.extract([s1])
    assert batch.provenance == "MIXED"
