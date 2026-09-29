import logging
import numpy as np
import xarray as xr
from typing import List, Dict
from dataclasses import dataclass, field

@dataclass
class FeatureExtractionResult:
    dataset: xr.Dataset | None = None
    original_variables: list[str] = field(default_factory=list)
    extracted_features: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

from backend.app.models.multimodal import MultimodalSample
from backend.app.models.features import MLFeatureBatch, FeatureMetadata
from backend.pipeline.common_grid import CommonGridResult

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Transforms sequential MultimodalSamples into an MLFeatureBatch.
    Computes spatial and temporal derived features.
    Maintains strict missingness masks and deterministic channel ordering.
    """
    
    def __init__(self):
        # Step 2 & 3: Authoritative Feature Registry
        self.registry: Dict[str, FeatureMetadata] = {
            # RAW SATELLITE
            "IMG_TIR1": FeatureMetadata(
                name="IMG_TIR1", source_modality="satellite",
                physical_meaning="Thermal Infrared Brightness Temperature (10.8 μm)", units="K",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            "IMG_TIR2": FeatureMetadata(
                name="IMG_TIR2", source_modality="satellite",
                physical_meaning="Thermal Infrared Brightness Temperature (12.0 μm)", units="K",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            "IMG_WV": FeatureMetadata(
                name="IMG_WV", source_modality="satellite",
                physical_meaning="Water Vapor Brightness Temperature (6.7 μm)", units="K",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            "CTP": FeatureMetadata(
                name="CTP", source_modality="satellite",
                physical_meaning="Cloud Top Pressure", units="hPa",
                depends_on_synthetic=False, normalization_method="min-max"
            ),
            "CTT": FeatureMetadata(
                name="CTT", source_modality="satellite",
                physical_meaning="Cloud Top Temperature", units="K",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            
            # DERIVED SATELLITE
            "TIR1_TIR2_DIFF": FeatureMetadata(
                name="TIR1_TIR2_DIFF", source_modality="satellite_derived",
                physical_meaning="Split window difference (TIR1 - TIR2) indicating cloud phase/optical depth", units="K",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            "TIR1_SPATIAL_GRAD": FeatureMetadata(
                name="TIR1_SPATIAL_GRAD", source_modality="satellite_derived",
                physical_meaning="Magnitude of spatial gradient in TIR1", units="K/pixel",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            "TIR1_TEMPORAL_DIFF": FeatureMetadata(
                name="TIR1_TEMPORAL_DIFF", source_modality="satellite_derived",
                physical_meaning="Temporal cooling/warming rate (TIR1[t] - TIR1[t-1])", units="K/30min",
                depends_on_synthetic=False, normalization_method="z-score"
            ),
            
            # SYNTHETIC MODALITIES
            "synthetic_radar_reflectivity": FeatureMetadata(
                name="synthetic_radar_reflectivity", source_modality="radar",
                physical_meaning="Simulated Radar Reflectivity", units="dBZ",
                depends_on_synthetic=True, normalization_method="min-max"
            ),
            "synthetic_nwp_cape": FeatureMetadata(
                name="synthetic_nwp_cape", source_modality="nwp",
                physical_meaning="Simulated Convective Available Potential Energy", units="J/kg",
                depends_on_synthetic=True, normalization_method="z-score"
            ),
            "synthetic_lightning_flash_density": FeatureMetadata(
                name="synthetic_lightning_flash_density", source_modality="lightning",
                physical_meaning="Simulated Lightning Flash Density", units="flashes/km2",
                is_continuous=False, depends_on_synthetic=True, normalization_method="min-max"
            ),
        }
        
        # Deterministic Channel Ordering
        self.feature_names = list(self.registry.keys())

    def run(self, grid_result: 'CommonGridResult') -> FeatureExtractionResult:
        result = FeatureExtractionResult()
        result.dataset = grid_result.dataset
        return result

    def extract(self, samples: List[MultimodalSample]) -> MLFeatureBatch:
        logger.info(f"Extracting features from {len(samples)} sequential multimodal samples")
        
        if not samples:
            raise ValueError("Empty sample list provided to FeatureExtractor")
            
        # Ensure sequential ordering
        samples = sorted(samples, key=lambda s: s.target_timestamp)
        timestamps = [s.target_timestamp.isoformat() for s in samples]

        # Dimensions
        N = len(samples)
        C = len(self.feature_names)

        
        # Get spatial dimensions from the first valid dataset
        first_valid = next((s.dataset for s in samples if s.dataset is not None), None)
        if first_valid is None:
            raise ValueError("All multimodal samples have None datasets.")
            
        H = first_valid.sizes["latitude"]
        W = first_valid.sizes["longitude"]
        
        # Initialize Tensors (NaN filled)
        tensor = np.full((N, C, H, W), np.nan, dtype=np.float32)
        
        has_real = False
        has_synthetic = False
        
        for t, sample in enumerate(samples):
            if sample.dataset is None:
                continue
                
            if sample.provenance in ["REAL", "MIXED"]:
                has_real = True
            if sample.provenance in ["SYNTHETIC", "MIXED"]:
                has_synthetic = True
                
            ds = sample.dataset
            
            # Step 1: Raw features
            for c, f_name in enumerate(self.feature_names):
                if f_name in ds.data_vars:
                    tensor[t, c] = ds[f_name].values
                    
            # Step 2: Spatial Derived Features
            tir1_idx = self.feature_names.index("IMG_TIR1")
            tir2_idx = self.feature_names.index("IMG_TIR2")
            
            # TIR1 - TIR2
            diff_idx = self.feature_names.index("TIR1_TIR2_DIFF")
            tensor[t, diff_idx] = tensor[t, tir1_idx] - tensor[t, tir2_idx]
            
            # TIR1 Spatial Gradient
            grad_idx = self.feature_names.index("TIR1_SPATIAL_GRAD")
            tir1_data = tensor[t, tir1_idx]
            if not np.all(np.isnan(tir1_data)):
                grads = np.gradient(tir1_data)
                grad_mag = np.sqrt(grads[0]**2 + grads[1]**2)
                # Keep NaNs where original was NaN
                grad_mag[np.isnan(tir1_data)] = np.nan
                tensor[t, grad_idx] = grad_mag
                
            # Step 3: Temporal Features
            tdiff_idx = self.feature_names.index("TIR1_TEMPORAL_DIFF")
            if t > 0:
                prev_tir1 = tensor[t-1, tir1_idx]
                curr_tir1 = tensor[t, tir1_idx]
                tensor[t, tdiff_idx] = curr_tir1 - prev_tir1
                # If either t or t-1 is NaN, the result is correctly NaN.
            else:
                # First timestamp has no previous frame available
                tensor[t, tdiff_idx] = np.nan
                
        # Step 4: Missingness Mask
        validity_mask = ~np.isnan(tensor)
        
        # Step 5: Final Provenance
        if has_real and has_synthetic:
            final_prov = "MIXED"
        elif has_real:
            final_prov = "REAL"
        else:
            final_prov = "SYNTHETIC"
            
        return MLFeatureBatch(
            timestamps=timestamps,
            feature_names=self.feature_names,
            feature_registry=self.registry,
            tensor=tensor,
            validity_mask=validity_mask,
            provenance=final_prov
        )
