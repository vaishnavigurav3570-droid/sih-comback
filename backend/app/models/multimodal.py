from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
from backend.app.models.payload import DataPayload

class ModalityStatus(BaseModel):
    is_available: bool = Field(..., description="Whether the modality was successfully acquired")
    source_name: str = Field(..., description="Name of the source")
    is_synthetic: bool = Field(..., description="True if synthetic, False if real")
    time_offset_seconds: float = Field(default=0.0, description="Offset from target time")
    missing_cells_count: int | None = Field(default=None, description="Number of missing cells on common grid")
    total_cells_count: int | None = Field(default=None, description="Total number of cells on common grid")

class MultimodalSample(BaseModel):
    """
    A synchronized sample combining all available modalities for a target timestamp.
    """
    target_timestamp: datetime = Field(..., description="The target analysis time")
    
    # Combined common-grid dataset
    dataset: Any = Field(default=None, description="xarray.Dataset containing all aligned variables")
    
    # Status per modality
    satellite_status: ModalityStatus | None = None
    radar_status: ModalityStatus | None = None
    lightning_status: ModalityStatus | None = None
    nwp_status: ModalityStatus | None = None
    
    provenance: str = Field(default="MIXED", description="REAL, SYNTHETIC, or MIXED")
    
    model_config = {"arbitrary_types_allowed": True}
