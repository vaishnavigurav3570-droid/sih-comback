import os
import shutil
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from backend.app.models.data_types import BoundingBox
from backend.app.models.metadata import DataSourceStatus
from backend.app.providers.mosdac import MOSDACSatelliteProvider


@pytest.fixture
def mock_env():
    with patch(
        "os.environ",
        {"MOSDAC_USERNAME": "test_user", "MOSDAC_PASSWORD": "test_password"},
    ):
        yield


from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_mdapi_available():
    with patch("backend.app.providers.mosdac.MDAPI_AVAILABLE", True):
        yield

@pytest.fixture
def mock_mdapi_unavailable():
    with patch("backend.app.providers.mosdac.MDAPI_AVAILABLE", False):
        yield

def test_mosdac_unavailable_without_credentials(mock_mdapi_available):
    with patch("os.getenv", return_value=None):
        provider = MOSDACSatelliteProvider()
        assert not provider.is_available
        status = provider.validate_connection()
        assert status.status == DataSourceStatus.DEGRADED

def test_mosdac_unavailable_without_mdapi(mock_env, mock_mdapi_unavailable):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        assert not provider.is_available
        status = provider.validate_connection()
        assert status.status == DataSourceStatus.UNAVAILABLE

def test_mosdac_available_with_both(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        assert provider.is_available
        status = provider.validate_connection()
        assert status.status == DataSourceStatus.OK

def test_mosdac_search_datasets(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        bbox = BoundingBox(south=10, north=20, west=70, east=80)
        now = datetime.now(timezone.utc)
        datasets = provider.search_datasets(now, now, bbox)
        assert len(datasets) == 1
        assert datasets[0].dataset_id == "3SIMG_L1B_STD"
        assert not datasets[0].is_synthetic

def test_mosdac_download(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        bbox = BoundingBox(south=10, north=20, west=70, east=80)
        
        with patch("subprocess.run") as mock_run, \
             patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["test.nc"]), \
             patch("xarray.open_dataset") as mock_xr:
             
            mock_run.return_value = MagicMock(returncode=0, stdout="Login Successful")
            
            mock_ds = MagicMock()
            mock_ds.attrs = {}
            mock_ds.data_vars = {"bt_tir1": [1, 2, 3]}
            mock_xr.return_value = mock_ds
            
            payload = provider.download("3SIMG_L1B_STD", bounding_box=bbox)
            
            assert payload.metadata.dataset_id == "3SIMG_L1B_STD"
            assert payload.data.attrs["source"] == "MOSDAC"
            assert payload.data.attrs["is_synthetic"] == "REAL"

def test_mosdac_discover_datasets(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        bbox = BoundingBox(south=10, north=20, west=70, east=80)
        start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
        
        with patch("subprocess.run") as mock_run:
            # Mock the stdout returned by mosdac_discover_wrapper.py
            mock_run.return_value = MagicMock(
                returncode=0, 
                stdout='''Some logs
===DISCOVERY_RESULTS===
[{"identifier": "3SIMG_29MAY2025_1200", "record_id": "abc1", "prod_date": "2025-05-29T12:00:00Z"}, {"identifier": "3SIMG_29MAY2025_1230", "record_id": "abc2", "prod_date": "2025-05-29T12:30:00Z"}]
'''
            )
            
            results = provider.discover_datasets(["3SIMG_L1B_STD"], start_time, end_time, bbox)
            
            assert len(results) == 2
            assert results[0].dataset_id == "3SIMG_L1B_STD"
            assert results[0].file_name == "3SIMG_29MAY2025_1200"
            assert results[0].download_identifier == "abc1"
            assert results[0].timestamp == datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
            assert results[0].source == "MOSDAC"
            assert results[0].data_status == "REAL"
            assert results[0].availability_status == "DISCOVERED"

def test_mosdac_discover_datasets_auth_failure(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout='''Authentication Failure'''
            )
            
            import pytest
            with pytest.raises(PermissionError, match="MOSDAC Authentication Failed"):
                provider.discover_datasets(["3SIMG_L1B_STD"], start_time, end_time)

def test_mosdac_discover_datasets_network_failure(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout='''No Internet Connection Detected'''
            )
            
            import pytest
            with pytest.raises(ConnectionError, match="Network Error"):
                provider.discover_datasets(["3SIMG_L1B_STD"], start_time, end_time)

def test_mosdac_discover_datasets_empty_result(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, 
                stdout='''===DISCOVERY_RESULTS===
[]
'''
            )
            
            results = provider.discover_datasets(["3SIMG_L1B_STD"], start_time, end_time)
            
            assert len(results) == 0

def test_mosdac_download_files(mock_env, mock_mdapi_available, tmp_path):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
        end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
        output_dir = tmp_path / "data"
        target_files = ["3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5"]
        
        # Test download behavior
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Simulate mdapi downloading the file in temp directory
            original_exists = os.path.exists
            original_listdir = os.listdir
            original_getsize = os.path.getsize
            original_move = shutil.move
            
            def mock_exists(path):
                if "3SIMG_L1B_STD" in str(path) and "temp" not in str(path).lower(): 
                    # For final path check
                    if str(output_dir) in str(path):
                        return False
                return True
                
            def mock_listdir(path):
                return ["3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5"]
                
            def mock_getsize(path):
                return 1024
                
            def mock_move(src, dst):
                # Fake writing to the final destination so hashing works
                with open(dst, "wb") as f:
                    f.write(b"fake hdf5 content")
                    
            with patch("os.path.exists", side_effect=mock_exists):
                with patch("os.listdir", side_effect=mock_listdir):
                    with patch("os.path.getsize", side_effect=mock_getsize):
                        with patch("shutil.move", side_effect=mock_move):
                            # Mock h5py 
                            with patch("h5py.File"):
                                results = provider.download_files(
                                    "3SIMG_L1B_STD", target_files, start_time, end_time, output_dir
                                )
                                
                                assert len(results) == 1
                                assert results[0].status == "VERIFIED"
                                assert results[0].file_size_bytes == 1024
                                assert results[0].sha256_checksum is not None
                                assert results[0].file_name == "3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5"
