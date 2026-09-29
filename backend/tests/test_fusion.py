import numpy as np
import pytest
import xarray as xr
from backend.pipeline.feature_extraction import FeatureExtractionResult
from backend.pipeline.fusion import DataFuser


@pytest.fixture
def mock_extraction_result():
    # Create a small dataset with synthetic variables and NaNs
    lat = np.linspace(20, 21, 10)
    lon = np.linspace(78, 79, 10)

    var1_data = np.ones((10, 10))
    var2_data = np.full((10, 10), 2.0)
    # Put a NaN in var2
    var2_data[0, 0] = np.nan

    ds = xr.Dataset(
        {
            "var1": (("latitude", "longitude"), var1_data),
            "var2": (("latitude", "longitude"), var2_data),
        },
        coords={"latitude": lat, "longitude": lon},
    )

    return FeatureExtractionResult(
        dataset=ds, original_variables=["var1"], extracted_features=["var2"]
    )


class TestDataFuser:

    def test_fuse_all_features(self, mock_extraction_result):
        fuser = DataFuser()
        result = fuser.run(mock_extraction_result)

        assert result.feature_tensor is not None
        # Should have shape (2, 10, 10) for 2 features and 10x10 grid
        assert result.feature_tensor.shape == (2, 10, 10)
        assert len(result.feature_names) == 2
        assert "var1" in result.feature_names
        assert "var2" in result.feature_names

    def test_fuse_selected_features(self, mock_extraction_result):
        fuser = DataFuser(selected_features=["var2"])
        result = fuser.run(mock_extraction_result)

        assert result.feature_tensor is not None
        assert result.feature_tensor.shape == (1, 10, 10)
        assert len(result.feature_names) == 1
        assert result.feature_names[0] == "var2"

    def test_nan_imputation(self, mock_extraction_result):
        fuser = DataFuser()
        result = fuser.run(mock_extraction_result)

        # var2[0, 0] was NaN, should be imputed to 0.0
        var2_idx = result.feature_names.index("var2")
        assert result.feature_tensor is not None
        assert result.feature_tensor[var2_idx, 0, 0] == 0.0
