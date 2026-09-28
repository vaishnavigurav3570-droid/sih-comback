"""
Tests for StormFusion AI — Processing Pipeline (Phase 2)

Tests the full pipeline from ingestion through common grid:
1. Ingestion — reads from providers
2. Quality Control — range checks, flags
3. Time Synchronization — aligns to analysis time
4. Geospatial Alignment — validates CRS
5. Common Grid — regrid to uniform grid
6. Full pipeline integration — end-to-end test
"""

from datetime import datetime, timezone

import pytest
import xarray as xr
from backend.app.core.config import AppMode, Settings
from backend.app.models.data_types import (
    INDIA_BBOX,
    BoundingBox,
    DataSourceType,
)
from backend.app.providers.factory import DataProviderFactory
from backend.app.providers.synthetic import SyntheticDataProvider
from backend.pipeline.common_grid import CommonGridder, GridSpec
from backend.pipeline.geo_alignment import GeoAligner
from backend.pipeline.ingestion import IngestionEngine
from backend.pipeline.orchestrator import Pipeline
from backend.pipeline.quality_control import QCFlag, QualityController
from backend.pipeline.time_sync import TimeSynchronizer

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def demo_settings() -> Settings:
    """Settings for demo mode."""
    return Settings(
        stormfusion_mode=AppMode.DEMO,
        data_dir="./test_data",
        raw_data_dir="./test_data/raw",
        processed_data_dir="./test_data/processed",
        synthetic_data_dir="./test_data/synthetic",
    )


@pytest.fixture
def providers(demo_settings) -> dict[DataSourceType, SyntheticDataProvider]:
    """All synthetic providers."""
    factory = DataProviderFactory(demo_settings)
    return factory.get_all_providers()


@pytest.fixture
def reference_time() -> datetime:
    """Fixed reference time."""
    return datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def small_bbox() -> BoundingBox:
    """Small region for faster tests."""
    return BoundingBox(west=78.0, south=20.0, east=82.0, north=24.0)


@pytest.fixture
def small_grid_spec(small_bbox) -> GridSpec:
    """Small grid spec for faster tests."""
    return GridSpec(bbox=small_bbox, resolution_deg=1.0)


# ============================================================
# Stage 1: Ingestion Tests
# ============================================================


class TestIngestion:
    """Test the ingestion engine."""

    def test_ingest_all_sources(self, providers, reference_time):
        """Ingestion returns results for all providers."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        assert len(batch.results) == len(providers)
        assert len(batch.successful_sources) > 0

    def test_all_ingested_data_is_synthetic(self, providers, reference_time):
        """In demo mode, all ingested data is synthetic."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        for result in batch.results.values():
            if result.success and result.payloads:
                for payload in result.payloads:
                    assert payload.metadata.is_synthetic is True

    def test_ingestion_batch_has_payloads(self, providers, reference_time):
        """Ingestion batch contains actual data payloads."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        assert len(batch.all_payloads) > 0

    def test_ingestion_handles_missing_provider_gracefully(self, reference_time):
        """Ingestion works with a subset of providers."""
        partial = {
            DataSourceType.SATELLITE: SyntheticDataProvider(
                emulated_source_type=DataSourceType.SATELLITE
            ),
        }
        engine = IngestionEngine(partial)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        assert len(batch.results) == 1
        assert batch.results[DataSourceType.SATELLITE].success is True


# ============================================================
# Stage 2: Quality Control Tests
# ============================================================


class TestQualityControl:
    """Test the quality controller."""

    def test_qc_synthetic_data_all_good(self, providers, reference_time):
        """Synthetic data should pass QC (it's designed to be in range)."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        assert len(qc_result.qc_payloads) > 0
        assert qc_result.overall_quality in ("GOOD", "ACCEPTABLE")

    def test_qc_adds_attributes(self, providers, reference_time):
        """QC adds quality attributes to xarray data."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        for payload in qc_result.qc_payloads:
            if isinstance(payload.data, xr.DataArray):
                assert "qc_applied" in payload.data.attrs
                assert payload.data.attrs["qc_applied"] is True

    def test_qc_stats_populated(self, providers, reference_time):
        """QC produces statistics for each field."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        assert len(qc_result.stats) > 0
        for stat in qc_result.stats:
            assert stat.total_points > 0
            assert stat.good_fraction >= 0.0

    def test_qc_flag_enum_values(self):
        """QC flags have correct integer values."""
        assert QCFlag.GOOD.value == 0
        assert QCFlag.SUSPECT.value == 1
        assert QCFlag.OUT_OF_RANGE.value == 2
        assert QCFlag.MISSING.value == 3


# ============================================================
# Stage 3: Time Synchronization Tests
# ============================================================


class TestTimeSynchronization:
    """Test the time synchronizer."""

    def test_sync_aligns_to_analysis_time(self, providers, reference_time):
        """All payloads get aligned to the analysis time."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)

        assert len(sync_result.synced_payloads) > 0
        assert sync_result.analysis_time == reference_time

    def test_sync_records_offsets(self, providers, reference_time):
        """Time sync records offset info for each payload."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)

        assert len(sync_result.sync_info) > 0
        for info in sync_result.sync_info:
            assert info.analysis_time == reference_time

    def test_synthetic_data_always_within_tolerance(self, providers, reference_time):
        """Synthetic data should always be within time tolerance."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)

        qc = QualityController()
        qc_result = qc.run(batch)

        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)

        # No sources should be stale with synthetic data
        assert len(sync_result.stale_sources) == 0


# ============================================================
# Stage 4: Geospatial Alignment Tests
# ============================================================


class TestGeoAlignment:
    """Test the geospatial aligner."""

    def test_geo_alignment_preserves_data(self, providers, reference_time):
        """Geo alignment doesn't lose any data."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)
        qc = QualityController()
        qc_result = qc.run(batch)
        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)

        aligner = GeoAligner()
        geo_result = aligner.run(sync_result)

        assert len(geo_result.aligned_payloads) == len(sync_result.synced_payloads)

    def test_geo_alignment_sets_crs(self, providers, reference_time):
        """Aligned data has CRS attribute set."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)
        qc = QualityController()
        qc_result = qc.run(batch)
        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)

        aligner = GeoAligner()
        geo_result = aligner.run(sync_result)

        for payload in geo_result.aligned_payloads:
            if isinstance(payload.data, xr.DataArray):
                assert payload.data.attrs.get("crs") == "EPSG:4326"


# ============================================================
# Stage 5: Common Grid Tests
# ============================================================


class TestCommonGrid:
    """Test the common gridder."""

    def test_grid_spec_dimensions(self):
        """GridSpec computes correct grid dimensions."""
        spec = GridSpec(
            bbox=BoundingBox(west=78.0, south=20.0, east=82.0, north=24.0),
            resolution_deg=1.0,
        )
        assert spec.nlat > 0
        assert spec.nlon > 0
        assert len(spec.latitudes) == spec.nlat
        assert len(spec.longitudes) == spec.nlon

    def test_gridding_produces_dataset(
        self, providers, reference_time, small_grid_spec
    ):
        """Full pipeline through to gridding produces an xarray.Dataset."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)
        qc = QualityController()
        qc_result = qc.run(batch)
        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)
        aligner = GeoAligner()
        geo_result = aligner.run(sync_result)

        gridder = CommonGridder(grid_spec=small_grid_spec)
        grid_result = gridder.run(geo_result=geo_result, analysis_time=reference_time)

        assert grid_result.dataset is not None
        assert isinstance(grid_result.dataset, xr.Dataset)
        assert len(grid_result.dataset.data_vars) > 0

    def test_gridded_data_has_correct_shape(
        self, providers, reference_time, small_grid_spec
    ):
        """Each variable in the dataset has the shape of the target grid."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)
        qc = QualityController()
        qc_result = qc.run(batch)
        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)
        aligner = GeoAligner()
        geo_result = aligner.run(sync_result)

        gridder = CommonGridder(grid_spec=small_grid_spec)
        grid_result = gridder.run(geo_result=geo_result, analysis_time=reference_time)

        expected_shape = small_grid_spec.shape
        for var_name in grid_result.dataset.data_vars:
            var = grid_result.dataset[var_name]
            assert (
                var.shape == expected_shape
            ), f"{var_name} shape {var.shape} != expected {expected_shape}"

    def test_gridded_dataset_is_synthetic(
        self, providers, reference_time, small_grid_spec
    ):
        """In demo mode, gridded dataset is marked synthetic."""
        engine = IngestionEngine(providers)
        batch = engine.ingest(analysis_time=reference_time, region=INDIA_BBOX)
        qc = QualityController()
        qc_result = qc.run(batch)
        sync = TimeSynchronizer()
        sync_result = sync.run(qc_result=qc_result, analysis_time=reference_time)
        aligner = GeoAligner()
        geo_result = aligner.run(sync_result)

        gridder = CommonGridder(grid_spec=small_grid_spec)
        grid_result = gridder.run(geo_result=geo_result, analysis_time=reference_time)

        assert grid_result.is_synthetic is True


# ============================================================
# Full Pipeline Integration Tests
# ============================================================


class TestFullPipeline:
    """Test the full pipeline orchestrator end-to-end."""

    def test_pipeline_runs_successfully(
        self, providers, reference_time, small_grid_spec
    ):
        """Full pipeline completes without errors."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        assert result.success is True
        assert result.dataset is not None
        assert len(result.errors) == 0

    def test_pipeline_produces_multiple_variables(
        self, providers, reference_time, small_grid_spec
    ):
        """Pipeline output contains variables from multiple sources."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        # Should have satellite + radar + NWP + lightning variables
        assert len(result.variables) >= 4

    def test_pipeline_result_has_intermediate_results(
        self, providers, reference_time, small_grid_spec
    ):
        """Pipeline result contains all intermediate stage results."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        assert result.ingestion_result is not None
        assert result.qc_result is not None
        assert result.time_sync_result is not None
        assert result.geo_align_result is not None
        assert result.common_grid_result is not None

    def test_pipeline_records_duration(
        self, providers, reference_time, small_grid_spec
    ):
        """Pipeline records how long it took."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        assert result.duration_seconds is not None
        assert result.duration_seconds > 0

    def test_pipeline_is_synthetic_in_demo(
        self, providers, reference_time, small_grid_spec
    ):
        """Pipeline output is marked synthetic in demo mode."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        assert result.is_synthetic is True

    def test_pipeline_dataset_coordinates(
        self, providers, reference_time, small_grid_spec
    ):
        """Final dataset has proper lat/lon coordinates."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(analysis_time=reference_time, region=INDIA_BBOX)

        ds = result.dataset
        assert "latitude" in ds.dims
        assert "longitude" in ds.dims

        lats = ds.coords["latitude"].values
        lons = ds.coords["longitude"].values

        # Should cover the small_bbox region
        assert float(lats[0]) >= 20.0
        assert float(lats[-1]) <= 24.0
        assert float(lons[0]) >= 78.0
        assert float(lons[-1]) <= 82.0

    def test_pipeline_with_default_time(self, providers, small_grid_spec):
        """Pipeline works with default analysis time (now)."""
        pipeline = Pipeline(
            providers=providers,
            grid_spec=small_grid_spec,
        )
        result = pipeline.run(region=INDIA_BBOX)

        assert result.success is True
        assert result.analysis_time is not None
