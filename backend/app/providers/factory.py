"""
StormFusion AI — Data Provider Factory

Creates the right DataProvider based on configuration.

WHY A FACTORY:
    The pipeline code says "give me a satellite data provider" without
    knowing whether it'll get real MOSDAC data or synthetic data.
    The factory makes that decision based on the application mode
    (DEMO vs LIVE) set in the .env file.

USAGE:
    factory = DataProviderFactory(settings)
    satellite = factory.get_provider(DataSourceType.SATELLITE)
    radar = factory.get_provider(DataSourceType.RADAR)
    all_providers = factory.get_all_providers()
"""

from __future__ import annotations

import logging

from backend.app.core.config import AppMode, Settings
from backend.app.models.data_types import DataSourceType
from backend.app.models.metadata import ConnectionStatus
from backend.app.providers.base import DataProvider
from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.providers.synthetic import SyntheticDataProvider

logger = logging.getLogger(__name__)


class DataProviderFactory:
    """
    Factory that creates DataProvider instances based on configuration.

    In DEMO mode: returns SyntheticDataProvider for everything.
    In LIVE mode: returns real providers where available, falls back to synthetic.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the factory with application settings.

        Args:
            settings: Application configuration (mode, credentials, paths).
        """
        self._settings = settings
        self._providers: dict[DataSourceType, DataProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Set up all providers based on the current mode."""

        if self._settings.stormfusion_mode == AppMode.DEMO:
            logger.info("Running in DEMO mode — all providers will be synthetic")
            self._setup_demo_providers()
        else:
            logger.info("Running in LIVE mode — attempting real providers")
            self._setup_live_providers()

    def _setup_demo_providers(self) -> None:
        """In DEMO mode, every source type gets a SyntheticDataProvider."""
        for source_type in [
            DataSourceType.SATELLITE,
            DataSourceType.RADAR,
            DataSourceType.LIGHTNING,
            DataSourceType.NWP,
        ]:
            self._providers[source_type] = SyntheticDataProvider(
                emulated_source_type=source_type,
            )
            logger.info("Registered SyntheticDataProvider for %s", source_type.value)

    def _setup_live_providers(self) -> None:
        """
        In LIVE mode, try to create real providers.
        Fall back to synthetic for any that aren't available.

        NOTE: Real providers (MOSDAC, Radar, etc.) are NOT implemented yet.
        This method currently falls back to synthetic for everything
        but is structured so real providers can be plugged in later.
        """
        # --- Satellite ---
        try:
            provider = MOSDACSatelliteProvider()
            if provider.is_available:
                self._providers[DataSourceType.SATELLITE] = provider
                logger.info("Using LIVE MOSDACSatelliteProvider")
            else:
                logger.warning(
                    "MOSDAC provider not available (missing mdapi or credentials)"
                )
                self._fallback_to_synthetic(DataSourceType.SATELLITE)
        except Exception as e:
            logger.warning(f"Failed to initialize MOSDAC provider, falling back: {e}")
            self._fallback_to_synthetic(DataSourceType.SATELLITE)

        # --- Radar ---
        # TODO Phase 7: Replace with RadarDataProvider
        self._fallback_to_synthetic(DataSourceType.RADAR)

        # --- Lightning ---
        # TODO Phase 7: Replace with LightningDataProvider
        self._fallback_to_synthetic(DataSourceType.LIGHTNING)

        # --- NWP ---
        # TODO Phase 7: Replace with NWPDataProvider
        self._fallback_to_synthetic(DataSourceType.NWP)

    def _fallback_to_synthetic(self, source_type: DataSourceType) -> None:
        """Register a SyntheticDataProvider as fallback for a source type."""
        if source_type not in self._providers:
            self._providers[source_type] = SyntheticDataProvider(
                emulated_source_type=source_type,
            )
            logger.warning(
                "No real provider for %s — using SyntheticDataProvider (fallback)",
                source_type.value,
            )

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def get_provider(self, source_type: DataSourceType) -> DataProvider:
        """
        Get the configured provider for a specific data source type.

        Args:
            source_type: The type of data source (SATELLITE, RADAR, etc.)

        Returns:
            The DataProvider instance for that source type.

        Raises:
            KeyError: If no provider is configured for the given type.
        """
        if source_type not in self._providers:
            raise KeyError(
                f"No provider configured for source type: {source_type.value}. "
                f"Available: {list(self._providers.keys())}"
            )
        return self._providers[source_type]

    def get_all_providers(self) -> dict[DataSourceType, DataProvider]:
        """
        Get all configured providers.

        Returns:
            Dictionary mapping DataSourceType to DataProvider.
        """
        return dict(self._providers)

    def get_health(self) -> dict[DataSourceType, ConnectionStatus]:
        """
        Check the health of all configured providers.

        Returns:
            Dictionary mapping DataSourceType to ConnectionStatus.
        """
        health: dict[DataSourceType, ConnectionStatus] = {}
        for source_type, provider in self._providers.items():
            try:
                health[source_type] = provider.validate_connection()
            except Exception as exc:
                logger.error(
                    "Health check failed for %s: %s",
                    source_type.value,
                    exc,
                )
                from datetime import datetime, timezone

                health[source_type] = ConnectionStatus(
                    source_type=source_type,
                    status="unavailable",
                    is_connected=False,
                    message=f"Health check error: {exc}",
                    checked_at=datetime.now(timezone.utc),
                )
        return health
