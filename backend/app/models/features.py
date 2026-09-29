from pydantic import BaseModel, Field
from typing import Any, List
import numpy as np

class FeatureMetadata(BaseModel):
    name: str = Field(..., description="Name of the feature (e.g., 'IMG_TIR1', 'TIR1_spatial_grad')")
    source_modality: str = Field(..., description="satellite, radar, lightning, nwp, or derived")
    physical_meaning: str = Field(..., description="Physical meaning of the feature")
    units: str = Field(..., description="Physical units")
    is_continuous: bool = Field(True, description="True if continuous, False if categorical/count")
    depends_on_synthetic: bool = Field(..., description="True if derived from synthetic sources")
    normalization_method: str | None = Field(None, description="Recommended normalization (e.g., 'z-score', 'min-max')")

class MLFeatureBatch(BaseModel):
    """
    The final ML-ready representation.
    """
    timestamps: List[str] = Field(..., description="List of timestamps in this batch")
    feature_names: List[str] = Field(..., description="Deterministic ordering of features in the tensor")
    feature_registry: dict[str, FeatureMetadata] = Field(..., description="Metadata for each feature")
    
    # Core Tensors. Shape: (batch_time, channels, latitude, longitude)
    tensor: Any = Field(..., description="Numerical feature tensor. Missing values remain NaN.")
    validity_mask: Any = Field(..., description="Boolean tensor where True = valid observation, False = missing/invalid")
    
    provenance: str = Field(..., description="REAL, SYNTHETIC, or MIXED")
    
    model_config = {"arbitrary_types_allowed": True}
