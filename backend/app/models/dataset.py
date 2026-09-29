from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
import torch

@dataclass
class SlidingWindowConfig:
    sequence_length: int = 6
    forecast_horizon: int = 1
    stride: int = 1
    expected_time_delta: timedelta = timedelta(minutes=30)
    maximum_allowed_gap: timedelta = timedelta(minutes=30) # No gaps allowed by default beyond the expected step

@dataclass
class DatasetSplitConfig:
    train_end_time: datetime
    val_end_time: datetime

@dataclass
class MLDatasetSample:
    """
    A single valid sequence extracted via sliding window.
    """
    features: torch.Tensor          # [T, C, H, W]
    validity_mask: torch.Tensor     # [T, C, H, W]
    target: torch.Tensor            # [Horizon, Heads, H, W]
    target_mask: torch.Tensor       # [Horizon, Heads, H, W]
    input_timestamps: List[datetime]
    target_timestamps: List[datetime]
    provenance: str                 # REAL, SYNTHETIC, or MIXED

@dataclass
class MLDataLoaderBatch:
    """
    Collated batch of dataset samples.
    """
    features: torch.Tensor          # [B, T, C, H, W]
    validity_mask: torch.Tensor     # [B, T, C, H, W]
    target: torch.Tensor            # [B, Horizon, Heads, H, W]
    target_mask: torch.Tensor       # [B, Horizon, Heads, H, W]
    input_timestamps: List[List[datetime]]
    target_timestamps: List[List[datetime]]
    provenance: List[str]
