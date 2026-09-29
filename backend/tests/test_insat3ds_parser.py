"""
Tests for INSAT-3DS HDF5 Parsing
"""
import numpy as np
import h5py
import pytest
from pathlib import Path
from datetime import datetime, timezone

from backend.app.ingestion.insat3ds import INSAT3DSParser, INSAT3DSParserError

@pytest.fixture
def dummy_l1b_file(tmp_path):
    p = tmp_path / "dummy_L1B.h5"
    with h5py.File(p, "w") as f:
        f.attrs["Acquisition_Start_Time"] = [b"29-MAY-2025T12:00:15.568"]
        
        # Geolocation
        lat_ir = f.create_dataset("Latitude", data=np.array([[10, 10], [11, 11]], dtype=np.int16))
        lat_ir.attrs["scale_factor"] = 0.1
        lat_ir.attrs["_FillValue"] = 32767
        
        lon_ir = f.create_dataset("Longitude", data=np.array([[70, 71], [70, 71]], dtype=np.int16))
        lon_ir.attrs["scale_factor"] = 0.1
        lon_ir.attrs["_FillValue"] = 32767
        
        lat_vis = f.create_dataset("Latitude_VIS", data=np.array([[10, 10], [11, 11]], dtype=np.int16))
        lat_vis.attrs["scale_factor"] = 0.1
        lat_vis.attrs["_FillValue"] = 32767
        
        lon_vis = f.create_dataset("Longitude_VIS", data=np.array([[70, 71], [70, 71]], dtype=np.int16))
        lon_vis.attrs["scale_factor"] = 0.1
        lon_vis.attrs["_FillValue"] = 32767
        
        # Channel Data
        mir = f.create_dataset("IMG_MIR", data=np.array([[[100, 200], [300, 1023]]], dtype=np.uint16))
        mir.attrs["scale_factor"] = 0.5
        mir.attrs["add_offset"] = 10.0
        mir.attrs["_FillValue"] = 1023
        
        vis = f.create_dataset("IMG_VIS", data=np.array([[[50, 100], [150, 0]]], dtype=np.uint16))
        vis.attrs["scale_factor"] = 1.0
        vis.attrs["add_offset"] = 0.0
        vis.attrs["_FillValue"] = 0
        
    return p

@pytest.fixture
def dummy_ctp_file(tmp_path):
    p = tmp_path / "dummy_CTP.h5"
    with h5py.File(p, "w") as f:
        f.attrs["Acquisition_Start_Time"] = [b"29-MAY-2025T12:00:15.568"]
        
        lat = f.create_dataset("Latitude", data=np.array([[10, 10], [11, 11]], dtype=np.int16))
        lat.attrs["scale_factor"] = 0.1
        lat.attrs["_FillValue"] = 32767
        
        lon = f.create_dataset("Longitude", data=np.array([[70, 71], [70, 71]], dtype=np.int16))
        lon.attrs["scale_factor"] = 0.1
        lon.attrs["_FillValue"] = 32767
        
        ctp = f.create_dataset("CTP", data=np.array([[[-999.0, 500.0], [400.0, -999.0]]], dtype=np.float32))
        ctp.attrs["_FillValue"] = -999.0
        ctp.attrs["units"] = b"hPa"
        
    return p

def test_parse_l1b_file(dummy_l1b_file):
    payload = INSAT3DSParser.parse_l1b_file(dummy_l1b_file)
    
    assert payload.metadata.source_type == "satellite"
    assert not payload.metadata.is_synthetic
    assert payload.metadata.time_start.year == 2025
    
    ds = payload.data
    assert "IMG_MIR" in ds
    assert "IMG_VIS" in ds
    
    # Check scaling and fill values on MIR:
    # 100 * 0.5 + 10 = 60
    # 200 * 0.5 + 10 = 110
    # 300 * 0.5 + 10 = 160
    # 1023 (fill) -> NaN
    mir_data = ds["IMG_MIR"].values
    assert np.isclose(mir_data[0, 0], 60.0)
    assert np.isnan(mir_data[1, 1])
    
    # Check coordinates
    assert "latitude_ir" in ds.coords
    assert "longitude_vis" in ds.coords
    assert np.isclose(ds.coords["latitude_ir"].values[0, 0], 1.0) # 10 * 0.1

def test_parse_ctp_file(dummy_ctp_file):
    payload = INSAT3DSParser.parse_ctp_file(dummy_ctp_file)
    
    assert payload.metadata.source_type == "satellite"
    assert not payload.metadata.is_synthetic
    
    ds = payload.data
    assert "CTP" in ds
    
    ctp_data = ds["CTP"].values
    assert np.isnan(ctp_data[0, 0])
    assert np.isclose(ctp_data[0, 1], 500.0)

def test_missing_file():
    with pytest.raises(INSAT3DSParserError):
        INSAT3DSParser.parse_l1b_file(Path("non_existent_file.h5"))
