"""
StormFusion AI — Time Synchronization Module

PURPOSE:
    Aligns data from different sources to common analysis times.

THE PROBLEM:
    Different sensors produce data at different rates:
    - Satellite: every 15–30 minutes
    - Radar: every ~10 minutes
    - Lightning: near-real-time (seconds)
    - NWP: every 6–12 hours

    To fuse these sources, we need them all aligned to the same
    "analysis time" — a common reference timestamp.

HOW IT WORKS:
    For each data source, find the observation closest in time to
    the analysis time. If no observation is within the tolerance
    window, mark that source as "stale" or "unavailable."

    This is nearest-neighbor temporal matching. We pick the closest
    observation, we do NOT interpolate in time (that would introduce
    artifacts and is hard to justify scientifically for nowcasting).

TOLERANCE:
    Each source has a different acceptable time offset:
    - Satellite: ±30 minutes (they come at fixed intervals)
    - Radar: ±15 minutes
    - Lightning: ±10 minutes (near real-time)
    - NWP: ±180 minutes (updated much less frequently)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import xarray as xr
from backend.app.models.data_types import DataSourceType
from backend.app.models.payload import DataPayload
from backend.pipeline.quality_control import QCResult

logger = logging.getLogger(__name__)


# Default time tolerance for each source type (in minutes)
DEFAULT_TIME_TOLERANCES: dict[DataSourceType, int] = {
    DataSourceType.SATELLITE: 30,
    DataSourceType.RADAR: 15,
    DataSourceType.LIGHTNING: 10,
    DataSourceType.NWP: 180,
    DataSourceType.SURFACE_STATION: 30,
    DataSourceType.SYNTHETIC: 9999,  # Synthetic data is always "on time"
}


@dataclass
class TimeSyncInfo:
    """Information about how a payload was time-synchronized."""

    source_type: DataSourceType
    variable_name: str
    analysis_time: datetime
    observation_time: datetime
    time_offset_seconds: float
    tolerance_seconds: float
    is_within_tolerance: bool
    is_stale: bool = False

    @property
    def time_offset_minutes(self) -> float:
        """Offset in minutes."""
        return self.time_offset_seconds / 60.0

    @property
    def summary(self) -> str:
        status = "OK" if self.is_within_tolerance else "STALE"
        return (
            f"{self.variable_name}: offset={self.time_offset_minutes:+.1f}min "
            f"[{status}]"
        )


@dataclass
class TimeSyncResult:
    """Result of time synchronization for the full batch."""

    analysis_time: datetime
    synced_payloads: list[DataPayload] = field(default_factory=list)
    sync_info: list[TimeSyncInfo] = field(default_factory=list)
    stale_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def max_offset_minutes(self) -> float:
        """Maximum time offset across all synced payloads."""
        if not self.sync_info:
            return 0.0
        return max(abs(info.time_offset_minutes) for info in self.sync_info)


class TimeSynchronizer:
    """
    Aligns data to a common analysis time using nearest-neighbor matching.

    Each data source has a tolerance window. If the observation is within
    that window, it's considered valid. If not, it's flagged as stale.

    Usage:
        sync = TimeSynchronizer()
        sync_result = sync.run(
            qc_result=qc_result,
            analysis_time=datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc),
        )
    """

    def __init__(
        self,
        tolerances: dict[DataSourceType, int] | None = None,
    ) -> None:
        """
        Args:
            tolerances: Override time tolerances (in minutes) per source type.
        """
        self._tolerances = dict(DEFAULT_TIME_TOLERANCES)
        if tolerances:
            self._tolerances.update(tolerances)

    def run(
        self,
        qc_result: QCResult,
        analysis_time: datetime,
    ) -> TimeSyncResult:
        """
        Synchronize all QC'd payloads to the analysis time.

        Args:
            qc_result: Output from the quality control stage.
            analysis_time: The target time to align everything to.

        Returns:
            TimeSyncResult with synced payloads and offset information.
        """
        logger.info(
            "Starting time sync for analysis_time=%s with %d payloads",
            analysis_time.isoformat(),
            len(qc_result.qc_payloads),
        )

        result = TimeSyncResult(analysis_time=analysis_time)

        for payload in qc_result.qc_payloads:
            sync_info = self._sync_payload(payload, analysis_time)
            result.sync_info.append(sync_info)

            if sync_info.is_within_tolerance:
                # Update the time coordinate to analysis_time
                synced_payload = self._align_time(payload, analysis_time)
                result.synced_payloads.append(synced_payload)
                logger.debug("Synced: %s", sync_info.summary)
            else:
                # Data is too old/new — flag it
                result.stale_sources.append(
                    f"{payload.metadata.source_type.value}"
                    f"/{payload.metadata.variable_name}"
                )
                result.warnings.append(
                    f"STALE: {sync_info.variable_name} is "
                    f"{sync_info.time_offset_minutes:+.1f}min from analysis time "
                    f"(tolerance: ±{sync_info.tolerance_seconds/60:.0f}min)"
                )
                # Still include the data but mark it as stale
                stale_payload = self._mark_stale(payload)
                result.synced_payloads.append(stale_payload)
                logger.warning("Stale: %s", sync_info.summary)

        logger.info(
            "Time sync complete: %d payloads synced, " "%d stale, max offset=%.1fmin",
            len(result.synced_payloads),
            len(result.stale_sources),
            result.max_offset_minutes,
        )

        return result

    def _sync_payload(
        self,
        payload: DataPayload,
        analysis_time: datetime,
    ) -> TimeSyncInfo:
        """Calculate the time offset for a single payload."""

        obs_time = payload.metadata.time_start
        source_type = payload.metadata.source_type

        # Make sure both times are timezone-aware for comparison
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)
        if analysis_time.tzinfo is None:
            analysis_time = analysis_time.replace(tzinfo=timezone.utc)

        offset = (obs_time - analysis_time).total_seconds()
        tolerance_minutes = self._tolerances.get(source_type, 30)
        tolerance_seconds = tolerance_minutes * 60.0

        return TimeSyncInfo(
            source_type=source_type,
            variable_name=payload.metadata.variable_name,
            analysis_time=analysis_time,
            observation_time=obs_time,
            time_offset_seconds=offset,
            tolerance_seconds=tolerance_seconds,
            is_within_tolerance=abs(offset) <= tolerance_seconds,
            is_stale=abs(offset) > tolerance_seconds,
        )

    def _align_time(
        self,
        payload: DataPayload,
        analysis_time: datetime,
    ) -> DataPayload:
        """Update the time coordinate of a payload to the analysis time."""

        if isinstance(payload.data, xr.DataArray):
            aligned = payload.data.copy()
            aligned.coords["time"] = np.datetime64(
                analysis_time.replace(tzinfo=None), "ns"
            )
            aligned.attrs["time_synced"] = True
            aligned.attrs["original_time"] = str(payload.metadata.time_start)
            return DataPayload(metadata=payload.metadata, data=aligned)

        # For non-xarray data (lightning), just pass through
        return payload

    def _mark_stale(self, payload: DataPayload) -> DataPayload:
        """Mark a payload as stale (beyond time tolerance)."""

        if isinstance(payload.data, xr.DataArray):
            stale = payload.data.copy()
            stale.attrs["time_synced"] = False
            stale.attrs["is_stale"] = True
            return DataPayload(metadata=payload.metadata, data=stale)

        return payload
