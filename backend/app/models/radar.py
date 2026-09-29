from datetime import datetime
from pydantic import BaseModel
from backend.app.models.data_types import DataSourceType

class RadarMetadata(BaseModel):
    """Metadata representing a radar volume observation."""
    source_type: DataSourceType = DataSourceType.RADAR
    source_name: str
    radar_id: str
    latitude: float
    longitude: float
    altitude: float
    start_time: datetime
    end_time: datetime
    sweep_count: int
    field_names: list[str]
    units: dict[str, str]
    provenance: str
    is_synthetic: bool = False
    file_path: str = ""
