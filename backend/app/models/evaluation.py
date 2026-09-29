from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import numpy as np

@dataclass
class TargetDefinition:
    """Configurable target definition to decouple physical logic from binary model requirements."""
    name: str
    description: str
    threshold_value: Optional[float] = None
    is_binary: bool = True
    variable_name: str = ""

@dataclass
class TargetQCResult:
    """Target quality control metadata."""
    is_valid: bool
    missing_percentage: float
    duplicate_observations: int
    impossible_values_count: int
    spatial_coverage_fraction: float
    temporal_validity: bool
    warnings: List[str] = field(default_factory=list)

@dataclass
class SampleManifest:
    """Machine-readable description of a single sample to guarantee reproducibility and auditability."""
    sample_id: str
    input_timestamps: List[datetime]
    target_timestamp: datetime
    forecast_origin: datetime
    source_modalities: List[str]
    target_source: str
    target_definition_version: str
    provenance: str
    spatial_grid_shape: tuple
    qc_status: TargetQCResult
    split_assignment: Optional[str] = None

@dataclass
class EvaluationMetrics:
    """Scientifically appropriate metrics for nowcasting."""
    precision: float
    recall: float
    far: float
    f1: float
    csi: float # Critical Success Index
    brier_score: float
    confusion_matrix: Dict[str, int] # TP, FP, TN, FN
    reliability_curve: Optional[Dict[str, List[float]]] = None

@dataclass
class BaselinePrediction:
    """Abstract representation of a baseline model output."""
    baseline_name: str
    prediction_tensor: np.ndarray # Could be binary or probabilistic
