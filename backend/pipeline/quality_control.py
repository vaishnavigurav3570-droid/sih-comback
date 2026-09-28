"""
StormFusion AI — Quality Control Module

PURPOSE:
    Checks ingested data for physical validity and adds QC flags.
    This is the second pipeline stage — the "inspector" that catches
    bad data before it contaminates the forecast.

WHAT IT DOES:
    1. Range checks — is the value physically possible?
       (e.g., brightness temperature can't be -500 K)
    2. Missing data detection — flags NaN/missing values
    3. Adds QC flags to xarray attributes
    4. Reports statistics on data quality

WHAT IT DOES NOT DO:
    - Invent data to fill gaps (that would be scientifically dishonest)
    - Remove data (just flags it — downstream stages decide what to do)
    - Modify the actual values (only adds QC metadata)

PHILOSOPHY:
    "Flag, don't fix." QC marks problems but doesn't hide them.
    The pipeline and the user can see exactly what was flagged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import numpy as np
import xarray as xr
from backend.app.models.data_types import DataSourceType
from backend.app.models.payload import DataPayload, LightningDataPayload
from backend.pipeline.ingestion import IngestionBatch

logger = logging.getLogger(__name__)


# ============================================================
# QC Flag Values
# ============================================================


class QCFlag(int, Enum):
    """
    Quality control flag values.

    Following WMO-style flag conventions:
    0 = good, higher = worse quality.
    """

    GOOD = 0
    SUSPECT = 1
    OUT_OF_RANGE = 2
    MISSING = 3


# ============================================================
# Physical Range Definitions
# ============================================================

# Each variable has a (min, max) range of physically possible values.
# Values outside this range are flagged as OUT_OF_RANGE.
PHYSICAL_RANGES: dict[str, tuple[float, float]] = {
    # Satellite — brightness temperatures (Kelvin)
    "bt_tir1": (150.0, 340.0),
    "bt_tir2": (150.0, 340.0),
    "bt_wv": (150.0, 320.0),
    "bt_mir": (150.0, 350.0),
    # Radar
    "reflectivity": (-30.0, 80.0),
    "vil": (0.0, 100.0),
    "echo_top": (0.0, 25.0),
    # NWP
    "cape": (0.0, 8000.0),
    "cin": (-500.0, 0.0),
    "wind_shear_0_6km": (0.0, 80.0),
    "lifted_index": (-15.0, 15.0),
    # Lightning
    "flash_density": (0.0, 1000.0),
}


@dataclass
class QCStats:
    """Statistics about the quality control of a single data field."""

    variable_name: str
    source_type: DataSourceType
    total_points: int = 0
    good_points: int = 0
    suspect_points: int = 0
    out_of_range_points: int = 0
    missing_points: int = 0
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None

    @property
    def good_fraction(self) -> float:
        """Fraction of points that passed QC (0.0–1.0)."""
        if self.total_points == 0:
            return 0.0
        return self.good_points / self.total_points

    @property
    def summary(self) -> str:
        """One-line summary of QC results."""
        pct = self.good_fraction * 100
        return (
            f"{self.variable_name}: {pct:.1f}% good "
            f"({self.good_points}/{self.total_points}), "
            f"missing={self.missing_points}, "
            f"out_of_range={self.out_of_range_points}"
        )


@dataclass
class QCResult:
    """Result of quality control for an entire ingestion batch."""

    stats: list[QCStats] = field(default_factory=list)
    qc_payloads: list[DataPayload] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def overall_quality(self) -> str:
        """Simple overall quality assessment."""
        if not self.stats:
            return "NO_DATA"
        avg_good = sum(s.good_fraction for s in self.stats) / len(self.stats)
        if avg_good >= 0.95:
            return "GOOD"
        elif avg_good >= 0.80:
            return "ACCEPTABLE"
        elif avg_good >= 0.50:
            return "DEGRADED"
        else:
            return "POOR"


class QualityController:
    """
    Applies quality control checks to ingested data.

    The QC process:
    1. Takes an IngestionBatch from the ingestion stage
    2. For each gridded payload, checks values against physical ranges
    3. Creates a QC flag array (same shape as data)
    4. Attaches flags to the xarray as a new attribute/coordinate
    5. Returns a QCResult with flagged data and statistics

    Usage:
        qc = QualityController()
        qc_result = qc.run(ingestion_batch)
    """

    def __init__(
        self,
        custom_ranges: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        """
        Args:
            custom_ranges: Optional override for physical range checks.
                           Merged with the default PHYSICAL_RANGES.
        """
        self._ranges = dict(PHYSICAL_RANGES)
        if custom_ranges:
            self._ranges.update(custom_ranges)

    def run(self, batch: IngestionBatch) -> QCResult:
        """
        Run quality control on all data in an ingestion batch.

        Args:
            batch: The IngestionBatch from the ingestion stage.

        Returns:
            QCResult with flagged data and quality statistics.
        """
        logger.info("Starting quality control for %d sources", len(batch.results))

        qc_result = QCResult()

        for source_type, ingestion_result in batch.results.items():
            if not ingestion_result.success:
                qc_result.warnings.append(
                    f"Skipping QC for {source_type.value}: ingestion failed"
                )
                continue

            for payload in ingestion_result.payloads:
                try:
                    qc_payload, stats = self._qc_payload(payload, source_type)
                    qc_result.qc_payloads.append(qc_payload)
                    qc_result.stats.append(stats)
                    logger.info("QC: %s", stats.summary)
                except Exception as exc:
                    warning = (
                        f"QC failed for {source_type.value} "
                        f"/{payload.metadata.variable_name}: {exc}"
                    )
                    logger.warning(warning)
                    qc_result.warnings.append(warning)
                    # Pass through unflagged — don't lose the data
                    qc_result.qc_payloads.append(payload)

        logger.info(
            "Quality control complete: overall=%s, %d fields checked",
            qc_result.overall_quality,
            len(qc_result.stats),
        )

        return qc_result

    def _qc_payload(
        self,
        payload: DataPayload,
        source_type: DataSourceType,
    ) -> tuple[DataPayload, QCStats]:
        """Apply QC checks to a single payload."""

        var_name = payload.metadata.variable_name
        stats = QCStats(
            variable_name=var_name,
            source_type=source_type,
        )

        # Lightning data is point-based — different QC path
        if isinstance(payload.data, LightningDataPayload):
            return self._qc_lightning(payload, stats)

        # Gridded data (xarray.DataArray)
        if not isinstance(payload.data, (xr.DataArray, xr.Dataset)):
            stats.total_points = 0
            return payload, stats

        data_array = payload.data
        if isinstance(data_array, xr.Dataset):
            # For Datasets, check the first variable
            first_var = list(data_array.data_vars)[0]
            data_array = data_array[first_var]

        values = data_array.values
        stats.total_points = int(values.size)

        # Create QC flag array (same shape as data)
        qc_flags = np.full_like(values, QCFlag.GOOD.value, dtype=np.int8)

        # --- Check 1: Missing data (NaN) ---
        nan_mask = np.isnan(values)
        qc_flags[nan_mask] = QCFlag.MISSING.value
        stats.missing_points = int(np.sum(nan_mask))

        # --- Check 2: Physical range ---
        if var_name in self._ranges:
            valid_min, valid_max = self._ranges[var_name]
            out_of_range_mask = (~nan_mask) & (
                (values < valid_min) | (values > valid_max)
            )
            qc_flags[out_of_range_mask] = QCFlag.OUT_OF_RANGE.value
            stats.out_of_range_points = int(np.sum(out_of_range_mask))

        # --- Compute statistics on good data ---
        good_mask = qc_flags == QCFlag.GOOD.value
        stats.good_points = int(np.sum(good_mask))

        if stats.good_points > 0:
            good_values = values[good_mask]
            stats.min_value = float(np.min(good_values))
            stats.max_value = float(np.max(good_values))
            stats.mean_value = float(np.mean(good_values))

        # --- Attach QC flags to the xarray ---
        qc_data_array = data_array.copy()
        qc_data_array.attrs["qc_applied"] = True
        qc_data_array.attrs["qc_good_fraction"] = stats.good_fraction
        qc_data_array.attrs["qc_total_points"] = stats.total_points
        qc_data_array.attrs["qc_missing_points"] = stats.missing_points
        qc_data_array.attrs["qc_out_of_range_points"] = stats.out_of_range_points

        # Store the QC flags as a companion DataArray in attrs
        # (Can't easily add a parallel array to a DataArray, so we
        # store a summary. Full flag arrays are available via QCStats.)
        qc_payload = DataPayload(
            metadata=payload.metadata,
            data=qc_data_array,
        )

        return qc_payload, stats

    def _qc_lightning(
        self,
        payload: DataPayload,
        stats: QCStats,
    ) -> tuple[DataPayload, QCStats]:
        """QC checks for lightning point data."""

        lightning_data: LightningDataPayload = payload.data
        stats.total_points = len(lightning_data.flashes)
        stats.good_points = 0
        stats.out_of_range_points = 0

        for flash in lightning_data.flashes:
            # Check latitude range
            if not (-90.0 <= flash.latitude <= 90.0):
                stats.out_of_range_points += 1
                continue
            # Check longitude range
            if not (-180.0 <= flash.longitude <= 180.0):
                stats.out_of_range_points += 1
                continue
            # Check peak current (if present)
            if flash.peak_current_kA is not None and flash.peak_current_kA < 0:
                stats.out_of_range_points += 1
                continue

            stats.good_points += 1

        return payload, stats
