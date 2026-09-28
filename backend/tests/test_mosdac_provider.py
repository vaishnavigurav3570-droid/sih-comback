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


@pytest.fixture
def mock_mdapi_available():
    with patch("backend.app.providers.mosdac.MDAPI_AVAILABLE", True):
        yield


@pytest.fixture
def mock_mdapi_unavailable():
    with patch("backend.app.providers.mosdac.MDAPI_AVAILABLE", False):
        yield


def test_mosdac_unavailable_without_credentials(mock_mdapi_available):
    # Without mocking os.environ, username/password should be None
    with patch("os.getenv", return_value=None):
        provider = MOSDACSatelliteProvider()
        assert not provider.is_available

        status = provider.validate_connection()
        assert status.status == DataSourceStatus.DEGRADED
        assert "credentials not found" in status.message.lower()


def test_mosdac_unavailable_without_mdapi(mock_env, mock_mdapi_unavailable):
    with patch("os.getenv", return_value="test"):
        provider = MOSDACSatelliteProvider()
        assert not provider.is_available

        status = provider.validate_connection()
        assert status.status == DataSourceStatus.UNAVAILABLE
        assert "not installed" in status.message.lower()


def test_mosdac_available_with_both(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        with patch("backend.app.providers.mosdac.MdapiClient", create=True):
            provider = MOSDACSatelliteProvider()
            assert provider.is_available

            status = provider.validate_connection()
            assert status.status == DataSourceStatus.OK


def test_mosdac_search_datasets(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        with patch("backend.app.providers.mosdac.MdapiClient", create=True):
            provider = MOSDACSatelliteProvider()

            bbox = BoundingBox(south=10, north=20, west=70, east=80)
            now = datetime.now(timezone.utc)

            datasets = provider.search_datasets(now, now, bbox)
            assert len(datasets) == 1
            assert "INSAT-3DR-TIR1" in datasets[0].dataset_id
            assert not datasets[0].is_synthetic


def test_mosdac_download(mock_env, mock_mdapi_available):
    with patch("os.getenv", return_value="test"):
        with patch("backend.app.providers.mosdac.MdapiClient", create=True):
            provider = MOSDACSatelliteProvider()

            bbox = BoundingBox(south=10, north=20, west=70, east=80)
            payload = provider.download("test_id", bounding_box=bbox)

            assert payload.metadata.dataset_id == "test_id"
            assert payload.metadata.source_name == "MOSDAC"
            assert not payload.metadata.is_synthetic

            # The data is an xarray dataset
            assert "bt_tir1" in payload.data.data_vars
            assert payload.data.attrs["source"] == "MOSDAC"
