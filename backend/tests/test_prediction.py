import numpy as np
import pytest
from backend.app.models.data_types import BoundingBox
from backend.pipeline.common_grid import GridSpec
from backend.pipeline.fusion import FusionResult
from backend.pipeline.orchestrator import PipelineResult
from backend.pipeline.prediction import Predictor


@pytest.fixture
def mock_pipeline_result():
    # Shape: 3 features, 10 lats, 10 lons
    # Multiply by 5000 so that CAPE values are realistic and trigger forecasts
    tensor = (np.random.rand(3, 10, 10) * 5000.0).astype(np.float32)
    fusion_res = FusionResult(
        feature_tensor=tensor, feature_names=["cape", "bt_tir1", "cin"]
    )

    spec = GridSpec(bbox=BoundingBox(west=78, east=79, south=20, north=21))

    # Needs just enough mock data to run the predictor
    res = PipelineResult(fusion_result=fusion_res, grid_spec=spec, is_synthetic=True)
    return res


class TestPredictor:

    def test_predictor_heuristic(self, mock_pipeline_result):
        # Force heuristic mode so we don't depend on PyTorch for basic tests
        predictor = Predictor(use_dummy_heuristic=True)
        result = predictor.run(mock_pipeline_result)

        assert result.forecast_product is not None
        assert result.forecast_product.is_demo_mode is True

        # It should generate grid forecasts
        assert len(result.forecast_product.grid_forecasts) > 0

        # Check a sample forecast
        fcst = result.forecast_product.grid_forecasts[0]
        assert fcst.thunderstorm_probability >= 0.0
        assert fcst.lightning_probability >= 0.0
        assert fcst.lead_time.minutes >= 15
