"""
StormFusion AI — Ingestion Module

PURPOSE:
    Takes data from any DataProvider and loads it into standardized
    xarray structures. This is the first pipeline stage — it's the
    "front door" where raw data enters the processing pipeline.

WHAT IT DOES:
    1. Calls provider.download() to get data
    2. Validates that the data matches our expected format
    3. Wraps everything in a standardized IngestionResult
    4. Handles errors gracefully (logs them, doesn't crash)

WHAT IT DOES NOT DO:
    - Quality control (that's the next stage)
    - Reprojection or regridding (stages 4 and 5)
    - Feature extraction (stage 6+)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import xarray as xr
from backend.app.models.data_types import INDIA_BBOX, BoundingBox, DataSourceType
from backend.app.models.payload import DataPayload, LightningDataPayload
from backend.app.providers.base import DataProvider

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """
    Result of ingesting data from one provider.

    Contains the data (if successful) plus metadata about the ingestion
    process itself (timing, errors, etc.).
    """

    source_type: DataSourceType
    source_name: str
    success: bool = False
    payloads: list[DataPayload] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dataset_count: int = 0
    is_synthetic: bool = False

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAILED"
        return (
            f"<IngestionResult {self.source_type.value} "
            f"status={status} datasets={self.dataset_count} "
            f"synthetic={self.is_synthetic}>"
        )


@dataclass
class IngestionBatch:
    """
    Result of ingesting data from ALL providers for one analysis time.

    This is what gets passed to the next pipeline stage (Quality Control).
    """

    analysis_time: datetime
    region: BoundingBox
    results: dict[DataSourceType, IngestionResult] = field(default_factory=dict)
    is_demo_mode: bool = False

    @property
    def successful_sources(self) -> list[DataSourceType]:
        """Which data sources were ingested successfully."""
        return [src for src, result in self.results.items() if result.success]

    @property
    def failed_sources(self) -> list[DataSourceType]:
        """Which data sources failed to ingest."""
        return [src for src, result in self.results.items() if not result.success]

    @property
    def all_payloads(self) -> list[DataPayload]:
        """Flat list of all successfully ingested payloads."""
        payloads = []
        for result in self.results.values():
            if result.success:
                payloads.extend(result.payloads)
        return payloads

    @property
    def all_warnings(self) -> list[str]:
        """Collect all warnings from all results."""
        warnings = []
        for result in self.results.values():
            warnings.extend(result.warnings)
        return warnings


class IngestionEngine:
    """
    Reads data from providers and produces standardized data payloads.

    This is the first stage of the processing pipeline. It:
    1. Takes a dictionary of providers (from DataProviderFactory)
    2. For each provider, searches and downloads data
    3. Validates the downloaded data has the expected structure
    4. Returns an IngestionBatch containing all results

    Usage:
        factory = DataProviderFactory(settings)
        engine = IngestionEngine(factory.get_all_providers())
        batch = engine.ingest(
            analysis_time=datetime.now(timezone.utc),
            region=INDIA_BBOX,
            time_window_minutes=30,
        )
    """

    def __init__(
        self,
        providers: dict[DataSourceType, DataProvider],
    ) -> None:
        self._providers = providers
        logger.info(
            "IngestionEngine initialized with %d providers: %s",
            len(providers),
            [p.value for p in providers.keys()],
        )

    def ingest(
        self,
        analysis_time: datetime,
        region: BoundingBox = INDIA_BBOX,
        time_window_minutes: int = 30,
    ) -> IngestionBatch:
        """
        Ingest data from all providers for a given analysis time.

        Args:
            analysis_time: The target time to ingest data for (UTC).
            region: Geographic region to query.
            time_window_minutes: How far before/after analysis_time to search.

        Returns:
            IngestionBatch with results from each provider.
        """
        from datetime import timedelta

        start_time = analysis_time - timedelta(minutes=time_window_minutes)
        end_time = analysis_time + timedelta(minutes=time_window_minutes)

        logger.info(
            "Starting ingestion for analysis_time=%s, window=[%s, %s]",
            analysis_time.isoformat(),
            start_time.isoformat(),
            end_time.isoformat(),
        )

        batch = IngestionBatch(
            analysis_time=analysis_time,
            region=region,
        )

        for source_type, provider in self._providers.items():
            result = self._ingest_source(
                provider=provider,
                source_type=source_type,
                start_time=start_time,
                end_time=end_time,
                region=region,
                analysis_time=analysis_time,
            )
            batch.results[source_type] = result

            # Check if any result is synthetic
            if result.is_synthetic:
                batch.is_demo_mode = True

        logger.info(
            "Ingestion complete: %d/%d sources successful",
            len(batch.successful_sources),
            len(batch.results),
        )

        return batch

    def _ingest_source(
        self,
        provider: DataProvider,
        source_type: DataSourceType,
        start_time: datetime,
        end_time: datetime,
        region: BoundingBox,
        analysis_time: datetime,
    ) -> IngestionResult:
        """Ingest data from a single provider."""
        result = IngestionResult(
            source_type=source_type,
            source_name=provider.source_name,
            is_synthetic=not provider.is_available
            or provider.source_name == "Synthetic",
        )

        try:
            # Step 1: Search for available datasets
            datasets = provider.search_datasets(
                start_time=start_time,
                end_time=end_time,
                bounding_box=region,
            )

            if not datasets:
                result.warnings.append(
                    f"No datasets found for {source_type.value} "
                    f"in time window [{start_time}, {end_time}]"
                )
                result.success = True  # No data is not an error
                return result

            logger.info(
                "Found %d datasets for %s",
                len(datasets),
                source_type.value,
            )

            # Step 2: Download each dataset
            for meta in datasets:
                try:
                    payload = provider.download(
                        meta.dataset_id,
                        start_time=start_time,
                        end_time=end_time,
                        reference_time=analysis_time,
                    )

                    # Step 3: Validate the payload
                    validation_errors = self._validate_payload(payload, source_type)
                    if validation_errors:
                        result.warnings.extend(validation_errors)

                    result.payloads.append(payload)
                    result.dataset_count += 1

                except Exception as exc:
                    error_msg = f"Failed to download {meta.dataset_id}: {exc}"
                    logger.warning(error_msg)
                    result.warnings.append(error_msg)

            result.success = True
            result.is_synthetic = any(p.metadata.is_synthetic for p in result.payloads)

        except Exception as exc:
            error_msg = f"Ingestion failed for {source_type.value}: {exc}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False

        return result

    def _validate_payload(
        self,
        payload: DataPayload,
        source_type: DataSourceType,
    ) -> list[str]:
        """
        Validate that a payload has the expected structure.

        Returns a list of validation warnings (empty if all OK).
        """
        warnings: list[str] = []

        # Check metadata
        if payload.metadata is None:
            warnings.append("Payload has no metadata")
            return warnings

        # For gridded data, check xarray structure
        if source_type != DataSourceType.LIGHTNING:
            if isinstance(payload.data, xr.DataArray):
                if "latitude" not in payload.data.dims:
                    warnings.append("DataArray missing 'latitude' dimension")
                if "longitude" not in payload.data.dims:
                    warnings.append("DataArray missing 'longitude' dimension")
                if "source" not in payload.data.attrs:
                    warnings.append("DataArray missing 'source' attribute")
            elif isinstance(payload.data, xr.Dataset):
                pass  # Datasets are also acceptable
            else:
                warnings.append(
                    f"Expected xarray.DataArray or Dataset, "
                    f"got {type(payload.data).__name__}"
                )

        # For lightning data, check it's the right type
        if source_type == DataSourceType.LIGHTNING:
            if not isinstance(payload.data, LightningDataPayload):
                warnings.append(
                    f"Lightning payload expected LightningDataPayload, "
                    f"got {type(payload.data).__name__}"
                )

        return warnings
