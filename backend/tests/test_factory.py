"""
Tests for StormFusion AI — DataProviderFactory

Verifies that the factory:
1. Creates correct providers based on configuration
2. In DEMO mode, returns SyntheticDataProvider for all sources
3. Health check works for all providers
"""


import pytest
from backend.app.core.config import AppMode, Settings
from backend.app.models.data_types import DataSourceType
from backend.app.providers.factory import DataProviderFactory
from backend.app.providers.synthetic import SyntheticDataProvider

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def demo_settings() -> Settings:
    """Create settings configured for DEMO mode."""
    return Settings(
        stormfusion_mode=AppMode.DEMO,
        data_dir="./test_data",
        raw_data_dir="./test_data/raw",
        processed_data_dir="./test_data/processed",
        synthetic_data_dir="./test_data/synthetic",
    )


@pytest.fixture
def live_settings() -> Settings:
    """Create settings configured for LIVE mode (without real credentials)."""
    return Settings(
        stormfusion_mode=AppMode.LIVE,
        data_dir="./test_data",
        raw_data_dir="./test_data/raw",
        processed_data_dir="./test_data/processed",
        synthetic_data_dir="./test_data/synthetic",
    )


@pytest.fixture
def demo_factory(demo_settings) -> DataProviderFactory:
    """Create a factory in DEMO mode."""
    return DataProviderFactory(demo_settings)


@pytest.fixture
def live_factory(live_settings) -> DataProviderFactory:
    """Create a factory in LIVE mode (will fall back to synthetic)."""
    return DataProviderFactory(live_settings)


# ============================================================
# DEMO Mode Tests
# ============================================================


class TestDemoMode:
    """Test factory behavior in DEMO mode."""

    def test_satellite_is_synthetic(self, demo_factory):
        """In DEMO mode, satellite provider is synthetic."""
        provider = demo_factory.get_provider(DataSourceType.SATELLITE)
        assert isinstance(provider, SyntheticDataProvider)

    def test_radar_is_synthetic(self, demo_factory):
        """In DEMO mode, radar provider is synthetic."""
        provider = demo_factory.get_provider(DataSourceType.RADAR)
        assert isinstance(provider, SyntheticDataProvider)

    def test_lightning_is_synthetic(self, demo_factory):
        """In DEMO mode, lightning provider is synthetic."""
        provider = demo_factory.get_provider(DataSourceType.LIGHTNING)
        assert isinstance(provider, SyntheticDataProvider)

    def test_nwp_is_synthetic(self, demo_factory):
        """In DEMO mode, NWP provider is synthetic."""
        provider = demo_factory.get_provider(DataSourceType.NWP)
        assert isinstance(provider, SyntheticDataProvider)

    def test_get_all_providers(self, demo_factory):
        """get_all_providers returns all 4 source types."""
        all_providers = demo_factory.get_all_providers()
        assert DataSourceType.SATELLITE in all_providers
        assert DataSourceType.RADAR in all_providers
        assert DataSourceType.LIGHTNING in all_providers
        assert DataSourceType.NWP in all_providers

    def test_unknown_source_type_raises(self, demo_factory):
        """Requesting an unconfigured source type raises KeyError."""
        with pytest.raises(KeyError):
            demo_factory.get_provider(DataSourceType.SURFACE_STATION)


# ============================================================
# LIVE Mode Fallback Tests
# ============================================================


class TestLiveModeFallback:
    """
    Test factory behavior in LIVE mode without real providers.

    Since no real providers are implemented yet, LIVE mode should
    fall back to synthetic for everything.
    """

    def test_live_falls_back_to_synthetic(self, live_factory):
        """LIVE mode falls back to SyntheticDataProvider when no real provider exists."""
        provider = live_factory.get_provider(DataSourceType.SATELLITE)
        assert isinstance(provider, SyntheticDataProvider)


# ============================================================
# Health Check Tests
# ============================================================


class TestHealthCheck:
    """Test the factory's health check functionality."""

    def test_health_all_ok(self, demo_factory):
        """In DEMO mode, all providers should report OK."""
        health = demo_factory.get_health()
        assert len(health) == 4
        for source_type, status in health.items():
            assert status.is_connected is True
