import pytest
from datetime import datetime, timezone
import xarray as xr
import numpy as np

from backend.app.models.multimodal import MultimodalSample, ModalityStatus
from backend.app.models.data_types import DataSourceType, INDIA_BBOX
from backend.pipeline.common_grid import CommonGridResult, GridSpec
from backend.pipeline.multimodal_sync import MultimodalSynchronizer
from backend.app.models.metadata import DatasetMetadata

@pytest.fixture
def synchronizer():
    return MultimodalSynchronizer()

def create_mock_dataset(include_real=True, include_synthetic=True, include_lightning=True, include_nwp=True):
    coords = {
        "latitude": np.linspace(8.4, 37.6, 10),
        "longitude": np.linspace(68.7, 97.2, 10)
    }
    data_vars = {}
    
    if include_real:
        da_sat = xr.DataArray(
            np.ones((10, 10)),
            coords=coords,
            dims=["latitude", "longitude"],
            attrs={
                "is_synthetic": False,
                "source_type": DataSourceType.SATELLITE.value,
                "source": "MOSDAC",
                "time_offset_seconds": 0.0
            }
        )
        # Add some NaNs to simulate missing cells
        da_sat.values[0, 0] = np.nan
        data_vars["IMG_TIR1"] = da_sat
        
    if include_synthetic:
        da_radar = xr.DataArray(
            np.zeros((10, 10)),
            coords=coords,
            dims=["latitude", "longitude"],
            attrs={
                "is_synthetic": True,
                "source_type": DataSourceType.RADAR.value,
                "source": "Synthetic",
                "time_offset_seconds": 30.0
            }
        )
        data_vars["synthetic_radar_reflectivity"] = da_radar
        
    if include_lightning:
        da_lightning = xr.DataArray(
            np.zeros((10, 10)),
            coords=coords,
            dims=["latitude", "longitude"],
            attrs={
                "is_synthetic": True,
                "source_type": DataSourceType.LIGHTNING.value,
                "source": "Synthetic",
                "time_offset_seconds": -15.0
            }
        )
        data_vars["synthetic_lightning_density"] = da_lightning
        
    if include_nwp:
        da_nwp = xr.DataArray(
            np.ones((10, 10)),
            coords=coords,
            dims=["latitude", "longitude"],
            attrs={
                "is_synthetic": True,
                "source_type": DataSourceType.NWP.value,
                "source": "Synthetic",
                "time_offset_seconds": 3600.0
            }
        )
        data_vars["synthetic_nwp_cape"] = da_nwp

    return xr.Dataset(data_vars=data_vars)

def test_mixed_provenance_detection(synchronizer):
    ds = create_mock_dataset(include_real=True, include_synthetic=True)
    grid_result = CommonGridResult(
        grid_spec=GridSpec(bbox=INDIA_BBOX, resolution_deg=0.5),
        dataset=ds
    )
    
    target_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    sample = synchronizer.run(grid_result, target_time)
    
    assert sample.provenance == "MIXED"
    assert sample.satellite_status.is_synthetic is False
    assert sample.radar_status.is_synthetic is True
    assert sample.satellite_status.missing_cells_count == 1
    assert sample.satellite_status.total_cells_count == 100

def test_all_synthetic_provenance(synchronizer):
    ds = create_mock_dataset(include_real=False, include_synthetic=True)
    grid_result = CommonGridResult(
        grid_spec=GridSpec(bbox=INDIA_BBOX, resolution_deg=0.5),
        dataset=ds
    )
    
    target_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    sample = synchronizer.run(grid_result, target_time)
    
    assert sample.provenance == "SYNTHETIC"
    assert sample.satellite_status is None
    assert sample.radar_status is not None

def test_all_real_provenance(synchronizer):
    ds = create_mock_dataset(include_real=True, include_synthetic=False, include_lightning=False, include_nwp=False)
    grid_result = CommonGridResult(
        grid_spec=GridSpec(bbox=INDIA_BBOX, resolution_deg=0.5),
        dataset=ds
    )
    
    target_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    sample = synchronizer.run(grid_result, target_time)
    
    assert sample.provenance == "REAL"
    assert sample.radar_status is None

def test_missing_modality(synchronizer):
    ds = create_mock_dataset(include_real=True, include_synthetic=False, include_lightning=False, include_nwp=True)
    grid_result = CommonGridResult(
        grid_spec=GridSpec(bbox=INDIA_BBOX, resolution_deg=0.5),
        dataset=ds
    )
    
    target_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    sample = synchronizer.run(grid_result, target_time)
    
    assert sample.radar_status is None
    assert sample.lightning_status is None
    assert sample.satellite_status is not None
    assert sample.nwp_status is not None
