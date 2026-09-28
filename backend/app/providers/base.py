"""
StormFusion AI — Abstract Data Provider Interface

This is the contract that EVERY data source must follow.

WHY THIS EXISTS:
    The processing pipeline should never care whether it's reading
    real satellite data from MOSDAC or fake data from the synthetic
    provider. This abstract class defines the "shape" that every
    provider must match, so the pipeline code stays the same
    regardless of the data source.

HOW IT WORKS:
    1. Every provider (Satellite, Radar, Lightning, NWP, Synthetic)
       inherits from DataProvider.
    2. Every provider implements all the abstract methods.
    3. The DataProviderFactory creates the right provider based on
       configuration (DEMO mode vs LIVE mode).
    4. The pipeline only ever talks to the DataProvider interface.

ANALOGY:
    Think of DataProvider like a USB port. It doesn't matter if you
    plug in a keyboard, mouse, or flash drive — they all use the
    same USB interface. Similarly, it doesn't matter if data comes
    from MOSDAC or a synthetic generator — they all use the same
    DataProvider interface.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from backend.app.models.data_types import BoundingBox, DataSourceType
from backend.app.models.metadata import ConnectionStatus, DatasetMetadata
from backend.app.models.payload import DataPayload

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """
    Abstract base class for all data providers.

    Every data source in StormFusion must implement this interface.
    This ensures the pipeline can work with any source without
    knowing the implementation details.
    """

    # ----------------------------------------------------------
    # Abstract properties — must be implemented by subclasses
    # ----------------------------------------------------------

    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """
        The type of data this provider supplies.

        Returns:
            DataSourceType enum value (e.g., SATELLITE, RADAR, SYNTHETIC)
        """
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Human-readable name of this data source.

        Returns:
            String like "MOSDAC", "Synthetic", "DWR Mumbai", etc.
        """
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Whether this provider can currently serve data.

        For SyntheticDataProvider, this is always True.
        For MOSDACSatelliteProvider, this depends on credentials and connectivity.

        Returns:
            True if the provider is ready to serve data.
        """
        ...

    # ----------------------------------------------------------
    # Abstract methods — must be implemented by subclasses
    # ----------------------------------------------------------

    @abstractmethod
    def search_datasets(
        self,
        start_time: datetime,
        end_time: datetime,
        bounding_box: BoundingBox,
        variables: list[str] | None = None,
        count: int = 10,
    ) -> list[DatasetMetadata]:
        """
        Search for available datasets matching the given criteria.

        Args:
            start_time: Start of time range to search (UTC).
            end_time: End of time range to search (UTC).
            bounding_box: Geographic region to search within.
            variables: Optional list of variable names to filter by.
            count: Maximum number of results to return.

        Returns:
            List of DatasetMetadata objects describing available datasets.
        """
        ...

    @abstractmethod
    def download(
        self,
        dataset_id: str,
        output_dir: Path | None = None,
        **kwargs,
    ) -> DataPayload:
        """
        Download or generate data for a specific dataset.

        For real providers: downloads from the external source.
        For SyntheticDataProvider: generates data deterministically.

        Args:
            dataset_id: The unique ID of the dataset to retrieve.
            output_dir: Optional directory to save downloaded files.
            **kwargs: Additional provider-specific parameters.

        Returns:
            DataPayload containing the data and its metadata.
        """
        ...

    @abstractmethod
    def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """
        Get metadata for a specific dataset without downloading the data.

        Args:
            dataset_id: The unique ID of the dataset.

        Returns:
            DatasetMetadata describing the dataset.
        """
        ...

    @abstractmethod
    def validate_connection(self) -> ConnectionStatus:
        """
        Check if this provider is reachable and properly configured.

        For real providers: tests credentials, network connectivity.
        For SyntheticDataProvider: always returns OK.

        Returns:
            ConnectionStatus with health information.
        """
        ...

    # ----------------------------------------------------------
    # Concrete helper methods (shared by all providers)
    # ----------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"source_type={self.source_type.value} "
            f"source_name='{self.source_name}' "
            f"available={self.is_available}>"
        )
