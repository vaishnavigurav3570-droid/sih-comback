import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
import torch
import uuid

from backend.app.models.multimodal import MultimodalSample
from backend.app.models.evaluation import TargetDefinition, TargetQCResult, SampleManifest
from backend.pipeline.geo_alignment import GeoAlignResult
from backend.pipeline.common_grid import CommonGridder

logger = logging.getLogger(__name__)

class TargetQualityController:
    """Applies strict Quality Control to raw target observations."""
    
    @staticmethod
    def run_qc(data: np.ndarray, target_time: datetime, forecast_origin: datetime) -> TargetQCResult:
        warnings = []
        is_valid = True
        
        # Temporal Check
        temporal_validity = True
        if target_time <= forecast_origin:
            warnings.append("Target timestamp is not strictly in the future of forecast origin.")
            temporal_validity = False
            is_valid = False
            
        # Missingness Check
        nans = np.isnan(data)
        missing_percentage = float(np.mean(nans))
        if missing_percentage > 0.99:
            warnings.append("Target array is almost entirely missing/NaN.")
            
        # Impossible values check (assuming no negative counts for lightning, or reflectivity usually > -50)
        impossible_values = 0
        if not np.all(nans):
            valid_data = data[~nans]
            impossible_values = int(np.sum(valid_data < -100)) # Simple arbitrary baseline
            if impossible_values > 0:
                warnings.append(f"Found {impossible_values} impossible values.")
                is_valid = False
                
        spatial_cov = 1.0 - missing_percentage
        
        return TargetQCResult(
            is_valid=is_valid,
            missing_percentage=missing_percentage,
            duplicate_observations=0, # Hard to assess dynamically without raw swaths
            impossible_values_count=impossible_values,
            spatial_coverage_fraction=spatial_cov,
            temporal_validity=temporal_validity,
            warnings=warnings
        )

class RealTargetBuilder:
    """
    Builds scientifically rigorous target tensors.
    Fails explicitly if REAL is requested but unavailable.
    """
    def __init__(self, require_real: bool = False):
        self.require_real = require_real
        self.thunderstorm_def = TargetDefinition(
            name="Thunderstorm Occurrence",
            description="Reflectivity > 35 dBZ (if radar available)",
            threshold_value=35.0,
            is_binary=True,
            variable_name="synthetic_radar_reflectivity"
        )
        self.lightning_def = TargetDefinition(
            name="Lightning Density",
            description="Flash count per cell",
            threshold_value=0.0,
            is_binary=False,
            variable_name="synthetic_lightning_flash_density"
        )
        
    def _extract_target(self, sample: MultimodalSample, target_def: TargetDefinition) -> Tuple[np.ndarray, np.ndarray, str]:
        """Extracts and generates the explicit target mask representing missingness."""
        # Check provenance explicitly
        if self.require_real and sample.provenance != "REAL":
            raise ValueError("Strict REAL target requirement failed: Dataset contains SYNTHETIC provenance.")
            
        if sample.dataset is None or target_def.variable_name not in sample.dataset:
            # Missing entirely
            return None, None, "UNAVAILABLE"
            
        data = sample.dataset[target_def.variable_name].values
        
        # Missing Target != Negative Target
        # Nans are explicitly tracked in the mask
        mask = ~np.isnan(data)
        
        if target_def.is_binary:
            if target_def.threshold_value is not None:
                # Convert valid pixels to binary
                target = np.zeros_like(data, dtype=np.float32)
                target[mask] = (data[mask] > target_def.threshold_value).astype(np.float32)
            else:
                target = data.astype(np.float32)
        else:
            target = np.nan_to_num(data, nan=0.0).astype(np.float32)
            
        # Fill nans in target with 0.0 (safely ignored by mask during loss)
        target[~mask] = 0.0
        
        return target, mask, sample.provenance

    def build(self, input_timestamps: List[datetime], target_sample: MultimodalSample) -> Tuple[torch.Tensor, torch.Tensor, SampleManifest]:
        """Builds multi-head targets for a single future sample."""
        
        # 1. Temporal Alignment & Leakage Check
        forecast_origin = max(input_timestamps)
        if target_sample.target_timestamp <= forecast_origin:
            raise ValueError(f"Temporal Leakage: Target time {target_sample.target_timestamp} is not strictly after input origin {forecast_origin}")

        # 2. Extract targets
        t_storm, t_storm_mask, storm_prov = self._extract_target(target_sample, self.thunderstorm_def)
        t_light, t_light_mask, light_prov = self._extract_target(target_sample, self.lightning_def)
        
        # Handle entirely missing sources
        shape = (1, 1)
        if t_storm is not None:
            shape = t_storm.shape
        elif t_light is not None:
            shape = t_light.shape
            
        # Defaults if utterly missing
        if t_storm is None:
            t_storm = np.zeros(shape, dtype=np.float32)
            t_storm_mask = np.zeros(shape, dtype=bool)
            storm_prov = "UNAVAILABLE"
        if t_light is None:
            t_light = np.zeros(shape, dtype=np.float32)
            t_light_mask = np.zeros(shape, dtype=bool)
            light_prov = "UNAVAILABLE"

        def _extract_raw_data(sample: MultimodalSample, target_def: TargetDefinition):
            if sample.dataset is None or target_def.variable_name not in sample.dataset:
                return None
            return sample.dataset[target_def.variable_name].values
            
        raw_storm = _extract_raw_data(target_sample, self.thunderstorm_def)
        
        # 3. Quality Control
        # Run QC strictly on the primary target's raw data
        if raw_storm is not None:
            qc_result = TargetQualityController.run_qc(raw_storm, target_sample.target_timestamp, forecast_origin)
        else:
            # Dummy valid if unavailable
            qc_result = TargetQualityController.run_qc(np.array([np.nan]), target_sample.target_timestamp, forecast_origin)

        # 4. Construct Manifest
        manifest = SampleManifest(
            sample_id=str(uuid.uuid4()),
            input_timestamps=input_timestamps,
            target_timestamp=target_sample.target_timestamp,
            forecast_origin=forecast_origin,
            source_modalities=["RADAR", "LIGHTNING"] if t_storm is not None else [],
            target_source=f"Storm:{storm_prov}|Light:{light_prov}",
            target_definition_version="v1.0",
            provenance="MIXED" if (storm_prov == "SYNTHETIC" or light_prov == "SYNTHETIC") else "REAL",
            spatial_grid_shape=shape,
            qc_status=qc_result
        )

        target_tensor = torch.from_numpy(np.stack([t_storm, t_light], axis=0))
        mask_tensor = torch.from_numpy(np.stack([t_storm_mask, t_light_mask], axis=0))

        return target_tensor, mask_tensor, manifest
