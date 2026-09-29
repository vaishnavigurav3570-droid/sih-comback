from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

@dataclass
class TargetCandidateInfo:
    source: str
    product: str
    modality: str
    provenance: str  # 'REAL', 'SYNTHETIC', 'UNKNOWN'
    format: str
    date_coverage: str
    time_resolution: str
    spatial_resolution: str
    geographic_coverage: str
    variables: str
    target_suitability: str
    input_suitability: str
    may_29_available: bool
    time_window_compatible: bool
    access_status: str  # 'VERIFIED_AVAILABLE', 'SEARCH_ONLY', 'DOWNLOAD_FAILED', 'NOT_FOUND', 'UNKNOWN', 'INCOMPATIBLE'
    limitations: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "product": self.product,
            "modality": self.modality,
            "REAL/SYNTHETIC/UNKNOWN": self.provenance,
            "format": self.format,
            "date coverage": self.date_coverage,
            "time resolution": self.time_resolution,
            "spatial resolution": self.spatial_resolution,
            "geographic coverage": self.geographic_coverage,
            "variables": self.variables,
            "target suitability": self.target_suitability,
            "input suitability": self.input_suitability,
            "29-May-2025 availability": "Yes" if self.may_29_available else "No",
            "12:00–15:00 compatibility": "Yes" if self.time_window_compatible else "No",
            "access status": self.access_status,
            "limitations": self.limitations
        }

def calculate_temporal_compatibility(source_time: datetime, target_time: datetime) -> Dict[str, Any]:
    offset = abs((source_time - target_time).total_seconds()) / 60.0
    return {
        "nearest_observation": source_time.isoformat(),
        "time_offset_minutes": offset,
        "is_acceptable": offset <= 15.0  # Allow up to 15 min offset for compatibility
    }

def calculate_spatial_compatibility(
    source_lat_range: tuple[float, float],
    source_lon_range: tuple[float, float],
    target_lat_range: tuple[float, float] = (8.4, 37.6),
    target_lon_range: tuple[float, float] = (68.7, 97.2)
) -> bool:
    lat_overlap = not (source_lat_range[1] < target_lat_range[0] or source_lat_range[0] > target_lat_range[1])
    lon_overlap = not (source_lon_range[1] < target_lon_range[0] or source_lon_range[0] > target_lon_range[1])
    return lat_overlap and lon_overlap
