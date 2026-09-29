import pytest
import numpy as np
from datetime import datetime
from backend.pipeline.satellite_nowcast import SatelliteNowcastPrototype
from backend.app.models.features import MLFeatureBatch

class TestSatelliteNowcastPrototype:
    def test_prototype_is_deterministic(self):
        # uncalibrated probability guard / deterministic check
        nowcast = SatelliteNowcastPrototype()
        assert nowcast.cooling_weight == 0.4
        
    def test_prototype_no_training_methods(self):
        nowcast = SatelliteNowcastPrototype()
        # No forward(), fit(), or predict()
        assert not hasattr(nowcast, "fit")
        assert not hasattr(nowcast, "train")

    def test_six_frame_chronological_processing(self):
        nowcast = SatelliteNowcastPrototype()
        
        # Simulate 6 frames, 4 channels, 10x10 spatial
        N, C, H, W = 6, 4, 10, 10
        tensor = np.zeros((N, C, H, W), dtype=np.float32)
        
        timestamps = [f"2025-05-29T12:{i}0:00+00:00" for i in range(6)]
        
        batch = MLFeatureBatch(
            timestamps=timestamps,
            feature_names=["IMG_TIR1", "TIR1_TEMPORAL_DIFF", "TIR1_SPATIAL_GRAD", "TIR1_TIR2_DIFF"],
            feature_registry={},
            tensor=tensor,
            validity_mask=np.ones((N, 1, H, W), dtype=bool),
            provenance="REAL"
        )
        
        results = nowcast.process(batch)
        assert len(results) == 6
        
        # check missing data propagation
        # make first pixel NaN in frame 0
        batch.tensor[0, 0, 0, 0] = np.nan
        results2 = nowcast.process(batch)
        assert np.isnan(results2[0]["storm_development_indicator"][0, 0])
        assert not results2[0]["indicator_validity_mask"][0, 0]
        
    def test_cloud_top_cooling_calculation(self):
        nowcast = SatelliteNowcastPrototype()
        # Mock negative cooling
        cooling = np.array([-5.0, 0.0, 5.0, np.nan])
        norm = nowcast._normalize_cooling(cooling)
        # -5 should be 0.5, 0 should be 0, 5 should be 0 (clipped to 0)
        assert np.isclose(norm[0], 0.5)
        assert np.isclose(norm[1], 0.0)
        assert np.isclose(norm[2], 0.0)
        assert np.isnan(norm[3])

    def test_motion_estimation_output_shape(self):
        nowcast = SatelliteNowcastPrototype()
        tensor = np.zeros((2, 1, 10, 10))
        tensor[0, 0, 4:6, 4:6] = 1.0 # previous 
        tensor[1, 0, 5:7, 5:7] = 1.0 # current (shifted +1, +1) -> meaning u=1, v=1
        
        u, v, speed, d, q = nowcast._estimate_motion(tensor, 1, 0)
        assert isinstance(u, float)
        assert isinstance(v, float)
        assert u == 1.0
        assert v == 1.0
        
    def test_extrapolation_validity_mask(self):
        nowcast = SatelliteNowcastPrototype()
        
        ind = np.ones((10, 10))
        mask = np.ones((10, 10), dtype=bool)
        
        u = 2.0
        v = 2.0
        
        e_ind, e_mask = nowcast._extrapolate(ind, mask, u, v)
        assert e_ind.shape == (10, 10)
        assert e_mask.shape == (10, 10)
        
        # The shifted edge should be NaN and False
        assert np.isnan(e_ind[0, 0])
        assert e_mask[0, 0] == False
