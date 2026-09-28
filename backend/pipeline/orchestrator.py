"""
StormFusion AI — Pipeline Orchestrator

Runs all pipeline stages in sequence:
    Ingestion → Quality Control → Time Sync → Geo Alignment → Common Grid

This module is the "main" entry point for the processing pipeline.
You call Pipeline.run() and it executes all stages in order,
passing the output of each stage to the next.

Usage:
    from backend.pipeline.orchestrator import Pipeline

    pipeline = Pipeline(providers=factory.get_all_providers())
    result = pipeline.run(
        analysis_time=datetime.now(timezone.utc),
        region=INDIA_BBOX,
    )
    # result.dataset is an xarray.Dataset with all variables on one grid
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import xarray as xr
from backend.app.models.data_types import INDIA_BBOX, BoundingBox, DataSourceType
from backend.app.providers.base import DataProvider
from backend.pipeline.common_grid import CommonGridder, CommonGridResult, GridSpec
from backend.pipeline.feature_extraction import (
    FeatureExtractionResult,
    FeatureExtractor,
)
from backend.pipeline.fusion import DataFuser, FusionResult
from backend.pipeline.geo_alignment import GeoAligner, GeoAlignResult
from backend.pipeline.ingestion import IngestionBatch, IngestionEngine
from backend.pipeline.prediction import PredictionResult, Predictor
from backend.pipeline.quality_control import QCResult, QualityController
from backend.pipeline.time_sync import TimeSynchronizer, TimeSyncResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """
    Complete result from running the full processing pipeline.

    Contains the final dataset plus results from each individual stage
    for inspection and debugging.
    """

    # Final output
    dataset: xr.Dataset | None = None
    grid_spec: GridSpec | None = None
    analysis_time: datetime | None = None
    is_synthetic: bool = False

    # Intermediate results (for debugging/inspection)
    ingestion_result: IngestionBatch | None = None
    qc_result: QCResult | None = None
    time_sync_result: TimeSyncResult | None = None
    geo_align_result: GeoAlignResult | None = None
    common_grid_result: CommonGridResult | None = None
    feature_extraction_result: FeatureExtractionResult | None = None
    fusion_result: FusionResult | None = None
    prediction_result: PredictionResult | None = None

    # Diagnostics
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    success: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        """How long the pipeline took to run."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def variables(self) -> list[str]:
        """List of variable names in the final dataset."""
        if self.dataset is not None:
            return list(self.dataset.data_vars)
        return []


class Pipeline:
    """
    Orchestrates the full data processing pipeline.

    Stages:
    1. IngestionEngine — reads from providers
    2. QualityController — range checks + flags
    3. TimeSynchronizer — aligns to analysis time
    4. GeoAligner — ensures common CRS
    5. CommonGridder — interpolates to uniform grid
    6. FeatureExtractor — computes derived predictors
    7. DataFuser — stacks into ML-ready tensor
    8. Predictor — runs ML model to generate ForecastProducts

    Usage:
        pipeline = Pipeline(
            providers=factory.get_all_providers(),
            grid_spec=GridSpec(bbox=INDIA_BBOX, resolution_deg=0.5),
        )
        result = pipeline.run(analysis_time=datetime.now(timezone.utc))
    """

    def __init__(
        self,
        providers: dict[DataSourceType, DataProvider],
        grid_spec: GridSpec | None = None,
        time_tolerances: dict[DataSourceType, int] | None = None,
        custom_qc_ranges: dict[str, tuple[float, float]] | None = None,
        predictor_kwargs: dict | None = None,
    ) -> None:
        """
        Args:
            providers: Dictionary of data providers from the factory.
            grid_spec: Target grid specification (default: India 0.5°).
            time_tolerances: Override time tolerances per source type.
            custom_qc_ranges: Override physical range checks.
            predictor_kwargs: Kwargs to pass to the Predictor.
        """
        self._ingestion = IngestionEngine(providers)
        self._qc = QualityController(custom_ranges=custom_qc_ranges)
        self._time_sync = TimeSynchronizer(tolerances=time_tolerances)
        self._geo_align = GeoAligner()
        self._gridder = CommonGridder(grid_spec=grid_spec)
        self._feature_extractor = FeatureExtractor()
        self._fuser = DataFuser()
        self._predictor = Predictor(**(predictor_kwargs or {}))

        logger.info("Pipeline initialized with %d providers", len(providers))

    def run(
        self,
        analysis_time: datetime | None = None,
        region: BoundingBox = INDIA_BBOX,
        time_window_minutes: int = 30,
    ) -> PipelineResult:
        """
        Execute the full processing pipeline.

        Args:
            analysis_time: Target time (default: now UTC).
            region: Geographic region of interest.
            time_window_minutes: Search window around analysis time.

        Returns:
            PipelineResult with the final dataset and intermediate results.
        """
        if analysis_time is None:
            analysis_time = datetime.now(timezone.utc)

        result = PipelineResult(
            analysis_time=analysis_time,
            started_at=datetime.now(timezone.utc),
        )

        logger.info(
            "═══ PIPELINE START ═══ analysis_time=%s",
            analysis_time.isoformat(),
        )

        try:
            # Stage 1: Ingestion
            logger.info("── Stage 1/5: Ingestion ──")
            ingestion_batch = self._ingestion.ingest(
                analysis_time=analysis_time,
                region=region,
                time_window_minutes=time_window_minutes,
            )
            result.ingestion_result = ingestion_batch
            result.warnings.extend(ingestion_batch.all_warnings)

            if not ingestion_batch.successful_sources:
                result.errors.append("No data sources were ingested successfully")
                result.completed_at = datetime.now(timezone.utc)
                return result

            # Stage 2: Quality Control
            logger.info("── Stage 2/5: Quality Control ──")
            qc_result = self._qc.run(ingestion_batch)
            result.qc_result = qc_result
            result.warnings.extend(qc_result.warnings)

            if not qc_result.qc_payloads:
                result.errors.append("No data survived quality control")
                result.completed_at = datetime.now(timezone.utc)
                return result

            # Stage 3: Time Synchronization
            logger.info("── Stage 3/5: Time Synchronization ──")
            sync_result = self._time_sync.run(
                qc_result=qc_result,
                analysis_time=analysis_time,
            )
            result.time_sync_result = sync_result
            result.warnings.extend(sync_result.warnings)

            # Stage 4: Geospatial Alignment
            logger.info("── Stage 4/5: Geospatial Alignment ──")
            geo_result = self._geo_align.run(sync_result)
            result.geo_align_result = geo_result
            result.warnings.extend(geo_result.warnings)

            # Stage 5: Common Grid
            logger.info("── Stage 5/5: Common Grid ──")
            grid_result = self._gridder.run(
                geo_result=geo_result,
                analysis_time=analysis_time,
            )
            result.common_grid_result = grid_result
            result.dataset = grid_result.dataset
            result.grid_spec = grid_result.grid_spec
            result.is_synthetic = grid_result.is_synthetic
            result.warnings.extend(grid_result.warnings)

            if result.dataset is None:
                result.errors.append("Common Grid stage failed to produce a dataset")
                result.completed_at = datetime.now(timezone.utc)
                return result

            # Stage 6: Feature Extraction
            logger.info("── Stage 6/7: Feature Extraction ──")
            feature_result = self._feature_extractor.run(grid_result)
            result.feature_extraction_result = feature_result
            result.dataset = feature_result.dataset
            result.warnings.extend(feature_result.warnings)

            # Stage 7: Data Fusion
            logger.info("── Stage 7/8: Data Fusion ──")
            fusion_result = self._fuser.run(feature_result)
            result.fusion_result = fusion_result
            result.warnings.extend(fusion_result.warnings)

            if fusion_result.feature_tensor is None:
                result.errors.append("Data Fusion stage failed to produce a tensor")
                result.completed_at = datetime.now(timezone.utc)
                return result

            # Stage 8: Prediction
            logger.info("── Stage 8/8: Prediction ──")
            prediction_result = self._predictor.run(result)
            result.prediction_result = prediction_result
            result.warnings.extend(prediction_result.warnings)

            result.success = prediction_result.forecast_product is not None

        except Exception as exc:
            error_msg = f"Pipeline failed: {exc}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.success = False

        result.completed_at = datetime.now(timezone.utc)

        logger.info(
            "═══ PIPELINE %s ═══ duration=%.2fs, variables=%s, synthetic=%s",
            "COMPLETE" if result.success else "FAILED",
            result.duration_seconds or 0,
            result.variables,
            result.is_synthetic,
        )

        return result
