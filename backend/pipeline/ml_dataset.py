import logging
from typing import List, Callable, Optional, Dict, Tuple
from datetime import datetime
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

from backend.app.models.multimodal import MultimodalSample
from backend.app.models.features import MLFeatureBatch
from backend.app.models.dataset import (
    SlidingWindowConfig, 
    DatasetSplitConfig,
    MLDatasetSample,
    MLDataLoaderBatch
)
from backend.pipeline.feature_extraction import FeatureExtractor

logger = logging.getLogger(__name__)

class TargetBuilder:
    """
    Generates target tensors and masks for the model heads.
    Head 0: Thunderstorm Occurrence
    Head 1: Lightning Occurrence/Density
    """
    @staticmethod
    def build_targets(target_samples: List[MultimodalSample], expected_horizon: int, shape: Tuple[int, int]) -> Tuple[torch.Tensor, torch.Tensor]:
        H, W = shape
        heads = 2
        # Tensors initialized to zero, but rely on masks
        target = torch.zeros((expected_horizon, heads, H, W), dtype=torch.float32)
        target_mask = torch.zeros((expected_horizon, heads, H, W), dtype=torch.bool)
        
        for h_idx, sample in enumerate(target_samples):
            if h_idx >= expected_horizon:
                break
                
            if sample.dataset is None:
                continue
                
            ds = sample.dataset
            
            # Head 0: Thunderstorm Occurrence
            # Currently we have no real ground truth for thunderstorm occurrence in the DB.
            # E.g. we might use reflectivity > 35 dBZ as a proxy if we had real radar.
            if "synthetic_radar_reflectivity" in ds:
                # Demonstration mapping: reflectivity > 35 is a storm
                refl = ds["synthetic_radar_reflectivity"].values
                storm_mask = (refl > 35.0).astype(np.float32)
                target[h_idx, 0] = torch.from_numpy(storm_mask)
                target_mask[h_idx, 0] = ~torch.isnan(torch.from_numpy(refl))
            
            # Head 1: Lightning Occurrence/Density
            if "synthetic_lightning_flash_density" in ds:
                light = ds["synthetic_lightning_flash_density"].values
                target[h_idx, 1] = torch.from_numpy(light)
                target_mask[h_idx, 1] = ~torch.isnan(torch.from_numpy(light))
                
        # IMPORTANT SCIENTIFIC RULE:
        # If no target data is available, target_mask remains 0.
        # This prevents the network from learning that missing data = no storms.
        return target, target_mask

class StormFusionDataset(Dataset):
    """
    PyTorch Dataset for StormFusion temporal windowing.
    Implements lazy extraction and strictly rejects unexpected temporal gaps.
    """
    def __init__(
        self,
        metadata_records: List[Dict],
        load_sample_fn: Callable[[datetime], MultimodalSample],
        config: SlidingWindowConfig,
        feature_extractor: FeatureExtractor,
        partition: str = "ALL",
        split_config: Optional[DatasetSplitConfig] = None
    ):
        """
        metadata_records: List of dicts with at least 'timestamp' and 'provenance'.
        load_sample_fn: Function to lazily fetch a MultimodalSample for a given timestamp.
        config: Windowing rules.
        """
        # Ensure chronological ordering
        self.records = sorted(metadata_records, key=lambda x: x["timestamp"])
        self.load_sample_fn = load_sample_fn
        self.config = config
        self.feature_extractor = feature_extractor
        
        # Split chronological partitions
        self.records = self._apply_partition(self.records, partition, split_config)
        
        # Build valid indices considering sequence + horizon, gaps, and stride
        self.valid_window_indices = self._build_valid_windows()
        
    def _apply_partition(self, records: List[Dict], partition: str, split_config: Optional[DatasetSplitConfig]) -> List[Dict]:
        if partition == "ALL" or split_config is None:
            return records
            
        filtered = []
        for r in records:
            ts = r["timestamp"]
            if partition == "TRAIN" and ts <= split_config.train_end_time:
                filtered.append(r)
            elif partition == "VALIDATION" and split_config.train_end_time < ts <= split_config.val_end_time:
                filtered.append(r)
            elif partition == "TEST" and ts > split_config.val_end_time:
                filtered.append(r)
        return filtered

    def _build_valid_windows(self) -> List[int]:
        valid_starts = []
        req_len = self.config.sequence_length + self.config.forecast_horizon
        
        for i in range(0, len(self.records) - req_len + 1, self.config.stride):
            window = self.records[i:i + req_len]
            is_valid = True
            
            # Check for illegal temporal gaps
            for j in range(1, len(window)):
                delta = window[j]["timestamp"] - window[j-1]["timestamp"]
                # Must exactly match expected step up to maximum gap allowed
                # (By default max gap = expected step, meaning NO missing frames allowed)
                if abs(delta - self.config.expected_time_delta) > (self.config.maximum_allowed_gap - self.config.expected_time_delta):
                    is_valid = False
                    break
                    
            if is_valid:
                valid_starts.append(i)
                
        return valid_starts
        
    def __len__(self) -> int:
        return len(self.valid_window_indices)

    def _determine_window_provenance(self, window_records: List[Dict]) -> str:
        has_real = any(r.get("provenance", "SYNTHETIC") in ["REAL", "MIXED"] for r in window_records)
        has_synthetic = any(r.get("provenance", "SYNTHETIC") in ["SYNTHETIC", "MIXED"] for r in window_records)
        
        if has_real and has_synthetic:
            return "MIXED"
        elif has_real:
            return "REAL"
        return "SYNTHETIC"

    def __getitem__(self, idx: int) -> MLDatasetSample:
        start_idx = self.valid_window_indices[idx]
        seq_len = self.config.sequence_length
        horizon = self.config.forecast_horizon
        
        input_records = self.records[start_idx : start_idx + seq_len]
        target_records = self.records[start_idx + seq_len : start_idx + seq_len + horizon]
        
        # Lazy load samples
        input_samples = [self.load_sample_fn(r["timestamp"]) for r in input_records]
        target_samples = [self.load_sample_fn(r["timestamp"]) for r in target_records]
        
        # Extract features (uses Part 15 FeatureExtractor)
        batch: MLFeatureBatch = self.feature_extractor.extract(input_samples)
        
        features_tensor = torch.from_numpy(batch.tensor).float()
        validity_mask = torch.from_numpy(batch.validity_mask).bool()
        
        # Build targets
        H, W = features_tensor.shape[2], features_tensor.shape[3]
        target, target_mask = TargetBuilder.build_targets(target_samples, horizon, (H, W))
        
        # Calculate provenance
        prov = self._determine_window_provenance(input_records + target_records)
        
        return MLDatasetSample(
            features=features_tensor,
            validity_mask=validity_mask,
            target=target,
            target_mask=target_mask,
            input_timestamps=[r["timestamp"] for r in input_records],
            target_timestamps=[r["timestamp"] for r in target_records],
            provenance=prov
        )

def stormfusion_collate_fn(batch: List[MLDatasetSample]) -> MLDataLoaderBatch:
    """
    Custom collate function for DataLoader.
    Stacks tensors and lists timestamps/provenances.
    """
    features = torch.stack([s.features for s in batch], dim=0)
    validity_mask = torch.stack([s.validity_mask for s in batch], dim=0)
    target = torch.stack([s.target for s in batch], dim=0)
    target_mask = torch.stack([s.target_mask for s in batch], dim=0)
    
    input_ts = [s.input_timestamps for s in batch]
    target_ts = [s.target_timestamps for s in batch]
    provs = [s.provenance for s in batch]
    
    return MLDataLoaderBatch(
        features=features,
        validity_mask=validity_mask,
        target=target,
        target_mask=target_mask,
        input_timestamps=input_ts,
        target_timestamps=target_ts,
        provenance=provs
    )

def create_dataloader(dataset: StormFusionDataset, batch_size: int, shuffle: bool = False, num_workers: int = 0) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=stormfusion_collate_fn,
        pin_memory=False
    )
