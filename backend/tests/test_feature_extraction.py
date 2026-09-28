import numpy as np
import pytest
import xarray as xr
from backend.app.models.data_types import BoundingBox
from backend.pipeline.common_grid import CommonGridResult, GridSpec
from backend.pipeline.feature_extraction import FeatureExtractor


@pytest.fixture
def mock_grid_result():
    # Create a small dataset with synthetic variables
    lat = np.linspace(20, 21, 10)
    lon = np.linspace(78, 79, 10)

    # Create dummy data with a gradient
    cape_data = np.linspace(1000, 2000, 100).reshape(10, 10)
    cin_data = np.full((10, 10), -50.0)
    bt_tir1_data = np.full((10, 10), 280.0)

    ds = xr.Dataset(
        {
            "cape": (("latitude", "longitude"), cape_data),
            "cin": (("latitude", "longitude"), cin_data),
            "bt_tir1": (("latitude", "longitude"), bt_tir1_data),
        },
        coords={"latitude": lat, "longitude": lon},
    )

    spec = GridSpec(bbox=BoundingBox(west=78, east=79, south=20, north=21))
    return CommonGridResult(grid_spec=spec, dataset=ds)


class TestFeatureExtractor:

    def test_extract_spatial_gradients(self, mock_grid_result):
        extractor = FeatureExtractor()
        result = extractor.run(mock_grid_result)

        # Should have added bt_tir1_spatial_grad and cape_spatial_grad
        assert "cape_spatial_grad" in result.extracted_features
        assert "bt_tir1_spatial_grad" in result.extracted_features

        assert "cape_spatial_grad" in result.dataset.data_vars
        assert "bt_tir1_spatial_grad" in result.dataset.data_vars

        # Since bt_tir1 is constant, gradient should be 0
        bt_grad = result.dataset["bt_tir1_spatial_grad"].values
        assert np.allclose(bt_grad, 0.0)

        # cape has a gradient, so it should be > 0
        cape_grad = result.dataset["cape_spatial_grad"].values
        assert np.mean(cape_grad) > 0.0

    def test_extract_instability_indices(self, mock_grid_result):
        extractor = FeatureExtractor()
        result = extractor.run(mock_grid_result)

        assert "severe_convection_potential" in result.extracted_features
        assert "severe_convection_potential" in result.dataset.data_vars

        scp = result.dataset["severe_convection_potential"].values
        # cape ranges 1000-2000, cin is -50, so scp = cape - 50
        assert np.min(scp) == 1000 - 50
        assert np.max(scp) == 2000 - 50
