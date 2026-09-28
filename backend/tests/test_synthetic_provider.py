"""
Tests for StormFusion AI — SyntheticDataProvider

Verifies that the synthetic data provider:
1. Implements the DataProvider interface correctly
2. Generates data with the correct shapes and ranges
3. ALWAYS marks data as SYNTHETIC (critical for scientific honesty)
4. Produces deterministic output (same input → same output)
5. Works for all source types (satellite, radar, lightning, NWP)
"""

from datetime import datetime, timezone

import numpy as np
import pytest
import xarray as xr
from backend.app.models.data_types import (
    INDIA_BBOX,
    DataSourceStatus,
    DataSourceType,
)
from backend.app.models.payload import DataPayload, LightningDataPayload
from backend.app.providers.base import DataProvider
from backend.app.providers.synthetic import SyntheticDataProvider

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def satellite_provider() -> SyntheticDataProvider:
    """Create a SyntheticDataProvider emulating satellite data."""
    return SyntheticDataProvider(emulated_source_type=DataSourceType.SATELLITE)


@pytest.fixture
def radar_provider() -> SyntheticDataProvider:
    """Create a SyntheticDataProvider emulating radar data."""
    return SyntheticDataProvider(emulated_source_type=DataSourceType.RADAR)


@pytest.fixture
def lightning_provider() -> SyntheticDataProvider:
    """Create a SyntheticDataProvider emulating lightning data."""
    return SyntheticDataProvider(emulated_source_type=DataSourceType.LIGHTNING)


@pytest.fixture
def nwp_provider() -> SyntheticDataProvider:
    """Create a SyntheticDataProvider emulating NWP data."""
    return SyntheticDataProvider(emulated_source_type=DataSourceType.NWP)


@pytest.fixture
def reference_time() -> datetime:
    """A fixed reference time for deterministic testing."""
    return datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)


# ============================================================
# Interface Compliance Tests
# ============================================================


class TestInterfaceCompliance:
    """Verify that SyntheticDataProvider is a proper DataProvider."""

    def test_is_data_provider(self, satellite_provider):
        """SyntheticDataProvider IS a DataProvider (inheritance check)."""
        assert isinstance(satellite_provider, DataProvider)

    def test_has_source_type(self, satellite_provider):
        """Has a source_type property."""
        assert satellite_provider.source_type == DataSourceType.SATELLITE

    def test_has_source_name(self, satellite_provider):
        """Has a source_name property."""
        assert satellite_provider.source_name == "Synthetic"

    def test_is_always_available(self, satellite_provider):
        """Synthetic provider is ALWAYS available."""
        assert satellite_provider.is_available is True

    def test_repr(self, satellite_provider):
        """Has a useful string representation."""
        rep = repr(satellite_provider)
        assert "SyntheticDataProvider" in rep
        assert "satellite" in rep


# ============================================================
# Satellite Data Tests
# ============================================================


class TestSatelliteData:
    """Test synthetic satellite data generation."""

    def test_search_returns_datasets(self, satellite_provider, reference_time):
        """search_datasets returns a non-empty list."""
        results = satellite_provider.search_datasets(
            start_time=reference_time,
            end_time=reference_time,
            bounding_box=INDIA_BBOX,
        )
        assert len(results) > 0

    def test_search_results_are_synthetic(self, satellite_provider, reference_time):
        """All search results are marked as synthetic."""
        results = satellite_provider.search_datasets(
            start_time=reference_time,
            end_time=reference_time,
            bounding_box=INDIA_BBOX,
        )
        for meta in results:
            assert meta.is_synthetic is True
            assert meta.source_name == "Synthetic"

    def test_download_bt_tir1(self, satellite_provider, reference_time):
        """Can download brightness temperature TIR1 data."""
        payload = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )

        assert isinstance(payload, DataPayload)
        assert payload.metadata.is_synthetic is True
        assert isinstance(payload.data, xr.DataArray)

    def test_bt_values_in_range(self, satellite_provider, reference_time):
        """Brightness temperature values are physically reasonable (180–320 K)."""
        payload = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )
        data = payload.data
        assert float(data.min()) >= 180.0, f"Min BT too low: {float(data.min())}"
        assert float(data.max()) <= 320.0, f"Max BT too high: {float(data.max())}"

    def test_data_has_correct_coordinates(self, satellite_provider, reference_time):
        """Data has latitude and longitude coordinates."""
        payload = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )
        data = payload.data
        assert "latitude" in data.dims
        assert "longitude" in data.dims
        assert len(data.coords["latitude"]) == 64
        assert len(data.coords["longitude"]) == 60

    def test_data_has_source_attribute(self, satellite_provider, reference_time):
        """Data carries a 'source' attribute set to 'SYNTHETIC'."""
        payload = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )
        assert payload.data.attrs["source"] == "SYNTHETIC"

    def test_data_is_deterministic(self, satellite_provider, reference_time):
        """Same input produces identical output (no randomness)."""
        payload_1 = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )
        payload_2 = satellite_provider.download(
            "synthetic_satellite_bt_tir1",
            reference_time=reference_time,
        )
        np.testing.assert_array_equal(payload_1.data.values, payload_2.data.values)

    def test_download_all_satellite_variables(self, satellite_provider, reference_time):
        """Can download all satellite variable types."""
        datasets = satellite_provider.search_datasets(
            start_time=reference_time,
            end_time=reference_time,
            bounding_box=INDIA_BBOX,
        )
        for meta in datasets:
            payload = satellite_provider.download(
                meta.dataset_id,
                reference_time=reference_time,
            )
            assert payload.metadata.is_synthetic is True
            assert isinstance(payload.data, xr.DataArray)


# ============================================================
# Radar Data Tests
# ============================================================


class TestRadarData:
    """Test synthetic radar data generation."""

    def test_reflectivity_in_range(self, radar_provider, reference_time):
        """Radar reflectivity values are in physically valid range (0–70 dBZ)."""
        payload = radar_provider.download(
            "synthetic_radar_reflectivity",
            reference_time=reference_time,
        )
        data = payload.data
        assert float(data.min()) >= 0.0
        assert float(data.max()) <= 70.0

    def test_reflectivity_is_synthetic(self, radar_provider, reference_time):
        """Radar data is marked as SYNTHETIC."""
        payload = radar_provider.download(
            "synthetic_radar_reflectivity",
            reference_time=reference_time,
        )
        assert payload.metadata.is_synthetic is True
        assert payload.data.attrs["source"] == "SYNTHETIC"


# ============================================================
# Lightning Data Tests
# ============================================================


class TestLightningData:
    """Test synthetic lightning data generation."""

    def test_lightning_generates_flashes(self, lightning_provider, reference_time):
        """Lightning provider generates flash observations."""
        payload = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        assert isinstance(payload, DataPayload)
        # The data field contains a LightningDataPayload
        lightning_data = payload.data
        assert isinstance(lightning_data, LightningDataPayload)
        assert len(lightning_data.flashes) > 0

    def test_all_flashes_are_synthetic(self, lightning_provider, reference_time):
        """Every lightning flash is marked as synthetic."""
        payload = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        lightning_data = payload.data
        for flash in lightning_data.flashes:
            assert flash.is_synthetic is True

    def test_flashes_inside_bbox(self, lightning_provider, reference_time):
        """All flashes are within the bounding box."""
        payload = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        lightning_data = payload.data
        for flash in lightning_data.flashes:
            assert INDIA_BBOX.contains_point(flash.latitude, flash.longitude), (
                f"Flash at ({flash.latitude}, {flash.longitude}) "
                f"is outside India bounding box"
            )

    def test_flash_types_are_valid(self, lightning_provider, reference_time):
        """Flash types are either 'CG' or 'IC'."""
        payload = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        lightning_data = payload.data
        for flash in lightning_data.flashes:
            assert flash.flash_type in ("CG", "IC")

    def test_lightning_is_deterministic(self, lightning_provider, reference_time):
        """Lightning data is deterministic."""
        p1 = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        p2 = lightning_provider.download(
            "synthetic_lightning_flash_density",
            reference_time=reference_time,
        )
        flashes_1 = p1.data.flashes
        flashes_2 = p2.data.flashes
        assert len(flashes_1) == len(flashes_2)
        for f1, f2 in zip(flashes_1, flashes_2):
            assert f1.latitude == f2.latitude
            assert f1.longitude == f2.longitude


# ============================================================
# NWP Data Tests
# ============================================================


class TestNWPData:
    """Test synthetic NWP (weather model) data generation."""

    def test_cape_in_range(self, nwp_provider, reference_time):
        """CAPE values are in physically valid range (0–5000 J/kg)."""
        payload = nwp_provider.download(
            "synthetic_nwp_cape",
            reference_time=reference_time,
        )
        data = payload.data
        assert float(data.min()) >= 0.0
        assert float(data.max()) <= 5000.0

    def test_cin_is_negative(self, nwp_provider, reference_time):
        """CIN values should be negative or zero (inhibition)."""
        payload = nwp_provider.download(
            "synthetic_nwp_cin",
            reference_time=reference_time,
        )
        data = payload.data
        assert float(data.max()) <= 0.0

    def test_wind_shear_non_negative(self, nwp_provider, reference_time):
        """Wind shear values should be non-negative."""
        payload = nwp_provider.download(
            "synthetic_nwp_wind_shear_0_6km",
            reference_time=reference_time,
        )
        data = payload.data
        assert float(data.min()) >= 0.0

    def test_all_nwp_variables_downloadable(self, nwp_provider, reference_time):
        """Can download all NWP variables."""
        datasets = nwp_provider.search_datasets(
            start_time=reference_time,
            end_time=reference_time,
            bounding_box=INDIA_BBOX,
        )
        for meta in datasets:
            payload = nwp_provider.download(
                meta.dataset_id,
                reference_time=reference_time,
            )
            assert payload.metadata.is_synthetic is True


# ============================================================
# Connection Validation Tests
# ============================================================


class TestValidateConnection:
    """Test the validate_connection method."""

    def test_synthetic_always_connected(self, satellite_provider):
        """Synthetic provider always reports as connected."""
        status = satellite_provider.validate_connection()
        assert status.is_connected is True
        assert status.status == DataSourceStatus.OK

    def test_connection_status_type(self, satellite_provider):
        """Connection status reports the correct source type."""
        status = satellite_provider.validate_connection()
        assert status.source_type == DataSourceType.SATELLITE


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Test error handling in the synthetic provider."""

    def test_invalid_dataset_id_raises(self, satellite_provider):
        """Invalid dataset_id format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid synthetic dataset_id"):
            satellite_provider.download("bad_id")

    def test_unknown_variable_raises(self, satellite_provider):
        """Unknown variable name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown variable"):
            satellite_provider.download("synthetic_satellite_nonexistent_var")

    def test_get_metadata_invalid_id(self, satellite_provider):
        """get_metadata with invalid ID raises ValueError."""
        with pytest.raises(ValueError):
            satellite_provider.get_metadata("bad")
